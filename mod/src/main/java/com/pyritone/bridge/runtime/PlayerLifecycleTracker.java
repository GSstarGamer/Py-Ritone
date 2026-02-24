package com.pyritone.bridge.runtime;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * Tracks client-visible players and emits lifecycle transitions.
 *
 * <p>First observed snapshot seeds internal state and emits nothing.
 */
public final class PlayerLifecycleTracker {
    private static final int DEFAULT_LEAVE_GRACE_TICKS = 3;

    private final Map<String, PlayerSnapshot> knownByUuid = new HashMap<>();
    private final Map<String, Integer> missingTicksByUuid = new HashMap<>();
    private final int leaveGraceTicks;
    private boolean initialized;

    public PlayerLifecycleTracker() {
        this(DEFAULT_LEAVE_GRACE_TICKS);
    }

    public PlayerLifecycleTracker(int leaveGraceTicks) {
        this.leaveGraceTicks = Math.max(1, leaveGraceTicks);
    }

    public synchronized List<PlayerEvent> update(List<PlayerSnapshot> currentPlayers) {
        List<PlayerEvent> events = new ArrayList<>();
        Map<String, PlayerSnapshot> currentByUuid = new HashMap<>();
        for (PlayerSnapshot snapshot : currentPlayers) {
            if (snapshot == null || snapshot.uuid() == null || snapshot.uuid().isBlank()) {
                continue;
            }
            currentByUuid.put(snapshot.uuid(), snapshot);
        }

        if (!initialized) {
            knownByUuid.clear();
            missingTicksByUuid.clear();
            knownByUuid.putAll(currentByUuid);
            initialized = true;
            return events;
        }

        for (Map.Entry<String, PlayerSnapshot> entry : currentByUuid.entrySet()) {
            PlayerSnapshot current = entry.getValue();
            PlayerSnapshot previous = knownByUuid.get(current.uuid());
            if (previous == null) {
                events.add(new PlayerEvent(PlayerEventType.JOIN, current));
                continue;
            }

            missingTicksByUuid.remove(current.uuid());

            PlayerSnapshot effectiveCurrent = current;
            if (!current.aliveKnown() && previous.aliveKnown()) {
                effectiveCurrent = new PlayerSnapshot(
                    current.uuid(),
                    current.name(),
                    previous.alive(),
                    current.self(),
                    true
                );
                entry.setValue(effectiveCurrent);
            }

            if (previous.aliveKnown() && effectiveCurrent.aliveKnown()) {
                if (previous.alive() && !effectiveCurrent.alive()) {
                    events.add(new PlayerEvent(PlayerEventType.DEATH, effectiveCurrent));
                } else if (!previous.alive() && effectiveCurrent.alive()) {
                    events.add(new PlayerEvent(PlayerEventType.RESPAWN, effectiveCurrent));
                }
            }
        }

        for (PlayerSnapshot previous : knownByUuid.values()) {
            String uuid = previous.uuid();
            if (!currentByUuid.containsKey(uuid)) {
                int missingTicks = missingTicksByUuid.getOrDefault(uuid, 0) + 1;
                if (missingTicks >= leaveGraceTicks) {
                    missingTicksByUuid.remove(uuid);
                    events.add(new PlayerEvent(PlayerEventType.LEAVE, previous));
                } else {
                    missingTicksByUuid.put(uuid, missingTicks);
                    // Keep prior state during short disappearances (for example, death/respawn transitions).
                    currentByUuid.put(uuid, previous);
                }
            }
        }

        knownByUuid.clear();
        knownByUuid.putAll(currentByUuid);
        return events;
    }

    public synchronized void reset() {
        knownByUuid.clear();
        missingTicksByUuid.clear();
        initialized = false;
    }

    public enum PlayerEventType {
        JOIN,
        LEAVE,
        DEATH,
        RESPAWN
    }

    public record PlayerSnapshot(
        String uuid,
        String name,
        boolean alive,
        boolean self,
        boolean aliveKnown
    ) {
        public PlayerSnapshot(String uuid, String name, boolean alive, boolean self) {
            this(uuid, name, alive, self, true);
        }
    }

    public record PlayerEvent(
        PlayerEventType type,
        PlayerSnapshot player
    ) {
    }
}
