package com.pyritone.bridge.runtime;

import java.util.Optional;

public final class TaskLifecycleResolver {
    public static final int DEFAULT_QUIESCENCE_TICKS = 30;

    private final int quiescenceTicks;
    private LifecycleContext context;

    public TaskLifecycleResolver() {
        this(DEFAULT_QUIESCENCE_TICKS);
    }

    public TaskLifecycleResolver(int quiescenceTicks) {
        if (quiescenceTicks < 1) {
            throw new IllegalArgumentException("quiescenceTicks must be >= 1");
        }
        this.quiescenceTicks = quiescenceTicks;
    }

    public synchronized void start(String taskId) {
        if (taskId == null || taskId.isBlank()) {
            this.context = null;
            return;
        }
        this.context = new LifecycleContext(taskId);
    }

    public synchronized void clear() {
        this.context = null;
    }

    public synchronized void clearForTask(String taskId) {
        if (context != null && context.taskId.equals(taskId)) {
            context = null;
        }
    }

    public synchronized void markApiCancelRequested(String taskId) {
        LifecycleContext active = ensureContext(taskId);
        active.cancelRequestedByApi = true;
        active.lastHint = PathHint.CANCELED;
        active.lastHintEvent = "CANCELED";
        active.resumedAfterHint = false;
        active.idleTicks = 0;
    }

    public synchronized void recordPathEvent(String taskId, String pathEventName) {
        LifecycleContext active = ensureContext(taskId);
        PathHint hint = PathHint.fromPathEvent(pathEventName);
        if (hint == PathHint.NONE) {
            return;
        }
        // Once we observe a cancel hint, keep it sticky for this task.
        // Baritone may emit follow-up path events while winding down, but the task should still end as canceled.
        if (active.lastHint == PathHint.CANCELED && hint != PathHint.CANCELED) {
            return;
        }
        if (hint == active.lastHint && pathEventName != null && pathEventName.equals(active.lastHintEvent)) {
            return;
        }
        active.lastHint = hint;
        active.lastHintEvent = pathEventName;
        active.resumedAfterHint = false;
        active.idleTicks = 0;
    }

    public synchronized Optional<LifecycleUpdate> evaluate(String taskId, BaritoneGateway.ActivitySnapshot runtimeState) {
        if (taskId == null || taskId.isBlank()) {
            context = null;
            return Optional.empty();
        }

        LifecycleContext active = ensureContext(taskId);
        BaritoneGateway.ActivitySnapshot snapshot = runtimeState == null
            ? BaritoneGateway.ActivitySnapshot.idle()
            : runtimeState;

        boolean cancelIntent = active.cancelRequestedByApi || active.lastHint == PathHint.CANCELED;
        boolean cancelBusyWork = hasCancelableBusyWork(snapshot);
        boolean ignorePauseLatch = cancelIntent && !cancelBusyWork;

        PauseStatus pauseStatus = PauseStatus.fromSnapshot(snapshot);
        if (pauseStatus != null && !ignorePauseLatch) {
            active.idleTicks = 0;
            if (!active.paused || !pauseStatus.equals(active.pauseStatus)) {
                active.paused = true;
                active.pauseStatus = pauseStatus;
                return Optional.of(LifecycleUpdate.paused(pauseStatus));
            }
            return Optional.empty();
        }

        if (active.paused) {
            PauseStatus previousPauseStatus = active.pauseStatus;
            active.paused = false;
            active.pauseStatus = null;
            active.idleTicks = 0;
            return Optional.of(LifecycleUpdate.resumed(previousPauseStatus));
        }

        boolean treatAsBusy = cancelIntent ? cancelBusyWork : snapshot.isBusy();
        if (treatAsBusy) {
            if (active.lastHint != PathHint.NONE && active.lastHint != PathHint.CANCELED) {
                active.resumedAfterHint = true;
            }
            active.idleTicks = 0;
            return Optional.empty();
        }

        active.idleTicks += 1;
        if (active.idleTicks < quiescenceTicks) {
            return Optional.empty();
        }

        TerminalDecision terminalDecision = decide(active);
        context = null;
        return Optional.of(LifecycleUpdate.terminal(terminalDecision));
    }

