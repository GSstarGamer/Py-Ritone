package com.pyritone.bridge.net;

import com.google.gson.JsonObject;
import com.google.gson.JsonSyntaxException;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

class ProtocolCodecTest {
    @Test
    void parsesJsonObjectPayload() {
        JsonObject parsed = ProtocolCodec.parseObject("{\"type\":\"request\",\"id\":\"1\"}");
        assertEquals("request", parsed.get("type").getAsString());
    }

    @Test
    void rejectsNonObjectPayload() {
        assertThrows(JsonSyntaxException.class, () -> ProtocolCodec.parseObject("[]"));
    }

    @Test
    void successResponseHasExpectedShape() {
        JsonObject result = new JsonObject();
        result.addProperty("pong", true);

        JsonObject response = ProtocolCodec.successResponse("abc", result);

        assertEquals("response", response.get("type").getAsString());
        assertEquals("abc", response.get("id").getAsString());
        assertTrue(response.get("ok").getAsBoolean());
    }
}
