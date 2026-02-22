package com.pyritone.bridge.runtime;

import org.junit.jupiter.api.Test;

import java.util.Optional;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

class TaskLifecycleResolverTest {
    @Test
    void canceledHintThatResumesDoesNotTerminalEarly() {
        TaskLifecycleResolver resolver = new TaskLifecycleResolver(3);
        String taskId = "task-1";

        resolver.start(taskId);
        resolver.recordPathEvent(taskId, "CANCELED");

        assertTrue(resolver.evaluate(taskId, idle()).isEmpty());
        assertTrue(resolver.evaluate(taskId, busy()).isEmpty());
        assertTrue(resolver.evaluate(taskId, idle()).isEmpty());
        assertTrue(resolver.evaluate(taskId, idle()).isEmpty());

        TaskLifecycleResolver.TerminalDecision terminal = resolver.evaluate(taskId, idle()).orElseThrow();
        assertEquals(TaskState.COMPLETED, terminal.state());
    }

    @Test
    void apiCancelResolvesToCanceledAfterQuiescence() {
        TaskLifecycleResolver resolver = new TaskLifecycleResolver(3);
        String taskId = "task-2";

        resolver.start(taskId);
        resolver.markApiCancelRequested(taskId);

        assertTrue(resolver.evaluate(taskId, idle()).isEmpty());
        assertTrue(resolver.evaluate(taskId, idle()).isEmpty());
        TaskLifecycleResolver.TerminalDecision terminal = resolver.evaluate(taskId, idle()).orElseThrow();

        assertEquals(TaskState.CANCELED, terminal.state());
        assertEquals("task.canceled", terminal.eventName());
    }

    @Test
    void calcFailHintResolvesToFailedWhenIdleStabilizes() {
        TaskLifecycleResolver resolver = new TaskLifecycleResolver(3);
        String taskId = "task-3";

        resolver.start(taskId);
        resolver.recordPathEvent(taskId, "NEXT_CALC_FAILED");

        assertTrue(resolver.evaluate(taskId, idle()).isEmpty());
        assertTrue(resolver.evaluate(taskId, idle()).isEmpty());
        TaskLifecycleResolver.TerminalDecision terminal = resolver.evaluate(taskId, idle()).orElseThrow();

        assertEquals(TaskState.FAILED, terminal.state());
        assertEquals("task.failed", terminal.eventName());
    }

    @Test
    void idleAfterBusyWithoutHintsDefaultsToCompleted() {
        TaskLifecycleResolver resolver = new TaskLifecycleResolver(3);
        String taskId = "task-4";

        resolver.start(taskId);
        assertTrue(resolver.evaluate(taskId, busy()).isEmpty());
        assertTrue(resolver.evaluate(taskId, idle()).isEmpty());
        assertTrue(resolver.evaluate(taskId, idle()).isEmpty());

        TaskLifecycleResolver.TerminalDecision terminal = resolver.evaluate(taskId, idle()).orElseThrow();
        assertEquals(TaskState.COMPLETED, terminal.state());
    }

    @Test
    void quiescenceWindowBlocksImmediateTerminalOnPathHints() {
        TaskLifecycleResolver resolver = new TaskLifecycleResolver(3);
        String taskId = "task-5";

        resolver.start(taskId);
        resolver.recordPathEvent(taskId, "AT_GOAL");

        Optional<TaskLifecycleResolver.TerminalDecision> firstTick = resolver.evaluate(taskId, idle());
        Optional<TaskLifecycleResolver.TerminalDecision> secondTick = resolver.evaluate(taskId, idle());

        assertTrue(firstTick.isEmpty());
        assertTrue(secondTick.isEmpty());
    }

    private static BaritoneGateway.ActivitySnapshot idle() {
        return BaritoneGateway.ActivitySnapshot.idle();
    }

    private static BaritoneGateway.ActivitySnapshot busy() {
        return new BaritoneGateway.ActivitySnapshot(true, true, false, false);
    }
}
