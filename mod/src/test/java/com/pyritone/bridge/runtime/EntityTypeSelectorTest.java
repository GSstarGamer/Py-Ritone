package com.pyritone.bridge.runtime;

import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.junit.jupiter.api.Assertions.assertFalse;

class EntityTypeSelectorTest {
    @Test
    void noTypesMatchesEverything() {
        EntityTypeSelector selector = EntityTypeSelector.fromParams(new JsonObject());

        assertTrue(selector.matches("minecraft:zombie", false, true));
        assertTrue(selector.matches("minecraft:player", true, false));
        assertTrue(selector.matches("minecraft:boat", false, false));
    }

    @Test
    void groupPlayersMatchesOnlyPlayers() {
        EntityTypeSelector selector = EntityTypeSelector.fromParams(paramsWithTypes(EntityTypeSelector.GROUP_PLAYERS));

        assertTrue(selector.matches("minecraft:player", true, false));
        assertFalse(selector.matches("minecraft:zombie", false, true));
        assertFalse(selector.matches("minecraft:boat", false, false));
    }

    @Test
    void groupMobsMatchesOnlyMobs() {
        EntityTypeSelector selector = EntityTypeSelector.fromParams(paramsWithTypes(EntityTypeSelector.GROUP_MOBS));

        assertTrue(selector.matches("minecraft:zombie", false, true));
        assertFalse(selector.matches("minecraft:player", true, false));
        assertFalse(selector.matches("minecraft:item", false, false));
    }

    @Test
    void explicitIdsMatchConfiguredIds() {
        EntityTypeSelector selector = EntityTypeSelector.fromParams(paramsWithTypes("minecraft:zombie", "minecraft:skeleton"));

        assertTrue(selector.matches("minecraft:zombie", false, true));
        assertTrue(selector.matches("minecraft:skeleton", false, true));
        assertFalse(selector.matches("minecraft:creeper", false, true));
    }

    @Test
    void mixedGroupsAndIdsUseInclusiveMatching() {
        EntityTypeSelector selector = EntityTypeSelector.fromParams(
            paramsWithTypes(EntityTypeSelector.GROUP_PLAYERS, "minecraft:armor_stand")
        );

        assertTrue(selector.matches("minecraft:player", true, false));
        assertTrue(selector.matches("minecraft:armor_stand", false, false));
        assertFalse(selector.matches("minecraft:zombie", false, true));
    }

    @Test
    void unknownGroupTokenRaisesError() {
        IllegalArgumentException error = assertThrows(
            IllegalArgumentException.class,
            () -> EntityTypeSelector.fromParams(paramsWithTypes("group:unknown"))
        );

        assertTrue(error.getMessage().contains("Unknown entities.list group token"));
    }

    @Test
    void invalidTypesEntryRaisesError() {
        JsonObject params = new JsonObject();
        JsonArray types = new JsonArray();
        types.add(123);
        params.add("types", types);

        IllegalArgumentException error = assertThrows(
            IllegalArgumentException.class,
            () -> EntityTypeSelector.fromParams(params)
        );

        assertTrue(error.getMessage().contains("params.types entries must be strings"));
    }

    private static JsonObject paramsWithTypes(String... entries) {
        JsonObject params = new JsonObject();
        JsonArray types = new JsonArray();
        for (String entry : entries) {
            types.add(entry);
        }
        params.add("types", types);
        return params;
    }
}
