package com.pyritone.bridge.net;

import com.google.gson.JsonObject;
import org.java_websocket.client.WebSocketClient;
import org.java_websocket.handshake.ServerHandshake;
import org.junit.jupiter.api.Test;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.net.URI;
import java.util.concurrent.BlockingQueue;
import java.util.concurrent.LinkedBlockingQueue;
import java.util.concurrent.TimeUnit;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

class WebSocketBridgeServerAuthTest {
    private static final Logger LOGGER = LoggerFactory.getLogger(WebSocketBridgeServerAuthTest.class);

    @Test
    void enforcesAuthBeforeProtectedMethod() throws Exception {
        WebSocketBridgeServer server = new WebSocketBridgeServer("127.0.0.1", 0, "/ws", (session, request) -> {
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
            URI uri = new URI("ws://127.0.0.1:" + server.getBoundPort() + "/ws");

            TestClient client = new TestClient(uri);
            try {
                assertTrue(client.connectBlocking(5, TimeUnit.SECONDS));

                client.send("{\"type\":\"request\",\"id\":\"1\",\"method\":\"ping\",\"params\":{}}");
                JsonObject unauthorized = ProtocolCodec.parseObject(client.awaitMessage());
                assertFalse(unauthorized.get("ok").getAsBoolean());
                assertEquals("UNAUTHORIZED", unauthorized.getAsJsonObject("error").get("code").getAsString());

                client.send("{\"type\":\"request\",\"id\":\"2\",\"method\":\"auth.login\",\"params\":{\"token\":\"token\"}}");
                JsonObject auth = ProtocolCodec.parseObject(client.awaitMessage());
                assertTrue(auth.get("ok").getAsBoolean());

                client.send("{\"type\":\"request\",\"id\":\"3\",\"method\":\"ping\",\"params\":{}}");
                JsonObject authorized = ProtocolCodec.parseObject(client.awaitMessage());
                assertTrue(authorized.get("ok").getAsBoolean());
            } finally {
                client.closeBlocking();
            }
        } finally {
            server.close();
        }
    }

    private static final class TestClient extends WebSocketClient {
        private final BlockingQueue<String> inboundMessages = new LinkedBlockingQueue<>();

        private TestClient(URI serverUri) {
            super(serverUri);
        }

        @Override
        public void onOpen(ServerHandshake handshakedata) {
            // no-op
        }

        @Override
        public void onMessage(String message) {
            inboundMessages.offer(message);
        }

        @Override
        public void onClose(int code, String reason, boolean remote) {
            // no-op
        }

        @Override
        public void onError(Exception ex) {
            // no-op
        }

        private String awaitMessage() throws Exception {
            String message = inboundMessages.poll(5, TimeUnit.SECONDS);
            if (message == null) {
                throw new AssertionError("Timed out waiting for websocket message");
            }
            return message;
        }
    }
}
