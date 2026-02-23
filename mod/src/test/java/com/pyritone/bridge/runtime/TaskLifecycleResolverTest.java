package com.pyritone.bridge.runtime;

import org.junit.jupiter.api.Test;

import java.util.Optional;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

class TaskLifecycleResolverTest {
    @Test
    void apiCancelResolvesToCanceledAfterQuiescence() {
        TaskLifecycleResolver resolver = new TaskLifecycleResolver(3);
        String taskId = "task-1";

        resolver.start(taskId);
        resolver.markApiCancelRequested(taskId);

        assertTrue(resolver.evaluate(taskId, idle()).isEmpty());
        assertTrue(resolver.evaluate(taskId, idle()).isEmpty());

        TaskLifecycleResolver.LifecycleUpdate update = resolver.evaluate(taskId, idle()).orElseThrow();
        assertEquals(TaskLifecycleResolver.LifecycleUpdate.Kind.TERMINAL, update.kind());
        assertEquals(TaskState.CANCELED, update.terminalDecision().state());
    }

    @Test
    void calcFailHintResolvesToFailedWhenIdleStabilizes() {
        TaskLifecycleResolver resolver = new TaskLifecycleResolver(3);
        String taskId = "task-2";

        resolver.start(taskId);
        resolver.recordPathEvent(taskId, "NEXT_CALC_FAILED");

        assertTrue(resolver.evaluate(taskId, idle()).isEmpty());
        assertTrue(resolver.evaluate(taskId, idle()).isEmpty());

        TaskLifecycleResolver.LifecycleUpdate update = resolver.evaluate(taskId, idle()).orElseThrow();
        assertEquals(TaskLifecycleResolver.LifecycleUpdate.Kind.TERMINAL, update.kind());
        assertEquals(TaskState.FAILED, update.terminalDecision().state());
    }

    @Test
    void idleAfterBusyWithoutHintsDefaultsToCompleted() {
        TaskLifecycleResolver resolver = new TaskLifecycleResolver(3);
        String taskId = "task-3";

        resolver.start(taskId);
        assertTrue(resolver.evaluate(taskId, busy()).isEmpty());
        assertTrue(resolver.evaluate(taskId, idle()).isEmpty());
        assertTrue(resolver.evaluate(taskId, idle()).isEmpty());

        TaskLifecycleResolver.LifecycleUpdate update = resolver.evaluate(taskId, idle()).orElseThrow();
        assertEquals(TaskLifecycleResolver.LifecycleUpdate.Kind.TERMINAL, update.kind());
        assertEquals(TaskState.COMPLETED, update.terminalDecision().state());
    }

    @Test
    void pausedStateDoesNotTerminalAndEmitsPauseThenResume() {
        TaskLifecycleResolver resolver = new TaskLifecycleResolver(3);
        String taskId = "task-4";

        resolver.start(taskId);

        TaskLifecycleResolver.LifecycleUpdate paused = resolver.evaluate(taskId, paused()).orElseThrow();
        assertEquals(TaskLifecycleResolver.LifecycleUpdate.Kind.PAUSED, paused.kind());
        assertEquals("BUILDER_PAUSED", paused.pauseStatus().reasonCode());

        assertTrue(resolver.evaluate(taskId, paused()).isEmpty());

        TaskLifecycleResolver.LifecycleUpdate resumed = resolver.evaluate(taskId, busy()).orElseThrow();
        assertEquals(TaskLifecycleResolver.LifecycleUpdate.Kind.RESUMED, resumed.kind());
        assertEquals("BUILDER_PAUSED", resumed.pauseStatus().reasonCode());
    }

    @Test
    void cancelHintIgnoresStaleProcessInControlAndStillTerminals() {
        TaskLifecycleResolver resolver = new TaskLifecycleResolver(3);
        String taskId = "task-5";

        resolver.start(taskId);
        resolver.recordPathEvent(taskId, "CANCELED");

        assertTrue(resolver.evaluate(taskId, pausedWithStaleControl()).isEmpty());
        assertTrue(resolver.evaluate(taskId, pausedWithStaleControl()).isEmpty());

        TaskLifecycleResolver.LifecycleUpdate terminal = resolver.evaluate(taskId, pausedWithStaleControl()).orElseThrow();
        assertEquals(TaskLifecycleResolver.LifecycleUpdate.Kind.TERMINAL, terminal.kind());
        assertEquals(TaskState.CANCELED, terminal.terminalDecision().state());
    }

