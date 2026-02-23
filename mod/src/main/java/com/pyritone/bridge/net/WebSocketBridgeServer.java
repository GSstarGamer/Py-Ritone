package com.pyritone.bridge.net;

import com.google.gson.JsonObject;
import org.java_websocket.WebSocket;
import org.java_websocket.framing.CloseFrame;
import org.java_websocket.handshake.ClientHandshake;
import org.java_websocket.server.WebSocketServer;
import org.slf4j.Logger;

import java.io.Closeable;
import java.io.IOException;
import java.net.InetAddress;
import java.net.InetSocketAddress;
import java.util.Map;
import java.util.Set;
import java.util.UUID;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.concurrent.atomic.AtomicReference;

public final class WebSocketBridgeServer implements Closeable {
    private static final long STARTUP_TIMEOUT_MS = 5000L;

    private final String host;
    private final int port;
    private final String wsPath;
    private final RequestHandler requestHandler;
    private final Logger logger;

    private final Set<ClientSession> sessions = ConcurrentHashMap.newKeySet();
    private final AtomicBoolean running = new AtomicBoolean(false);
    private volatile BridgeWebSocketServer server;
    private volatile int boundPort;

    public WebSocketBridgeServer(String host, int port, String wsPath, RequestHandler requestHandler, Logger logger) {
        this.host = host;
        this.port = port;
        this.wsPath = normalizePath(wsPath);
        this.requestHandler = requestHandler;
        this.logger = logger;
    }

    public void start() throws IOException {
        if (running.get()) {
            return;
        }

        CountDownLatch startedLatch = new CountDownLatch(1);
        AtomicReference<Exception> startupError = new AtomicReference<>();

        InetSocketAddress bindAddress = new InetSocketAddress(InetAddress.getByName(host), port);
        BridgeWebSocketServer nextServer = new BridgeWebSocketServer(bindAddress, startedLatch, startupError);
        nextServer.setReuseAddr(true);
        this.server = nextServer;
        nextServer.start();

        try {
            boolean started = startedLatch.await(STARTUP_TIMEOUT_MS, TimeUnit.MILLISECONDS);
            if (!started) {
                stopQuietly(nextServer);
                this.server = null;
                throw new IOException("Timed out waiting for WebSocket bridge startup");
            }
        } catch (InterruptedException exception) {
            Thread.currentThread().interrupt();
            stopQuietly(nextServer);
            this.server = null;
            throw new IOException("Interrupted while waiting for WebSocket bridge startup", exception);
        }

        Exception startFailure = startupError.get();
        if (startFailure != null) {
            stopQuietly(nextServer);
            this.server = null;
            throw new IOException("Failed to start WebSocket bridge", startFailure);
        }

        int actualPort = nextServer.getPort();
        if (actualPort <= 0) {
            stopQuietly(nextServer);
            this.server = null;
            throw new IOException("WebSocket bridge started without a valid bound port");
        }

        this.boundPort = actualPort;
        running.set(true);
    }

    public boolean isRunning() {
        return running.get();
    }

    public int getBoundPort() {
        return boundPort;
    }

    public void publishEvent(JsonObject event) {
        for (ClientSession session : sessions) {
            if (!session.isAuthenticated()) {
                continue;
            }
            session.send(event);
        }
    }

    @Override
    public void close() {
        if (!running.getAndSet(false)) {
            return;
        }

        BridgeWebSocketServer currentServer = this.server;
        this.server = null;
        if (currentServer != null) {
            stopQuietly(currentServer);
        }

        for (ClientSession session : sessions) {
            session.close();
        }
        sessions.clear();
    }

    public interface RequestHandler {
        JsonObject handleRequest(ClientSession session, JsonObject request);
    }

    public static final class ClientSession implements Closeable {
        private final String sessionId = UUID.randomUUID().toString();
        private final WebSocket socket;
        private final Logger logger;
        private final AtomicBoolean authenticated = new AtomicBoolean(false);
        private final AtomicBoolean closed = new AtomicBoolean(false);

        private ClientSession(WebSocket socket, Logger logger) {
            this.socket = socket;
            this.logger = logger;
        }

        public String sessionId() {
            return sessionId;
        }

        public boolean isAuthenticated() {
            return authenticated.get();
        }

