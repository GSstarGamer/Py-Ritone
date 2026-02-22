package com.pyritone.bridge.runtime;

public enum TaskState {
    PENDING(false),
    RUNNING(false),
    COMPLETED(true),
    FAILED(true),
    CANCELED(true),
    REPLACED(true);

    private final boolean terminal;

    TaskState(boolean terminal) {
        this.terminal = terminal;
    }

    public boolean isTerminal() {
        return terminal;
    }
}
