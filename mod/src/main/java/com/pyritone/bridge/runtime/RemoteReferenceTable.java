package com.pyritone.bridge.runtime;

import java.util.HashMap;
import java.util.IdentityHashMap;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.ConcurrentHashMap;

public final class RemoteReferenceTable {
    private final Map<String, SessionReferences> sessions = new ConcurrentHashMap<>();

    public void clear() {
        sessions.clear();
    }

    public void clearSession(String sessionId) {
        if (sessionId == null || sessionId.isBlank()) {
            return;
        }
        sessions.remove(sessionId);
    }

    public void retainSessions(Set<String> activeSessionIds) {
        if (activeSessionIds == null) {
            clear();
            return;
        }
        sessions.keySet().retainAll(activeSessionIds);
    }

    public String store(String sessionId, Object value) {
        if (sessionId == null || sessionId.isBlank()) {
            throw new IllegalArgumentException("sessionId is required");
        }
        if (value == null) {
            throw new IllegalArgumentException("value is required");
        }
        SessionReferences references = sessions.computeIfAbsent(sessionId, ignored -> new SessionReferences());
        return references.store(value);
    }

    public Optional<Object> resolve(String sessionId, String referenceId) {
        if (sessionId == null || sessionId.isBlank() || referenceId == null || referenceId.isBlank()) {
            return Optional.empty();
        }
        SessionReferences references = sessions.get(sessionId);
        if (references == null) {
            return Optional.empty();
        }
        return references.resolve(referenceId);
    }

    private static final class SessionReferences {
        private final Map<String, Object> byReferenceId = new HashMap<>();
        private final IdentityHashMap<Object, String> byIdentity = new IdentityHashMap<>();
        private long sequence = 1L;

        private synchronized String store(Object value) {
            String existing = byIdentity.get(value);
            if (existing != null) {
                return existing;
            }

            String referenceId = "ref-" + sequence++;
            byReferenceId.put(referenceId, value);
            byIdentity.put(value, referenceId);
            return referenceId;
        }

        private synchronized Optional<Object> resolve(String referenceId) {
            return Optional.ofNullable(byReferenceId.get(referenceId));
        }
    }
}
