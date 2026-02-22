package com.pyritone.bridge.runtime;

import com.google.gson.JsonElement;
import com.google.gson.JsonNull;

import java.time.Instant;
import java.util.Optional;
import java.util.UUID;

public final class TaskRegistry {
    private TaskRecord active;

    public synchronized StartResult start(String command) {
        TaskSnapshot replacedTask = null;
        if (active != null && !active.state.isTerminal()) {
            active.state = TaskState.REPLACED;
            active.detail = "Replaced by a new task";
            active.updatedAt = Instant.now();
            replacedTask = active.snapshot();
        }

        TaskRecord next = TaskRecord.running(command);
        active = next;
        return new StartResult(next.snapshot(), replacedTask);
    }

    public synchronized Optional<TaskSnapshot> updateActiveDetail(String detail) {
        if (active == null || active.state.isTerminal()) {
            return Optional.empty();
        }
        active.detail = detail;
        active.updatedAt = Instant.now();
        return Optional.of(active.snapshot());
    }

    public synchronized Optional<TaskSnapshot> transitionActive(TaskState targetState, String detail) {
        if (active == null) {
            return Optional.empty();
        }

        active.state = targetState;
        active.detail = detail;
        active.updatedAt = Instant.now();
        TaskSnapshot snapshot = active.snapshot();

        if (targetState.isTerminal()) {
            active = null;
        }

        return Optional.of(snapshot);
    }

    public synchronized Optional<TaskSnapshot> active() {
        if (active == null) {
            return Optional.empty();
        }
        return Optional.of(active.snapshot());
    }

    public synchronized JsonElement activeAsJson() {
        return active().<JsonElement>map(TaskSnapshot::toJson).orElse(JsonNull.INSTANCE);
    }

    public record StartResult(TaskSnapshot startedTask, TaskSnapshot replacedTask) {
    }

    private static final class TaskRecord {
        private final String taskId;
        private final String command;
        private final Instant startedAt;
        private Instant updatedAt;
        private TaskState state;
        private String detail;

        private TaskRecord(String taskId, String command, TaskState state, String detail) {
            this.taskId = taskId;
            this.command = command;
            this.startedAt = Instant.now();
            this.updatedAt = this.startedAt;
            this.state = state;
            this.detail = detail;
        }

        private static TaskRecord running(String command) {
            return new TaskRecord(UUID.randomUUID().toString(), command, TaskState.RUNNING, "Command dispatched");
        }

        private TaskSnapshot snapshot() {
            return new TaskSnapshot(
                taskId,
                command,
                state,
                startedAt.toString(),
                updatedAt.toString(),
                detail
            );
        }
    }
}
