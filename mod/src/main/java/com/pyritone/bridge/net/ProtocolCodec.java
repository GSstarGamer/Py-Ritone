package com.pyritone.bridge.net;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import com.google.gson.JsonSyntaxException;

import java.time.Instant;

public final class ProtocolCodec {
    private static final Gson GSON = new GsonBuilder().disableHtmlEscaping().create();

    private ProtocolCodec() {
    }

    public static JsonObject parseObject(String line) {
        JsonElement element = JsonParser.parseString(line);
        if (!element.isJsonObject()) {
            throw new JsonSyntaxException("Expected a JSON object");
        }
        return element.getAsJsonObject();
    }

    public static String toLine(JsonObject payload) {
        return GSON.toJson(payload);
    }

    public static JsonObject successResponse(String id, JsonElement result) {
        JsonObject response = new JsonObject();
        response.addProperty("type", "response");
        if (id != null) {
            response.addProperty("id", id);
        }
        response.addProperty("ok", true);
        response.add("result", result);
        return response;
    }

    public static JsonObject errorResponse(String id, String code, String message) {
        return errorResponse(id, code, message, null);
    }

    public static JsonObject errorResponse(String id, String code, String message, JsonElement data) {
        JsonObject error = new JsonObject();
        error.addProperty("code", code);
        error.addProperty("message", message);
        if (data != null && !data.isJsonNull()) {
            error.add("data", data);
        }

        JsonObject response = new JsonObject();
        response.addProperty("type", "response");
        if (id != null) {
            response.addProperty("id", id);
        }
        response.addProperty("ok", false);
        response.add("error", error);
        return response;
    }

    public static JsonObject eventEnvelope(String eventName, JsonObject data) {
        JsonObject event = new JsonObject();
        event.addProperty("type", "event");
        event.addProperty("event", eventName);
        event.add("data", data);
        event.addProperty("ts", Instant.now().toString());
        return event;
    }

    public static String requestId(JsonObject payload) {
        if (!payload.has("id") || !payload.get("id").isJsonPrimitive()) {
            return null;
        }
        return payload.get("id").getAsString();
    }
}
