package com.pyritone.bridge;

import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonNull;
import com.google.gson.JsonObject;
import com.pyritone.bridge.command.PyritoneCommand;
import com.pyritone.bridge.config.BridgeConfig;
import com.pyritone.bridge.config.BridgeInfoWriter;
import com.pyritone.bridge.config.TokenManager;
import com.pyritone.bridge.net.ProtocolCodec;
import com.pyritone.bridge.net.SocketBridgeServer;
import com.pyritone.bridge.runtime.BaritoneGateway;
import com.pyritone.bridge.runtime.TaskRegistry;
import com.pyritone.bridge.runtime.TaskSnapshot;
import com.pyritone.bridge.runtime.TaskState;
import com.pyritone.bridge.runtime.WatchPatternRegistry;
import net.fabricmc.api.ClientModInitializer;
import net.fabricmc.fabric.api.client.event.lifecycle.v1.ClientTickEvents;
import net.fabricmc.fabric.api.client.message.v1.ClientSendMessageEvents;
import net.fabricmc.loader.api.FabricLoader;
import net.minecraft.client.MinecraftClient;
import net.minecraft.text.MutableText;
import net.minecraft.text.Text;
import net.minecraft.util.Formatting;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.security.MessageDigest;
import java.time.Instant;
import java.util.List;
import java.util.Optional;

public final class PyritoneBridgeClientMod implements ClientModInitializer {
    private static final Logger LOGGER = LoggerFactory.getLogger(BridgeConfig.MOD_ID);

    private String token;
    private String serverVersion;

    private final TaskRegistry taskRegistry = new TaskRegistry();
    private final WatchPatternRegistry watchPatternRegistry = new WatchPatternRegistry();

    private BaritoneGateway baritoneGateway;
    private SocketBridgeServer server;

    @Override
    public void onInitializeClient() {
        ensureBaritoneSettingsFile();
        this.serverVersion = FabricLoader.getInstance()
            .getModContainer(BridgeConfig.MOD_ID)
            .map(container -> container.getMetadata().getVersion().getFriendlyString())
            .orElse("0.1.0");

        this.token = TokenManager.loadOrCreateToken(LOGGER);
        this.baritoneGateway = new BaritoneGateway(LOGGER, this::onPathEvent);
        this.baritoneGateway.tickApplyPyritoneChatBranding();

        startBridgeServer();

        ClientTickEvents.END_CLIENT_TICK.register(client -> {
            baritoneGateway.tickRegisterPathListener();
            baritoneGateway.tickApplyPyritoneChatBranding();
        });
        ClientSendMessageEvents.ALLOW_CHAT.register(this::handleOutgoingChat);
        ClientSendMessageEvents.ALLOW_COMMAND.register(this::handleOutgoingCommand);

        PyritoneCommand.register(this);

        Runtime.getRuntime().addShutdownHook(new Thread(this::shutdownBridgeServer, "pyritone-bridge-shutdown"));
    }

    public String commandStatusLine() {
        boolean running = server != null && server.isRunning();
        int port = server != null ? server.getBoundPort() : BridgeConfig.DEFAULT_PORT;
        return "Bridge=" + (running ? "UP" : "DOWN") + " host=" + BridgeConfig.DEFAULT_HOST + " port=" + port;
    }

    public int addWatchPattern(String pattern) {
        return watchPatternRegistry.addPattern(pattern);
    }

    public void clearWatchPatterns() {
        watchPatternRegistry.clear();
    }

    public List<String> listWatchPatterns() {
        return watchPatternRegistry.list();
    }

    public Path bridgeInfoPath() {
        return BridgeConfig.bridgeInfoFile();
    }


    private void ensureBaritoneSettingsFile() {
        Path settingsFile = FabricLoader.getInstance().getGameDir().resolve("baritone").resolve("settings.txt");
        if (Files.exists(settingsFile)) {
            return;
        }

        try {
            Files.createDirectories(settingsFile.getParent());
            Files.writeString(
                settingsFile,
                "# Auto-created by Py-Ritone to avoid first-run reset warnings.\n",
                StandardCharsets.UTF_8,
                StandardOpenOption.CREATE_NEW
            );
            LOGGER.info("Created default Baritone settings file at {}", settingsFile.toAbsolutePath());
        } catch (IOException exception) {
            LOGGER.warn("Unable to create default Baritone settings file at {}", settingsFile.toAbsolutePath(), exception);
        }
    }
    private boolean handleOutgoingChat(String message) {
        emitWatchMatches("chat", message);
        return true;
    }

