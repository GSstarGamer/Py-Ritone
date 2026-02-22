package com.pyritone.bridge.net;

import com.google.gson.JsonObject;
import org.slf4j.Logger;

import java.io.BufferedReader;
import java.io.BufferedWriter;
import java.io.Closeable;
import java.io.IOException;
import java.io.InputStreamReader;
import java.io.OutputStreamWriter;
import java.net.InetAddress;
import java.net.InetSocketAddress;
import java.net.ServerSocket;
import java.net.Socket;
import java.nio.charset.StandardCharsets;
import java.util.Set;
import java.util.UUID;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.atomic.AtomicBoolean;

public final class SocketBridgeServer implements Closeable {
    private final String host;
    private final int port;
    private final RequestHandler requestHandler;
    private final Logger logger;

    private final Set<ClientSession> sessions = ConcurrentHashMap.newKeySet();
    private final ExecutorService acceptExecutor = Executors.newSingleThreadExecutor(r -> {
        Thread thread = new Thread(r, "pyritone-bridge-accept");
        thread.setDaemon(true);
        return thread;
    });
    private final ExecutorService sessionExecutor = Executors.newCachedThreadPool(r -> {
        Thread thread = new Thread(r, "pyritone-bridge-session");
        thread.setDaemon(true);
        return thread;
    });

    private final AtomicBoolean running = new AtomicBoolean(false);
    private volatile ServerSocket serverSocket;
    private volatile int boundPort;

    public SocketBridgeServer(String host, int port, RequestHandler requestHandler, Logger logger) {
        this.host = host;
        this.port = port;
        this.requestHandler = requestHandler;
        this.logger = logger;
    }

    public void start() throws IOException {
        if (running.get()) {
            return;
        }

        ServerSocket socket = new ServerSocket();
        socket.bind(new InetSocketAddress(InetAddress.getByName(host), port));
        serverSocket = socket;
        boundPort = socket.getLocalPort();
        running.set(true);

        acceptExecutor.submit(this::acceptLoop);
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

        try {
            if (serverSocket != null) {
                serverSocket.close();
            }
        } catch (IOException exception) {
            logger.debug("Failed to close bridge server socket cleanly", exception);
        }

        for (ClientSession session : sessions) {
            session.close();
        }
        sessions.clear();

        acceptExecutor.shutdownNow();
        sessionExecutor.shutdownNow();
    }

    private void acceptLoop() {
        while (running.get()) {
            try {
                Socket socket = serverSocket.accept();
                socket.setTcpNoDelay(true);

                ClientSession session = new ClientSession(socket, logger);
                sessions.add(session);
                sessionExecutor.submit(() -> runSession(session));
            } catch (IOException exception) {
                if (running.get()) {
                    logger.warn("Bridge accept loop error", exception);
                }
            }
        }
    }

    private void runSession(ClientSession session) {
        try {
            session.loop(requestHandler);
        } finally {
            sessions.remove(session);
            session.close();
        }
    }

    public interface RequestHandler {
        JsonObject handleRequest(ClientSession session, JsonObject request);
    }

    public static final class ClientSession implements Closeable {
        private final String sessionId = UUID.randomUUID().toString();
        private final Socket socket;
        private final BufferedReader reader;
        private final BufferedWriter writer;
        private final Logger logger;
        private final AtomicBoolean authenticated = new AtomicBoolean(false);
        private final AtomicBoolean closed = new AtomicBoolean(false);

        private ClientSession(Socket socket, Logger logger) throws IOException {
            this.socket = socket;
            this.reader = new BufferedReader(new InputStreamReader(socket.getInputStream(), StandardCharsets.UTF_8));
            this.writer = new BufferedWriter(new OutputStreamWriter(socket.getOutputStream(), StandardCharsets.UTF_8));
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
            if (closed.get()) {
                return;
            }
            synchronized (writer) {
                try {
                    writer.write(ProtocolCodec.toLine(payload));
                    writer.newLine();
                    writer.flush();
                } catch (IOException exception) {
                    logger.debug("Failed writing payload to session {}", sessionId, exception);
                    close();
                }
            }
        }

        @Override
        public void close() {
            if (!closed.getAndSet(true)) {
                try {
                    socket.close();
                } catch (IOException ignored) {
                    // Nothing useful to do on shutdown.
                }
            }
        }

        private void loop(RequestHandler requestHandler) {
            while (!closed.get()) {
                String line;
                try {
                    line = reader.readLine();
                } catch (IOException exception) {
                    break;
                }

                if (line == null) {
                    break;
                }

                try {
                    JsonObject request = ProtocolCodec.parseObject(line);
                    JsonObject response = requestHandler.handleRequest(this, request);
                    if (response != null) {
                        send(response);
                    }
                } catch (Exception exception) {
                    logger.debug("Session {} received invalid payload", sessionId, exception);
                    send(ProtocolCodec.errorResponse(null, "BAD_REQUEST", "Malformed request payload"));
                }
            }
        }
    }
}
