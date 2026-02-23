package com.pyritone.bridge.runtime;

import org.junit.jupiter.api.Test;

import java.util.Set;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

class StatusSubscriptionRegistryTest {
    @Test
    void doesNotEmitWithoutSubscription() {
        StatusSubscriptionRegistry registry = new StatusSubscriptionRegistry();

        assertTrue(registry.evaluate("session-a", "digest-1", 1000L, 2000L).isEmpty());
    }

    @Test
    void emitsChangeWhenDigestChanges() {
        StatusSubscriptionRegistry registry = new StatusSubscriptionRegistry();
        registry.subscribe("session-a", "digest-1", 1000L);

        StatusSubscriptionRegistry.Emission change = registry
            .evaluate("session-a", "digest-2", 1200L, 2000L)
            .orElseThrow();

        assertEquals("change", change.reason());
        assertEquals(1L, change.sequence());
    }

    @Test
    void emitsHeartbeatWhenDigestUnchangedAndIntervalElapsed() {
        StatusSubscriptionRegistry registry = new StatusSubscriptionRegistry();
        registry.subscribe("session-a", "digest-1", 1000L);

        assertTrue(registry.evaluate("session-a", "digest-1", 2500L, 2000L).isEmpty());

        StatusSubscriptionRegistry.Emission heartbeat = registry
            .evaluate("session-a", "digest-1", 3000L, 2000L)
            .orElseThrow();
        assertEquals("heartbeat", heartbeat.reason());
        assertEquals(1L, heartbeat.sequence());
    }

    @Test
    void sequenceIncrementsAcrossEmissions() {
        StatusSubscriptionRegistry registry = new StatusSubscriptionRegistry();
        registry.subscribe("session-a", "digest-1", 1000L);

        StatusSubscriptionRegistry.Emission first = registry
            .evaluate("session-a", "digest-2", 1100L, 2000L)
            .orElseThrow();
        StatusSubscriptionRegistry.Emission second = registry
            .evaluate("session-a", "digest-2", 3200L, 2000L)
            .orElseThrow();

        assertEquals(1L, first.sequence());
        assertEquals(2L, second.sequence());
    }

    @Test
    void unsubscribeAndRetainSessionsStopFurtherEmissions() {
        StatusSubscriptionRegistry registry = new StatusSubscriptionRegistry();
        registry.subscribe("session-a", "digest-1", 1000L);
        registry.subscribe("session-b", "digest-1", 1000L);

        assertTrue(registry.unsubscribe("session-a"));
        assertTrue(registry.evaluate("session-a", "digest-2", 1500L, 2000L).isEmpty());

        registry.retainSessions(Set.of("session-a"));
        assertTrue(registry.evaluate("session-b", "digest-2", 1500L, 2000L).isEmpty());
    }
}