    private boolean handleOutgoingCommand(String command) {
        emitWatchMatches("command", "/" + command);
        return true;
    }

    private void emitWatchMatches(String source, String message) {
        List<String> matches = watchPatternRegistry.matches(message);
        for (String pattern : matches) {
            JsonObject payload = new JsonObject();
            payload.addProperty("pattern", pattern);
            payload.addProperty("message", message);
            payload.addProperty("source", source);
            publishEvent("chat.match", payload);
        }
    }

    private void startBridgeServer() {
        this.server = new SocketBridgeServer(
            BridgeConfig.DEFAULT_HOST,
            BridgeConfig.DEFAULT_PORT,
            this::handleRequest,
            LOGGER
        );

        try {
            this.server.start();
            BridgeInfoWriter.write(
                LOGGER,
                BridgeConfig.DEFAULT_HOST,
                this.server.getBoundPort(),
                token,
                BridgeConfig.PROTOCOL_VERSION,
                serverVersion
            );
            LOGGER.info("Py-Ritone bridge started on {}:{}", BridgeConfig.DEFAULT_HOST, this.server.getBoundPort());
        } catch (Exception exception) {
            LOGGER.error("Failed to start Py-Ritone bridge on {}:{}", BridgeConfig.DEFAULT_HOST, BridgeConfig.DEFAULT_PORT, exception);
        }
    }

    private void shutdownBridgeServer() {
        if (this.server != null) {
            this.server.close();
        }
    }

    private JsonObject handleRequest(SocketBridgeServer.ClientSession session, JsonObject request) {
        String id = ProtocolCodec.requestId(request);
        try {
            String type = asString(request, "type");
            String method = asString(request, "method");
            JsonObject params = asObject(request, "params");

            if (!"request".equals(type)) {
                return ProtocolCodec.errorResponse(id, "BAD_REQUEST", "Expected type=request");
            }
            if (method == null || method.isBlank()) {
                return ProtocolCodec.errorResponse(id, "BAD_REQUEST", "Missing method");
            }

            if (!"auth.login".equals(method) && !"ping".equals(method) && !session.isAuthenticated()) {
                return ProtocolCodec.errorResponse(id, "UNAUTHORIZED", "Authenticate with auth.login first");
            }

            return switch (method) {
                case "auth.login" -> handleAuthLogin(id, params, session);
                case "ping" -> handlePing(id, session);
                case "status.get" -> handleStatus(id, session);
                case "baritone.execute" -> handleBaritoneExecute(id, params);
                case "task.cancel" -> handleTaskCancel(id);
                default -> ProtocolCodec.errorResponse(id, "METHOD_NOT_FOUND", "Unknown method: " + method);
            };
        } catch (Exception exception) {
            LOGGER.error("Unexpected request handling error", exception);
            return ProtocolCodec.errorResponse(id, "INTERNAL_ERROR", "Internal request handling error");
        }
    }

    private JsonObject handleAuthLogin(String id, JsonObject params, SocketBridgeServer.ClientSession session) {
        String candidate = asString(params, "token");
        if (candidate == null || candidate.isBlank()) {
            return ProtocolCodec.errorResponse(id, "BAD_REQUEST", "Missing token");
        }

        if (!constantTimeEquals(token, candidate)) {
            return ProtocolCodec.errorResponse(id, "UNAUTHORIZED", "Invalid token");
        }

        session.setAuthenticated(true);

        JsonObject result = new JsonObject();
        result.addProperty("protocol_version", BridgeConfig.PROTOCOL_VERSION);
        result.addProperty("server_version", serverVersion);
        result.addProperty("session_id", session.sessionId());

        int bridgePort = server != null ? server.getBoundPort() : BridgeConfig.DEFAULT_PORT;
        emitPyritoneNotice(
            "Python client connected on "
                + BridgeConfig.DEFAULT_HOST
                + ":"
                + bridgePort
                + " (session "
                + shortSessionId(session.sessionId())
                + ")"
        );

        return ProtocolCodec.successResponse(id, result);
    }

