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
        active.lastHint = hint;
        active.lastHintEvent = pathEventName;
        active.resumedAfterHint = false;
        active.idleTicks = 0;
    }

    public synchronized Optional<TerminalDecision> evaluate(String taskId, BaritoneGateway.ActivitySnapshot runtimeState) {
        if (taskId == null || taskId.isBlank()) {
            context = null;
            return Optional.empty();
        }

        LifecycleContext active = ensureContext(taskId);
        BaritoneGateway.ActivitySnapshot snapshot = runtimeState == null
            ? BaritoneGateway.ActivitySnapshot.idle()
            : runtimeState;

        if (snapshot.isBusy()) {
            if (active.lastHint != PathHint.NONE) {
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
        return Optional.of(terminalDecision);
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

        if (!active.resumedAfterHint) {
            if (active.lastHint == PathHint.CANCELED) {
                return new TerminalDecision(TaskState.CANCELED, "Baritone canceled", "canceled_quiesced");
            }
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
}
