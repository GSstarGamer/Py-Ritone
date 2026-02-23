package com.pyritone.bridge;

import com.google.gson.JsonObject;
import com.pyritone.bridge.net.ProtocolCodec;
import com.pyritone.bridge.net.WebSocketBridgeServer;
import org.java_websocket.client.WebSocketClient;
import org.java_websocket.handshake.ServerHandshake;
import org.junit.jupiter.api.Test;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.lang.reflect.Field;
import java.lang.reflect.Method;
import java.net.URI;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.TimeUnit;

import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

class PyritoneBridgeClientModSessionGateTest {
    private static final Logger LOGGER = LoggerFactory.getLogger(PyritoneBridgeClientModSessionGateTest.class);

    @Test
    void detectsAnotherAuthenticatedSessionForSingleSessionPolicy() throws Exception {
        WebSocketBridgeServer server = new WebSocketBridgeServer("127.0.0.1", 0, "/ws", (session, request) -> {
            String id = ProtocolCodec.requestId(request);
            JsonObject result = new JsonObject();
            result.addProperty("ok", true);
            return ProtocolCodec.successResponse(id, result);
        }, LOGGER);

        try {
            server.start();
            URI uri = new URI("ws://127.0.0.1:" + server.getBoundPort() + "/ws");

            TestClient clientA = new TestClient(uri);
            TestClient clientB = new TestClient(uri);
            try {
                assertTrue(clientA.connectBlocking(5, TimeUnit.SECONDS));
                assertTrue(clientB.connectBlocking(5, TimeUnit.SECONDS));
                waitForSessionCount(server, 2);

                List<WebSocketBridgeServer.ClientSession> sessions = new ArrayList<>(server.sessionSnapshot());
                WebSocketBridgeServer.ClientSession first = sessions.get(0);
                WebSocketBridgeServer.ClientSession second = sessions.get(1);
                first.setAuthenticated(true);

                PyritoneBridgeClientMod mod = new PyritoneBridgeClientMod();
                Field serverField = PyritoneBridgeClientMod.class.getDeclaredField("server");
                serverField.setAccessible(true);
                serverField.set(mod, server);

                Method hasAnother = PyritoneBridgeClientMod.class.getDeclaredMethod(
                    "hasAnotherAuthenticatedSession",
                    WebSocketBridgeServer.ClientSession.class
                );
                hasAnother.setAccessible(true);

                assertFalse((boolean) hasAnother.invoke(mod, first));
                assertTrue((boolean) hasAnother.invoke(mod, second));
            } finally {
                clientA.closeBlocking();
                clientB.closeBlocking();
            }
        } finally {
            server.close();
        }
    }

    private static void waitForSessionCount(WebSocketBridgeServer server, int expected) throws Exception {
        long deadline = System.nanoTime() + TimeUnit.SECONDS.toNanos(5);
        while (System.nanoTime() < deadline) {
            if (server.sessionSnapshot().size() == expected) {
                return;
            }
            Thread.sleep(10L);
        }
        throw new AssertionError("Timed out waiting for " + expected + " websocket sessions");
    }

    private static final class TestClient extends WebSocketClient {
        private TestClient(URI serverUri) {
            super(serverUri);
        }

        @Override
        public void onOpen(ServerHandshake handshakedata) {
            // no-op
        }

        @Override
        public void onMessage(String message) {
            // no-op
        }

        @Override
        public void onClose(int code, String reason, boolean remote) {
            // no-op
        }

        @Override
        public void onError(Exception ex) {
            // no-op
        }
    }
}
