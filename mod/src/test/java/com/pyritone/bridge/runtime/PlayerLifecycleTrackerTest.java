package com.pyritone.bridge.runtime;

import org.junit.jupiter.api.Test;

import java.util.List;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

class PlayerLifecycleTrackerTest {
    @Test
    void firstSnapshotSeedsStateWithoutReplay() {
        PlayerLifecycleTracker tracker = new PlayerLifecycleTracker();

        List<PlayerLifecycleTracker.PlayerEvent> events = tracker.update(
            List.of(player("u1", "Self", true, true), player("u2", "Other", true, false))
        );

        assertTrue(events.isEmpty());
    }

    @Test
    void emitsJoinAndLeaveFromDiff() {
        PlayerLifecycleTracker tracker = new PlayerLifecycleTracker(1);
        tracker.update(List.of(player("u1", "Self", true, true)));

        List<PlayerLifecycleTracker.PlayerEvent> joinEvents = tracker.update(
            List.of(player("u1", "Self", true, true), player("u2", "Other", true, false))
        );
        assertEquals(1, joinEvents.size());
        assertEquals(PlayerLifecycleTracker.PlayerEventType.JOIN, joinEvents.getFirst().type());
        assertEquals("u2", joinEvents.getFirst().player().uuid());

        List<PlayerLifecycleTracker.PlayerEvent> leaveEvents = tracker.update(
            List.of(player("u1", "Self", true, true))
        );
        assertEquals(1, leaveEvents.size());
        assertEquals(PlayerLifecycleTracker.PlayerEventType.LEAVE, leaveEvents.getFirst().type());
        assertEquals("u2", leaveEvents.getFirst().player().uuid());
    }

    @Test
    void emitsDeathAndRespawnOnAliveTransitions() {
        PlayerLifecycleTracker tracker = new PlayerLifecycleTracker();
        tracker.update(List.of(player("u1", "Self", true, true)));

        List<PlayerLifecycleTracker.PlayerEvent> deathEvents = tracker.update(
            List.of(player("u1", "Self", false, true))
        );
        assertEquals(1, deathEvents.size());
        assertEquals(PlayerLifecycleTracker.PlayerEventType.DEATH, deathEvents.getFirst().type());
        assertEquals("u1", deathEvents.getFirst().player().uuid());

        List<PlayerLifecycleTracker.PlayerEvent> respawnEvents = tracker.update(
            List.of(player("u1", "Self", true, true))
        );
        assertEquals(1, respawnEvents.size());
        assertEquals(PlayerLifecycleTracker.PlayerEventType.RESPAWN, respawnEvents.getFirst().type());
        assertEquals("u1", respawnEvents.getFirst().player().uuid());
    }

    @Test
    void resetClearsStateAndPreventsReplay() {
        PlayerLifecycleTracker tracker = new PlayerLifecycleTracker();
        tracker.update(List.of(player("u1", "Self", true, true)));
        tracker.reset();

        List<PlayerLifecycleTracker.PlayerEvent> events = tracker.update(
            List.of(player("u1", "Self", true, true), player("u2", "Other", true, false))
        );

        assertTrue(events.isEmpty());
    }

    @Test
    void transientMissingPlayerDoesNotEmitLeaveOrJoin() {
        PlayerLifecycleTracker tracker = new PlayerLifecycleTracker(2);
        tracker.update(List.of(player("u1", "Self", true, true), player("u2", "Other", true, false)));

        List<PlayerLifecycleTracker.PlayerEvent> firstMissing = tracker.update(
            List.of(player("u1", "Self", true, true))
        );
        assertTrue(firstMissing.isEmpty());

        List<PlayerLifecycleTracker.PlayerEvent> reappear = tracker.update(
            List.of(player("u1", "Self", true, true), player("u2", "Other", true, false))
        );
        assertTrue(reappear.isEmpty());
    }

    @Test
    void emitsLeaveAfterGraceTicks() {
        PlayerLifecycleTracker tracker = new PlayerLifecycleTracker(2);
        tracker.update(List.of(player("u1", "Self", true, true), player("u2", "Other", true, false)));

        List<PlayerLifecycleTracker.PlayerEvent> firstMissing = tracker.update(
            List.of(player("u1", "Self", true, true))
        );
        assertTrue(firstMissing.isEmpty());

        List<PlayerLifecycleTracker.PlayerEvent> secondMissing = tracker.update(
            List.of(player("u1", "Self", true, true))
        );
        assertEquals(1, secondMissing.size());
        assertEquals(PlayerLifecycleTracker.PlayerEventType.LEAVE, secondMissing.getFirst().type());
        assertEquals("u2", secondMissing.getFirst().player().uuid());
    }

    @Test
    void unknownAliveStateDoesNotTriggerRespawnAfterDeath() {
        PlayerLifecycleTracker tracker = new PlayerLifecycleTracker(2);
        tracker.update(List.of(player("u1", "Self", true, true)));

        List<PlayerLifecycleTracker.PlayerEvent> deathEvents = tracker.update(
            List.of(player("u1", "Self", false, true))
        );
        assertEquals(1, deathEvents.size());
        assertEquals(PlayerLifecycleTracker.PlayerEventType.DEATH, deathEvents.getFirst().type());

        List<PlayerLifecycleTracker.PlayerEvent> unknownAliveTick = tracker.update(
            List.of(playerUnknownAlive("u1", "Self", true))
        );
        assertTrue(unknownAliveTick.isEmpty());

        List<PlayerLifecycleTracker.PlayerEvent> stillDeadEvents = tracker.update(
            List.of(player("u1", "Self", false, true))
        );
        assertTrue(stillDeadEvents.isEmpty());
    }

    private static PlayerLifecycleTracker.PlayerSnapshot player(String uuid, String name, boolean alive, boolean self) {
        return new PlayerLifecycleTracker.PlayerSnapshot(uuid, name, alive, self);
    }

    private static PlayerLifecycleTracker.PlayerSnapshot playerUnknownAlive(String uuid, String name, boolean self) {
        return new PlayerLifecycleTracker.PlayerSnapshot(uuid, name, false, self, false);
    }
}
