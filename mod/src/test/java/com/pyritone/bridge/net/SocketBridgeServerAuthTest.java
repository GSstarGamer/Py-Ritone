package com.pyritone.bridge.net;

import com.google.gson.JsonObject;
import org.junit.jupiter.api.Test;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.BufferedReader;
import java.io.BufferedWriter;
import java.io.InputStreamReader;
import java.io.OutputStreamWriter;
import java.net.Socket;
import java.nio.charset.StandardCharsets;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

class SocketBridgeServerAuthTest {
    private static final Logger LOGGER = LoggerFactory.getLogger(SocketBridgeServerAuthTest.class);

    @Test
    void enforcesAuthBeforeProtectedMethod() throws Exception {
        SocketBridgeServer server = new SocketBridgeServer("127.0.0.1", 0, (session, request) -> {
            String id = ProtocolCodec.requestId(request);
            String method = request.get("method").getAsString();

            if ("auth.login".equals(method)) {
                String token = request.getAsJsonObject("params").get("token").getAsString();
                if ("token".equals(token)) {
                    session.setAuthenticated(true);
                    JsonObject result = new JsonObject();
                    result.addProperty("ok", true);
                    return ProtocolCodec.successResponse(id, result);
                }
                return ProtocolCodec.errorResponse(id, "UNAUTHORIZED", "bad token");
            }

            if (!session.isAuthenticated()) {
                return ProtocolCodec.errorResponse(id, "UNAUTHORIZED", "auth required");
            }

            JsonObject result = new JsonObject();
            result.addProperty("pong", true);
            return ProtocolCodec.successResponse(id, result);
        }, LOGGER);

        try {
            server.start();

            try (Socket socket = new Socket("127.0.0.1", server.getBoundPort())) {
                BufferedReader reader = new BufferedReader(new InputStreamReader(socket.getInputStream(), StandardCharsets.UTF_8));
                BufferedWriter writer = new BufferedWriter(new OutputStreamWriter(socket.getOutputStream(), StandardCharsets.UTF_8));

                writer.write("{\"type\":\"request\",\"id\":\"1\",\"method\":\"ping\",\"params\":{}}\n");
                writer.flush();
                JsonObject unauthorized = ProtocolCodec.parseObject(reader.readLine());
                assertFalse(unauthorized.get("ok").getAsBoolean());
                assertEquals("UNAUTHORIZED", unauthorized.getAsJsonObject("error").get("code").getAsString());

                writer.write("{\"type\":\"request\",\"id\":\"2\",\"method\":\"auth.login\",\"params\":{\"token\":\"token\"}}\n");
                writer.flush();
                JsonObject auth = ProtocolCodec.parseObject(reader.readLine());
                assertTrue(auth.get("ok").getAsBoolean());

                writer.write("{\"type\":\"request\",\"id\":\"3\",\"method\":\"ping\",\"params\":{}}\n");
                writer.flush();
                JsonObject authorized = ProtocolCodec.parseObject(reader.readLine());
                assertTrue(authorized.get("ok").getAsBoolean());
            }
        } finally {
            server.close();
        }
    }
}