    private JsonObject handlePing(String id, SocketBridgeServer.ClientSession session) {
        if (session.isAuthenticated()) {
            emitPyritoneNotice("Pong");
        }

        JsonObject result = new JsonObject();
        result.addProperty("pong", true);
        result.addProperty("ts", Instant.now().toString());
        return ProtocolCodec.successResponse(id, result);
    }

    private JsonObject handleStatus(String id, SocketBridgeServer.ClientSession session) {
        JsonObject result = new JsonObject();
        result.addProperty("protocol_version", BridgeConfig.PROTOCOL_VERSION);
        result.addProperty("server_version", serverVersion);
        result.addProperty("host", BridgeConfig.DEFAULT_HOST);
        result.addProperty("port", server != null ? server.getBoundPort() : BridgeConfig.DEFAULT_PORT);
        result.addProperty("authenticated", session.isAuthenticated());
        result.addProperty("baritone_available", baritoneGateway.isAvailable());
        result.addProperty("in_world", baritoneGateway.isInWorld());
        result.add("active_task", taskRegistry.activeAsJson());
        result.add("watch_patterns", watchPatternRegistry.toJsonArray());
        return ProtocolCodec.successResponse(id, result);
    }

    private JsonObject handleBaritoneExecute(String id, JsonObject params) {
        String command = asString(params, "command");
        if (command == null || command.isBlank()) {
            return ProtocolCodec.errorResponse(id, "BAD_REQUEST", "Missing command");
        }

        emitPyritoneNotice("Python execute: " + compactCommand(command));

        if (!baritoneGateway.isAvailable()) {
            emitPyritoneNotice("Python execute blocked: Baritone unavailable");
            return ProtocolCodec.errorResponse(id, "BARITONE_UNAVAILABLE", "Baritone is not available");
        }
        if (!baritoneGateway.isInWorld()) {
            emitPyritoneNotice("Python execute blocked: join a world first");
            return ProtocolCodec.errorResponse(id, "NOT_IN_WORLD", "Join a world before executing commands");
        }

        TaskRegistry.StartResult startResult = taskRegistry.start(command);
        if (startResult.replacedTask() != null) {
            emitTaskEvent("task.canceled", startResult.replacedTask(), "replaced");
        }

        emitTaskEvent("task.started", startResult.startedTask(), "dispatched");

        BaritoneGateway.Outcome outcome = baritoneGateway.executeRaw(command);
        if (!outcome.ok()) {
            emitPyritoneNotice("Python execute failed: " + compactCommand(outcome.message()));
            Optional<TaskSnapshot> failed = taskRegistry.transitionActive(TaskState.FAILED, outcome.message());
            failed.ifPresent(snapshot -> emitTaskEvent("task.failed", snapshot, "execute_failed"));
            return ProtocolCodec.errorResponse(id, "EXECUTION_FAILED", outcome.message());
        }

        Optional<TaskSnapshot> updated = taskRegistry.updateActiveDetail(outcome.message());
        updated.ifPresent(snapshot -> emitTaskEvent("task.progress", snapshot, "command_accepted"));

        JsonObject result = new JsonObject();
        result.addProperty("accepted", true);
        result.add("task", updated.<JsonElement>map(TaskSnapshot::toJson).orElse(startResult.startedTask().toJson()));
        return ProtocolCodec.successResponse(id, result);
    }

    private JsonObject handleTaskCancel(String id) {
        Optional<TaskSnapshot> active = taskRegistry.active();
        if (active.isEmpty()) {
            emitPyritoneNotice("Python cancel requested, but no active task");
            JsonObject result = new JsonObject();
            result.addProperty("canceled", false);
            return ProtocolCodec.successResponse(id, result);
        }

        if (!baritoneGateway.isAvailable()) {
            emitPyritoneNotice("Python cancel blocked: Baritone unavailable");
            return ProtocolCodec.errorResponse(id, "BARITONE_UNAVAILABLE", "Baritone is not available");
        }

        emitPyritoneNotice("Python cancel requested");
        BaritoneGateway.Outcome outcome = baritoneGateway.cancelCurrent();
        if (!outcome.ok()) {
            emitPyritoneNotice("Python cancel failed: " + compactCommand(outcome.message()));
            return ProtocolCodec.errorResponse(id, "EXECUTION_FAILED", outcome.message());
        }

        Optional<TaskSnapshot> canceled = taskRegistry.transitionActive(TaskState.CANCELED, outcome.message());
        canceled.ifPresent(snapshot -> emitTaskEvent("task.canceled", snapshot, "cancel_requested"));
        emitPyritoneNotice("Python cancel accepted");

        JsonObject result = new JsonObject();
        result.addProperty("canceled", true);
        result.add("task", canceled.<JsonElement>map(TaskSnapshot::toJson).orElse(JsonNull.INSTANCE));
        return ProtocolCodec.successResponse(id, result);
    }

