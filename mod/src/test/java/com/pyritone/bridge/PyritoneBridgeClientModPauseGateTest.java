package com.pyritone.bridge;

import com.google.gson.JsonObject;
import org.junit.jupiter.api.Test;

import java.lang.reflect.Method;
import java.util.List;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

class PyritoneBridgeClientModPauseGateTest {
    @Test
    void pauseGateMethodSetMatchesProtocolContract() throws Exception {
        PyritoneBridgeClientMod mod = new PyritoneBridgeClientMod();
        Method isPauseGatedMethod = PyritoneBridgeClientMod.class.getDeclaredMethod(
            "isPauseGatedMethod",
            String.class
        );
        isPauseGatedMethod.setAccessible(true);

        List<String> gatedMethods = List.of(
            "status.get",
            "status.subscribe",
            "status.unsubscribe",
            "entities.list",
            "api.metadata.get",
            "api.construct",
            "api.invoke",
            "baritone.execute",
            "task.cancel"
        );
        for (String method : gatedMethods) {
            assertTrue((boolean) isPauseGatedMethod.invoke(mod, method), method + " should be pause-gated");
        }

        assertFalse((boolean) isPauseGatedMethod.invoke(mod, "auth.login"));
        assertFalse((boolean) isPauseGatedMethod.invoke(mod, "ping"));
    }

    @Test
    void pauseGateErrorReflectsOperatorAndGamePauseState() throws Exception {
        PyritoneBridgeClientMod mod = new PyritoneBridgeClientMod();
        Method pauseGateError = PyritoneBridgeClientMod.class.getDeclaredMethod("pauseGateError", String.class);
        pauseGateError.setAccessible(true);

        assertNull(pauseGateError.invoke(mod, "1"));

        assertTrue(mod.pausePythonExecuteFromPyritoneCommand());
        JsonObject operatorPaused = (JsonObject) pauseGateError.invoke(mod, "2");
        assertNotNull(operatorPaused);
        assertEquals("PAUSED", operatorPaused.getAsJsonObject("error").get("code").getAsString());
        JsonObject operatorPausedData = operatorPaused.getAsJsonObject("error").getAsJsonObject("data");
        assertTrue(operatorPausedData.get("paused").getAsBoolean());
        assertTrue(operatorPausedData.get("operator_paused").getAsBoolean());
        assertFalse(operatorPausedData.get("game_paused").getAsBoolean());
        assertEquals("operator_pause", operatorPausedData.get("reason").getAsString());
        assertTrue(operatorPausedData.get("seq").getAsLong() >= 1L);

        Method setGamePauseActive = PyritoneBridgeClientMod.class.getDeclaredMethod("setGamePauseActive", boolean.class);
        setGamePauseActive.setAccessible(true);
        assertTrue((boolean) setGamePauseActive.invoke(mod, true));

        JsonObject bothPaused = (JsonObject) pauseGateError.invoke(mod, "3");
        JsonObject bothPausedData = bothPaused.getAsJsonObject("error").getAsJsonObject("data");
        assertTrue(bothPausedData.get("paused").getAsBoolean());
        assertTrue(bothPausedData.get("operator_paused").getAsBoolean());
        assertTrue(bothPausedData.get("game_paused").getAsBoolean());
        assertEquals("operator_and_game_pause", bothPausedData.get("reason").getAsString());

        assertTrue(mod.resumePythonExecuteFromPyritoneCommand());
        JsonObject gameOnlyPaused = (JsonObject) pauseGateError.invoke(mod, "4");
        JsonObject gameOnlyPausedData = gameOnlyPaused.getAsJsonObject("error").getAsJsonObject("data");
        assertTrue(gameOnlyPausedData.get("paused").getAsBoolean());
        assertFalse(gameOnlyPausedData.get("operator_paused").getAsBoolean());
        assertTrue(gameOnlyPausedData.get("game_paused").getAsBoolean());
        assertEquals("game_pause", gameOnlyPausedData.get("reason").getAsString());

        assertTrue((boolean) setGamePauseActive.invoke(mod, false));
        assertNull(pauseGateError.invoke(mod, "5"));
    }
}
