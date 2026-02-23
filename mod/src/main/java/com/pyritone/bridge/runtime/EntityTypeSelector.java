package com.pyritone.bridge.runtime;

import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import net.minecraft.entity.Entity;
import net.minecraft.entity.mob.MobEntity;
import net.minecraft.entity.player.PlayerEntity;

import java.util.HashSet;
import java.util.Objects;
import java.util.Set;
import java.util.regex.Pattern;

public final class EntityTypeSelector {
    public static final String GROUP_PLAYERS = "group:players";
    public static final String GROUP_MOBS = "group:mobs";

    private static final Pattern ENTITY_ID_PATTERN = Pattern.compile("^[a-z0-9_.-]+:[a-z0-9_./-]+$");

    private final boolean includePlayers;
    private final boolean includeMobs;
    private final Set<String> explicitTypeIds;

    private EntityTypeSelector(boolean includePlayers, boolean includeMobs, Set<String> explicitTypeIds) {
        this.includePlayers = includePlayers;
        this.includeMobs = includeMobs;
        this.explicitTypeIds = Set.copyOf(explicitTypeIds);
    }

    public static EntityTypeSelector fromParams(JsonObject params) {
        if (params == null || !params.has("types") || params.get("types").isJsonNull()) {
            return allowAll();
        }

        JsonElement typesElement = params.get("types");
        if (!typesElement.isJsonArray()) {
            throw new IllegalArgumentException("entities.list params.types must be an array of strings");
        }

        JsonArray typeArray = typesElement.getAsJsonArray();
        boolean includePlayers = false;
        boolean includeMobs = false;
        Set<String> explicitTypeIds = new HashSet<>();

        for (int index = 0; index < typeArray.size(); index += 1) {
            JsonElement entry = typeArray.get(index);
            if (!entry.isJsonPrimitive() || !entry.getAsJsonPrimitive().isString()) {
                throw new IllegalArgumentException("entities.list params.types entries must be strings");
            }

            String rawValue = entry.getAsString();
            String value = rawValue == null ? "" : rawValue.trim();
            if (value.isEmpty()) {
                throw new IllegalArgumentException("entities.list params.types entries must be non-empty strings");
            }

            if (value.startsWith("group:")) {
                switch (value) {
                    case GROUP_PLAYERS -> includePlayers = true;
                    case GROUP_MOBS -> includeMobs = true;
                    default -> throw new IllegalArgumentException(
                        "Unknown entities.list group token: "
                            + value
                            + " (supported: "
                            + GROUP_PLAYERS
                            + ", "
                            + GROUP_MOBS
                            + ")"
                    );
                }
                continue;
            }

            if (!ENTITY_ID_PATTERN.matcher(value).matches()) {
                throw new IllegalArgumentException(
                    "Invalid entities.list types entry at index "
                        + index
                        + ": expected entity id (namespace:path) or group token"
                );
            }

            explicitTypeIds.add(value);
        }

        return new EntityTypeSelector(includePlayers, includeMobs, explicitTypeIds);
    }

    public boolean matches(Entity entity, String typeId) {
        Objects.requireNonNull(entity, "entity");
        return matches(typeId, entity instanceof PlayerEntity, entity instanceof MobEntity);
    }

    boolean matches(String typeId, boolean isPlayer, boolean isMob) {
        if (!hasFilters()) {
            return true;
        }
        if (includePlayers && isPlayer) {
            return true;
        }
        if (includeMobs && isMob) {
            return true;
        }
        return typeId != null && explicitTypeIds.contains(typeId);
    }

    private boolean hasFilters() {
        return includePlayers || includeMobs || !explicitTypeIds.isEmpty();
    }

    private static EntityTypeSelector allowAll() {
        return new EntityTypeSelector(false, false, Set.of());
    }
}