    private void onPathEvent(String pathEventName) {
        JsonObject data = new JsonObject();
        data.addProperty("path_event", pathEventName);

        Optional<TaskSnapshot> active = taskRegistry.active();
        active.ifPresent(snapshot -> data.addProperty("task_id", snapshot.taskId()));

        publishEvent("baritone.path_event", data);

        if (active.isEmpty()) {
            return;
        }

        switch (pathEventName) {
            case "AT_GOAL" -> taskRegistry.transitionActive(TaskState.COMPLETED, "Reached goal")
                .ifPresent(snapshot -> emitTaskEvent("task.completed", snapshot, pathEventName));
            case "CANCELED" -> taskRegistry.transitionActive(TaskState.CANCELED, "Baritone canceled")
                .ifPresent(snapshot -> emitTaskEvent("task.canceled", snapshot, pathEventName));
            case "CALC_FAILED", "NEXT_CALC_FAILED" -> taskRegistry.transitionActive(TaskState.FAILED, pathEventName)
                .ifPresent(snapshot -> emitTaskEvent("task.failed", snapshot, pathEventName));
            default -> taskRegistry.updateActiveDetail("Path event: " + pathEventName)
                .ifPresent(snapshot -> emitTaskEvent("task.progress", snapshot, pathEventName));
        }
    }

    private void emitTaskEvent(String eventName, TaskSnapshot taskSnapshot, String stage) {
        JsonObject data = taskSnapshot.toJson();
        if (stage != null) {
            data.addProperty("stage", stage);
        }
        publishEvent(eventName, data);
    }

    private void publishEvent(String eventName, JsonObject data) {
        SocketBridgeServer currentServer = this.server;
        if (currentServer == null || !currentServer.isRunning()) {
            return;
        }
        currentServer.publishEvent(ProtocolCodec.eventEnvelope(eventName, data));
    }

    private static String asString(JsonObject source, String key) {
        if (source == null || !source.has(key) || !source.get(key).isJsonPrimitive()) {
            return null;
        }
        return source.get(key).getAsString();
    }

    private static JsonObject asObject(JsonObject source, String key) {
        if (source == null || !source.has(key) || !source.get(key).isJsonObject()) {
            return new JsonObject();
        }
        return source.getAsJsonObject(key);
    }

    private static boolean constantTimeEquals(String expected, String actual) {
        byte[] left = expected.getBytes(StandardCharsets.UTF_8);
        byte[] right = actual.getBytes(StandardCharsets.UTF_8);
        return MessageDigest.isEqual(left, right);
    }

    private static String shortSessionId(String sessionId) {
        if (sessionId == null || sessionId.length() <= 8) {
            return sessionId;
        }
        return sessionId.substring(0, 8);
    }

    private static String compactCommand(String value) {
        if (value == null) {
            return "";
        }
        String collapsed = value.replaceAll("\\s+", " ").trim();
        if (collapsed.length() <= 72) {
            return collapsed;
        }
        return collapsed.substring(0, 69) + "...";
    }

    private void emitPyritoneNotice(String message) {
        MinecraftClient client = MinecraftClient.getInstance();
        if (client == null) {
            return;
        }

        client.execute(() -> {
            if (client.player == null) {
                return;
            }
            client.player.sendMessage(pyritoneMessage(message), false);
        });
    }

    private static Text pyritoneMessage(String message) {
        MutableText text = pyritonePrefix();
        text.append(Text.literal(" "));
        text.append(Text.literal(message).formatted(Formatting.GRAY));
        return text;
    }

    private static MutableText pyritonePrefix() {
        MutableText prefix = Text.literal("");
        prefix.append(Text.literal("[").formatted(Formatting.DARK_GREEN));
        prefix.append(Text.literal("Py-Ritone").formatted(Formatting.GREEN));
        prefix.append(Text.literal("]").formatted(Formatting.DARK_GREEN));
        return prefix;
    }
}