    private static boolean hasCancelableBusyWork(BaritoneGateway.ActivitySnapshot snapshot) {
        if (snapshot == null) {
            return false;
        }
        return snapshot.isPathing() || snapshot.calcInProgress() || snapshot.builderActive();
    }

    private LifecycleContext ensureContext(String taskId) {
        if (context == null || !context.taskId.equals(taskId)) {
            context = new LifecycleContext(taskId);
        }
        return context;
    }

    private static TerminalDecision decide(LifecycleContext active) {
        if (active.cancelRequestedByApi) {
            return new TerminalDecision(TaskState.CANCELED, "Canceled by API request", "cancel_requested_quiesced");
        }

        if (active.lastHint == PathHint.CANCELED) {
            return new TerminalDecision(TaskState.CANCELED, "Baritone canceled", "canceled_quiesced");
        }

        if (!active.resumedAfterHint) {
            if (active.lastHint == PathHint.CALC_FAILED) {
                String detail = active.lastHintEvent == null || active.lastHintEvent.isBlank()
                    ? "Path calculation failed"
                    : active.lastHintEvent;
                return new TerminalDecision(TaskState.FAILED, detail, "calc_failed_quiesced");
            }
            if (active.lastHint == PathHint.AT_GOAL) {
                return new TerminalDecision(TaskState.COMPLETED, "Reached goal", "at_goal_quiesced");
            }
        }

        return new TerminalDecision(TaskState.COMPLETED, "Task became idle", "idle_quiesced");
    }

    private enum PathHint {
        NONE,
        AT_GOAL,
        CANCELED,
        CALC_FAILED;

        static PathHint fromPathEvent(String eventName) {
            if (eventName == null || eventName.isBlank()) {
                return NONE;
            }
            return switch (eventName) {
                case "AT_GOAL" -> AT_GOAL;
                case "CANCELED" -> CANCELED;
                case "CALC_FAILED", "NEXT_CALC_FAILED" -> CALC_FAILED;
                default -> NONE;
            };
        }
    }

    private static final class LifecycleContext {
        private final String taskId;
        private boolean cancelRequestedByApi;
        private PathHint lastHint = PathHint.NONE;
        private String lastHintEvent;
        private boolean resumedAfterHint;
        private boolean paused;
        private PauseStatus pauseStatus;
        private int idleTicks;

        private LifecycleContext(String taskId) {
            this.taskId = taskId;
        }
    }

    public record TerminalDecision(TaskState state, String detail, String stage) {
        public String eventName() {
            return switch (state) {
                case COMPLETED -> "task.completed";
                case FAILED -> "task.failed";
                case CANCELED -> "task.canceled";
                default -> "task.progress";
            };
        }
    }

    public record PauseStatus(
        String reasonCode,
        String sourceProcess,
        String commandType
    ) {
        private static PauseStatus fromSnapshot(BaritoneGateway.ActivitySnapshot snapshot) {
            if (snapshot == null || !snapshot.isPaused()) {
                return null;
            }

            return new PauseStatus(
                snapshot.pauseReasonCode(),
                snapshot.sourceProcess(),
                snapshot.commandType()
            );
        }
    }

    public record LifecycleUpdate(Kind kind, PauseStatus pauseStatus, TerminalDecision terminalDecision) {
        public static LifecycleUpdate paused(PauseStatus pauseStatus) {
            return new LifecycleUpdate(Kind.PAUSED, pauseStatus, null);
        }

        public static LifecycleUpdate resumed(PauseStatus pauseStatus) {
            return new LifecycleUpdate(Kind.RESUMED, pauseStatus, null);
        }

        public static LifecycleUpdate terminal(TerminalDecision terminalDecision) {
            return new LifecycleUpdate(Kind.TERMINAL, null, terminalDecision);
        }

        public enum Kind {
            PAUSED,
            RESUMED,
            TERMINAL
        }
    }
}