    @Test
    void duplicateCancelHintsDoNotResetQuiescenceCountdown() {
        TaskLifecycleResolver resolver = new TaskLifecycleResolver(3);
        String taskId = "task-6";

        resolver.start(taskId);
        resolver.recordPathEvent(taskId, "CANCELED");

        assertTrue(resolver.evaluate(taskId, idle()).isEmpty());

        resolver.recordPathEvent(taskId, "CANCELED");
        assertTrue(resolver.evaluate(taskId, idle()).isEmpty());

        resolver.recordPathEvent(taskId, "CANCELED");
        TaskLifecycleResolver.LifecycleUpdate terminal = resolver.evaluate(taskId, idle()).orElseThrow();
        assertEquals(TaskLifecycleResolver.LifecycleUpdate.Kind.TERMINAL, terminal.kind());
        assertEquals(TaskState.CANCELED, terminal.terminalDecision().state());
    }

    @Test
    void cancelHintRemainsTerminalEvenIfFollowupCalcFailEventsArrive() {
        TaskLifecycleResolver resolver = new TaskLifecycleResolver(3);
        String taskId = "task-7";

        resolver.start(taskId);
        resolver.recordPathEvent(taskId, "CANCELED");
        resolver.recordPathEvent(taskId, "NEXT_CALC_FAILED");
        resolver.recordPathEvent(taskId, "CALC_FAILED");

        assertTrue(resolver.evaluate(taskId, idle()).isEmpty());
        assertTrue(resolver.evaluate(taskId, idle()).isEmpty());

        TaskLifecycleResolver.LifecycleUpdate terminal = resolver.evaluate(taskId, idle()).orElseThrow();
        assertEquals(TaskLifecycleResolver.LifecycleUpdate.Kind.TERMINAL, terminal.kind());
        assertEquals(TaskState.CANCELED, terminal.terminalDecision().state());
    }

    @Test
    void staleProcessControlWithoutWorkStillResolvesTerminal() {
        TaskLifecycleResolver resolver = new TaskLifecycleResolver(3);
        String taskId = "task-8";

        resolver.start(taskId);

        assertTrue(resolver.evaluate(taskId, staleControlNoWork()).isEmpty());
        assertTrue(resolver.evaluate(taskId, staleControlNoWork()).isEmpty());

        TaskLifecycleResolver.LifecycleUpdate terminal = resolver.evaluate(taskId, staleControlNoWork()).orElseThrow();
        assertEquals(TaskLifecycleResolver.LifecycleUpdate.Kind.TERMINAL, terminal.kind());
        assertEquals(TaskState.COMPLETED, terminal.terminalDecision().state());
    }

    private static BaritoneGateway.ActivitySnapshot idle() {
        return BaritoneGateway.ActivitySnapshot.idle();
    }

    private static BaritoneGateway.ActivitySnapshot busy() {
        return new BaritoneGateway.ActivitySnapshot(
            true,
            true,
            false,
            true,
            "SET_GOAL_AND_PATH",
            "Pathing",
            false,
            false
        );
    }

    private static BaritoneGateway.ActivitySnapshot paused() {
        return new BaritoneGateway.ActivitySnapshot(
            false,
            false,
            false,
            false,
            "REQUEST_PAUSE",
            "Builder",
            true,
            true
        );
    }

    private static BaritoneGateway.ActivitySnapshot pausedWithStaleControl() {
        return new BaritoneGateway.ActivitySnapshot(
            false,
            false,
            false,
            true,
            "REQUEST_PAUSE",
            "Builder",
            false,
            true
        );
    }

    private static BaritoneGateway.ActivitySnapshot staleControlNoWork() {
        return new BaritoneGateway.ActivitySnapshot(
            false,
            false,
            false,
            true,
            "SET_GOAL_AND_PATH",
            "Builder",
            false,
            false
        );
    }
}
