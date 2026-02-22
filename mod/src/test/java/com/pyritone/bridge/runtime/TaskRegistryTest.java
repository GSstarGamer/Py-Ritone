package com.pyritone.bridge.runtime;

import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

class TaskRegistryTest {
    @Test
    void startReplacesPreviousActiveTask() {
        TaskRegistry registry = new TaskRegistry();

        TaskRegistry.StartResult first = registry.start("goto 0 64 0");
        TaskRegistry.StartResult second = registry.start("goto 10 64 10");

        assertNotNull(first.startedTask());
        assertNotNull(second.startedTask());
        assertNotNull(second.replacedTask());
        assertEquals(TaskState.REPLACED, second.replacedTask().state());
        assertTrue(registry.active().isPresent());
        assertEquals(second.startedTask().taskId(), registry.active().orElseThrow().taskId());
    }

    @Test
    void terminalTransitionClearsActiveTask() {
        TaskRegistry registry = new TaskRegistry();
        registry.start("goto 1 64 1");

        TaskSnapshot completed = registry.transitionActive(TaskState.COMPLETED, "Reached goal").orElseThrow();

        assertEquals(TaskState.COMPLETED, completed.state());
        assertTrue(registry.active().isEmpty());
    }
}