        public void setAuthenticated(boolean authenticated) {
            this.authenticated.set(authenticated);
        }

        public void send(JsonObject payload) {
            if (closed.get() || payload == null) {
                return;
            }

            try {
                if (socket != null && socket.isOpen()) {
                    socket.send(ProtocolCodec.toLine(payload));
                }
            } catch (Exception exception) {
                logger.debug("Failed writing payload to session {}", sessionId, exception);
                close();
            }
        }

        @Override
        public void close() {
            if (!closed.getAndSet(true)) {
                try {
                    if (socket != null) {
                        socket.close();
                    }
                } catch (Exception ignored) {
                    // Nothing useful to do on shutdown.
                }
            }
        }
    }

    private final class BridgeWebSocketServer extends WebSocketServer {
        private final CountDownLatch startedLatch;
        private final AtomicReference<Exception> startupError;
        private final Map<WebSocket, ClientSession> sessionBySocket = new ConcurrentHashMap<>();

        private BridgeWebSocketServer(
            InetSocketAddress address,
            CountDownLatch startedLatch,
            AtomicReference<Exception> startupError
        ) {
            super(address);
            this.startedLatch = startedLatch;
            this.startupError = startupError;
        }

        @Override
        public void onOpen(WebSocket conn, ClientHandshake handshake) {
            if (conn == null) {
                return;
            }

            if (!isExpectedPath(handshake)) {
                conn.close(CloseFrame.POLICY_VALIDATION, "Expected websocket endpoint " + wsPath);
                return;
            }

            ClientSession session = new ClientSession(conn, logger);
            sessionBySocket.put(conn, session);
            sessions.add(session);
        }

        @Override
        public void onClose(WebSocket conn, int code, String reason, boolean remote) {
            if (conn == null) {
                return;
            }

            ClientSession session = sessionBySocket.remove(conn);
            if (session != null) {
                sessions.remove(session);
                session.close();
            }
        }

        @Override
        public void onMessage(WebSocket conn, String message) {
            if (conn == null) {
                return;
            }

            ClientSession session = sessionBySocket.get(conn);
            if (session == null) {
                conn.close(CloseFrame.POLICY_VALIDATION, "Session not initialized");
                return;
            }

            try {
                JsonObject request = ProtocolCodec.parseObject(message);
                JsonObject response = requestHandler.handleRequest(session, request);
                if (response != null) {
                    session.send(response);
                }
            } catch (Exception exception) {
                logger.debug("Session {} received invalid payload", session.sessionId(), exception);
                session.send(ProtocolCodec.errorResponse(null, "BAD_REQUEST", "Malformed request payload"));
            }
        }

        @Override
        public void onError(WebSocket conn, Exception exception) {
            if (conn == null) {
                if (startedLatch.getCount() > 0 && exception != null) {
                    startupError.compareAndSet(null, exception);
                    startedLatch.countDown();
                }
                if (running.get()) {
                    logger.warn("Bridge websocket server error", exception);
                }
                return;
            }

            logger.debug("Bridge websocket session error", exception);
            ClientSession session = sessionBySocket.remove(conn);
            if (session != null) {
                sessions.remove(session);
                session.close();
            }
        }

        @Override
        public void onStart() {
            startedLatch.countDown();
        }
    }

    private static void stopQuietly(WebSocketServer server) {
        try {
            server.stop(1000);
        } catch (InterruptedException exception) {
            Thread.currentThread().interrupt();
        } catch (Exception ignored) {
            // No-op on shutdown.
        }
    }

    private boolean isExpectedPath(ClientHandshake handshake) {
        String resource = handshake != null ? handshake.getResourceDescriptor() : null;
        return wsPath.equals(normalizePath(stripQuery(resource)));
    }

    private static String stripQuery(String path) {
        if (path == null) {
            return null;
        }
        int queryIndex = path.indexOf('?');
        if (queryIndex < 0) {
            return path;
        }
        return path.substring(0, queryIndex);
    }

    private static String normalizePath(String path) {
        if (path == null || path.isBlank()) {
            return "/";
        }
        String normalized = path.startsWith("/") ? path : "/" + path;
        if (normalized.length() > 1 && normalized.endsWith("/")) {
            return normalized.substring(0, normalized.length() - 1);
        }
        return normalized;
    }
}
