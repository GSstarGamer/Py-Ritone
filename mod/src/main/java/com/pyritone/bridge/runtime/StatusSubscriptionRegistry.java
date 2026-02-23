package com.pyritone.bridge.runtime;

import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.ConcurrentHashMap;

public final class StatusSubscriptionRegistry {
    private final Map<String, SubscriptionState> subscriptions = new ConcurrentHashMap<>();

    public void clear() {
        subscriptions.clear();
    }

    public void subscribe(String sessionId, String statusDigest, long nowMs) {
        if (sessionId == null || sessionId.isBlank()) {
            return;
        }

        subscriptions.compute(sessionId, (ignored, existing) -> {
            SubscriptionState state = existing == null ? new SubscriptionState() : existing;
            state.seed(statusDigest, nowMs);
            return state;
        });
    }

    public boolean unsubscribe(String sessionId) {
        if (sessionId == null || sessionId.isBlank()) {
            return false;
        }
        return subscriptions.remove(sessionId) != null;
    }

    public void retainSessions(Set<String> activeSessionIds) {
        if (activeSessionIds == null) {
            clear();
            return;
        }
        subscriptions.keySet().retainAll(activeSessionIds);
    }

    public Optional<Emission> evaluate(
        String sessionId,
        String statusDigest,
        long nowMs,
        long heartbeatIntervalMs
    ) {
        if (sessionId == null || sessionId.isBlank()) {
            return Optional.empty();
        }

        SubscriptionState state = subscriptions.get(sessionId);
        if (state == null) {
            return Optional.empty();
        }
        return Optional.ofNullable(state.evaluate(statusDigest, nowMs, heartbeatIntervalMs));
    }

    private static final class SubscriptionState {
        private String lastDigest;
        private long lastEmittedAtMs;
        private long sequence;

        private synchronized void seed(String statusDigest, long nowMs) {
            this.lastDigest = statusDigest;
            this.lastEmittedAtMs = nowMs;
            this.sequence = 0;
        }

        private synchronized Emission evaluate(String statusDigest, long nowMs, long heartbeatIntervalMs) {
            boolean changed = lastDigest == null || !lastDigest.equals(statusDigest);
            if (changed) {
                lastDigest = statusDigest;
                lastEmittedAtMs = nowMs;
                sequence += 1;
                return new Emission("change", sequence);
            }

            long interval = Math.max(heartbeatIntervalMs, 1L);
            if (nowMs - lastEmittedAtMs >= interval) {
                lastEmittedAtMs = nowMs;
                sequence += 1;
                return new Emission("heartbeat", sequence);
            }

            return null;
        }
    }

    public record Emission(String reason, long sequence) {
    }
}
