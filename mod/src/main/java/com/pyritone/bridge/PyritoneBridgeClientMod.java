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
import com.pyritone.bridge.net.WebSocketBridgeServer;
import com.pyritone.bridge.runtime.BaritoneGateway;
import com.pyritone.bridge.runtime.EntityTypeSelector;
import com.pyritone.bridge.runtime.PlayerLifecycleTracker;
import com.pyritone.bridge.runtime.StatusSubscriptionRegistry;
import com.pyritone.bridge.runtime.TaskRegistry;
import com.pyritone.bridge.runtime.TaskLifecycleResolver;
import com.pyritone.bridge.runtime.TaskSnapshot;
import com.pyritone.bridge.runtime.TaskState;
import com.pyritone.bridge.runtime.TypedApiException;
import com.pyritone.bridge.runtime.TypedApiService;
import com.pyritone.bridge.runtime.WatchPatternRegistry;
import com.mojang.authlib.GameProfile;
import net.fabricmc.api.ClientModInitializer;
import net.fabricmc.fabric.api.client.event.lifecycle.v1.ClientTickEvents;
import net.fabricmc.fabric.api.client.message.v1.ClientReceiveMessageEvents;
import net.fabricmc.fabric.api.client.message.v1.ClientSendMessageEvents;
import net.fabricmc.loader.api.FabricLoader;
import net.minecraft.client.MinecraftClient;
import net.minecraft.client.network.PlayerListEntry;
import net.minecraft.entity.Entity;
import net.minecraft.entity.player.PlayerEntity;
import net.minecraft.registry.Registries;
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
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.CompletionException;
import java.util.concurrent.ExecutionException;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.TimeoutException;
import java.util.concurrent.Callable;

public final class PyritoneBridgeClientMod implements ClientModInitializer {
    private static final Logger LOGGER = LoggerFactory.getLogger(BridgeConfig.MOD_ID);
    private static final Set<String> PAUSE_GATED_METHODS = Set.of(
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

    private String token;
    private String serverVersion;

    private final TaskRegistry taskRegistry = new TaskRegistry();
    private final TaskLifecycleResolver taskLifecycleResolver = new TaskLifecycleResolver();
    private final WatchPatternRegistry watchPatternRegistry = new WatchPatternRegistry();
    private final StatusSubscriptionRegistry statusSubscriptionRegistry = new StatusSubscriptionRegistry();
    private final TypedApiService typedApiService = new TypedApiService(PyritoneBridgeClientMod.class.getClassLoader());
    private final PlayerLifecycleTracker playerLifecycleTracker = new PlayerLifecycleTracker();
    private boolean playerLifecycleInWorld;
    private boolean playerLifecycleSelfJoinEmitted;
    private PlayerLifecycleTracker.PlayerSnapshot lastKnownSelfPlayer;

    private final Object pauseStateLock = new Object();
    private volatile boolean operatorPauseActive;
    private volatile boolean gamePauseActive;
    private volatile boolean effectivePauseActive;
    private volatile long pauseStateSeq;

    private BaritoneGateway baritoneGateway;
    private WebSocketBridgeServer server;

    @Override
    public void onInitializeClient() {
        ensureBaritoneSettingsFile();
        this.serverVersion = FabricLoader.getInstance()
            .getModContainer(BridgeConfig.MOD_ID)
            .map(container -> container.getMetadata().getVersion().getFriendlyString())
            .orElse("0.1.0");

        this.token = TokenManager.loadOrCreateToken(LOGGER);
        this.baritoneGateway = new BaritoneGateway(LOGGER, this::onPathEvent);
        this.typedApiService.registerRoot("baritone", "baritone.api.IBaritone", this::resolvePrimaryBaritone);
        this.baritoneGateway.tickApplyPyritoneChatBranding();

        startBridgeServer();

        ClientTickEvents.END_CLIENT_TICK.register(client -> {
            baritoneGateway.tickRegisterPathListener();
            baritoneGateway.tickRegisterPyritoneHashCommand(
                () -> endPythonSessionsFromPyritoneCommand(),
                () -> pausePythonExecuteFromPyritoneCommand(),
                () -> resumePythonExecuteFromPyritoneCommand()
            );
            baritoneGateway.tickApplyPyritoneChatBranding();
            tickPauseState(client);
            tickPlayerLifecycleEvents(client);
            tickTaskLifecycle();
            tickStatusStreams();
        });
        ClientReceiveMessageEvents.CHAT.register(
            (message, signedMessage, sender, params, receptionTimestamp) -> onIncomingChatMessage(message, sender)
        );
        ClientReceiveMessageEvents.GAME.register(this::onIncomingSystemMessage);
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
        if (applyPyritoneChatControl(message)) {
            return false;
        }
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
        this.server = new WebSocketBridgeServer(
            BridgeConfig.DEFAULT_HOST,
            BridgeConfig.DEFAULT_PORT,
            BridgeConfig.DEFAULT_WS_PATH,
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
        clearPauseStateForShutdown();
        playerLifecycleTracker.reset();
        playerLifecycleInWorld = false;
        playerLifecycleSelfJoinEmitted = false;
        lastKnownSelfPlayer = null;
        statusSubscriptionRegistry.clear();
        typedApiService.clear();
        if (this.server != null) {
            this.server.close();
        }
    }

    private JsonObject handleRequest(WebSocketBridgeServer.ClientSession session, JsonObject request) {
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

            if (isPauseGatedMethod(method)) {
                JsonObject pauseError = pauseGateError(id);
                if (pauseError != null) {
                    return pauseError;
                }
            }

            return switch (method) {
                case "auth.login" -> handleAuthLogin(id, params, session);
                case "ping" -> handlePing(id, session);
                case "status.get" -> handleStatus(id, session);
                case "status.subscribe" -> handleStatusSubscribe(id, session);
                case "status.unsubscribe" -> handleStatusUnsubscribe(id, session);
                case "api.metadata.get" -> handleApiMetadataGet(id, params, session);
                case "api.construct" -> handleApiConstruct(id, params, session);
                case "api.invoke" -> handleApiInvoke(id, params, session);
                case "entities.list" -> handleEntitiesList(id, params);
                case "baritone.execute" -> handleBaritoneExecute(id, params, session);
                case "task.cancel" -> handleTaskCancel(id);
                default -> ProtocolCodec.errorResponse(id, "METHOD_NOT_FOUND", "Unknown method: " + method);
            };
        } catch (Exception exception) {
            LOGGER.error("Unexpected request handling error", exception);
            return ProtocolCodec.errorResponse(id, "INTERNAL_ERROR", "Internal request handling error");
        }
    }

    private JsonObject handleAuthLogin(String id, JsonObject params, WebSocketBridgeServer.ClientSession session) {
        String candidate = asString(params, "token");
        if (candidate == null || candidate.isBlank()) {
            return ProtocolCodec.errorResponse(id, "BAD_REQUEST", "Missing token");
        }

        if (!constantTimeEquals(token, candidate)) {
            return ProtocolCodec.errorResponse(id, "UNAUTHORIZED", "Invalid token");
        }

        if (hasAnotherAuthenticatedSession(session)) {
            return ProtocolCodec.errorResponse(id, "UNAUTHORIZED", "Another Python session is already connected");
        }

        session.setAuthenticated(true);

        emitPauseStateEventToSession(session, currentPauseStateSnapshot());

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

    private JsonObject handlePing(String id, WebSocketBridgeServer.ClientSession session) {
        if (session.isAuthenticated()) {
            emitPyritoneNotice("Pong");
        }

        JsonObject result = new JsonObject();
        result.addProperty("pong", true);
        result.addProperty("ts", Instant.now().toString());
        return ProtocolCodec.successResponse(id, result);
    }

    private JsonObject handleStatus(String id, WebSocketBridgeServer.ClientSession session) {
        return ProtocolCodec.successResponse(id, buildStatusPayload(session));
    }

    private JsonObject handleStatusSubscribe(String id, WebSocketBridgeServer.ClientSession session) {
        long nowMs = System.currentTimeMillis();
        JsonObject status = buildStatusPayload(session);
        statusSubscriptionRegistry.subscribe(session.sessionId(), statusDigest(status), nowMs);

        JsonObject result = new JsonObject();
        result.addProperty("subscribed", true);
        result.addProperty("heartbeat_interval_ms", BridgeConfig.STATUS_HEARTBEAT_INTERVAL_MS);
        result.add("status", status);
        return ProtocolCodec.successResponse(id, result);
    }

    private JsonObject handleStatusUnsubscribe(String id, WebSocketBridgeServer.ClientSession session) {
        boolean wasSubscribed = statusSubscriptionRegistry.unsubscribe(session.sessionId());
        JsonObject result = new JsonObject();
        result.addProperty("subscribed", false);
        result.addProperty("was_subscribed", wasSubscribed);
        return ProtocolCodec.successResponse(id, result);
    }

    private JsonObject handleApiMetadataGet(String id, JsonObject params, WebSocketBridgeServer.ClientSession session) {
        return handleTypedApiRequest(id, () -> typedApiService.metadata(session.sessionId(), params));
    }

    private JsonObject handleApiConstruct(String id, JsonObject params, WebSocketBridgeServer.ClientSession session) {
        return handleTypedApiRequest(id, () -> typedApiService.construct(session.sessionId(), params));
    }

    private JsonObject handleApiInvoke(String id, JsonObject params, WebSocketBridgeServer.ClientSession session) {
        return handleTypedApiRequest(id, () -> typedApiService.invoke(session.sessionId(), params));
    }

    private JsonObject handleEntitiesList(String id, JsonObject params) {
        try {
            JsonObject result = runOnClientThread(() -> {
                MinecraftClient client = MinecraftClient.getInstance();
                if (client == null || client.world == null || client.player == null) {
                    throw new TypedApiException("NOT_IN_WORLD", "Join a world before listing entities");
                }

                EntityTypeSelector selector = EntityTypeSelector.fromParams(params);

                List<JsonObject> entities = new ArrayList<>();
                for (Entity entity : client.world.getEntities()) {
                    if (entity == client.player) {
                        continue;
                    }

                    String typeId = Registries.ENTITY_TYPE.getId(entity.getType()).toString();
                    if (!selector.matches(entity, typeId)) {
                        continue;
                    }

                    JsonObject payload = new JsonObject();
                    payload.addProperty("id", entity.getUuidAsString());
                    payload.addProperty("type_id", typeId);
                    payload.addProperty("category", entity.getType().getSpawnGroup().name().toLowerCase(Locale.ROOT));
                    payload.addProperty("x", entity.getX());
                    payload.addProperty("y", entity.getY());
                    payload.addProperty("z", entity.getZ());
                    payload.addProperty("distance_sq", client.player.squaredDistanceTo(entity));
                    entities.add(payload);
                }

                entities.sort(Comparator.comparingDouble(entity -> entity.get("distance_sq").getAsDouble()));

                JsonArray entries = new JsonArray();
                for (JsonObject entity : entities) {
                    entries.add(entity);
                }

                JsonObject response = new JsonObject();
                response.add("entities", entries);
                return response;
            });
            return ProtocolCodec.successResponse(id, result);
        } catch (IllegalArgumentException exception) {
            return ProtocolCodec.errorResponse(id, "BAD_REQUEST", exception.getMessage());
        } catch (TypedApiException exception) {
            return ProtocolCodec.errorResponse(id, exception.code(), exception.getMessage(), exception.details());
        } catch (TimeoutException exception) {
            return ProtocolCodec.errorResponse(id, "INTERNAL_ERROR", "Timed out waiting for client thread");
        } catch (Exception exception) {
            LOGGER.debug("entities.list request failed", exception);
            return ProtocolCodec.errorResponse(id, "INTERNAL_ERROR", "Unable to list entities");
        }
    }

    private JsonObject buildStatusPayload(WebSocketBridgeServer.ClientSession session) {
        JsonObject result = new JsonObject();
        result.addProperty("protocol_version", BridgeConfig.PROTOCOL_VERSION);
        result.addProperty("server_version", serverVersion);
        result.addProperty("host", BridgeConfig.DEFAULT_HOST);
        result.addProperty("port", server != null ? server.getBoundPort() : BridgeConfig.DEFAULT_PORT);
        result.addProperty("authenticated", session != null && session.isAuthenticated());
        result.addProperty("baritone_available", baritoneGateway.isAvailable());
        result.addProperty("in_world", baritoneGateway.isInWorld());
        result.add("active_task", taskRegistry.activeAsJson());
        result.add("watch_patterns", watchPatternRegistry.toJsonArray());
        JsonObject player = currentPlayerPayload(MinecraftClient.getInstance());
        result.add("player", player != null ? player : JsonNull.INSTANCE);
        return result;
    }

    private static String statusDigest(JsonObject status) {
        return ProtocolCodec.toLine(status);
    }

    private JsonObject handleBaritoneExecute(String id, JsonObject params, WebSocketBridgeServer.ClientSession session) {
        String command = asString(params, "command");
        if (command == null || command.isBlank()) {
            return ProtocolCodec.errorResponse(id, "BAD_REQUEST", "Missing command");
        }

        String label = asString(params, "label");
        String notice = label != null && !label.isBlank() ? label : command;
        emitPyritoneNotice("Python execute: " + compactCommand(notice));

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

        taskLifecycleResolver.start(startResult.startedTask().taskId());
        emitTaskEvent("task.started", startResult.startedTask(), "dispatched");

        BaritoneGateway.Outcome outcome = baritoneGateway.executeRaw(command);
        if (!outcome.ok()) {
            emitPyritoneNotice("Python execute failed: " + compactCommand(outcome.message()));
            Optional<TaskSnapshot> failed = taskRegistry.transitionActive(TaskState.FAILED, outcome.message());
            failed.ifPresent(snapshot -> {
                taskLifecycleResolver.clearForTask(snapshot.taskId());
                emitTaskEvent("task.failed", snapshot, "execute_failed");
            });
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

        taskLifecycleResolver.markApiCancelRequested(active.orElseThrow().taskId());
        Optional<TaskSnapshot> updated = taskRegistry.updateActiveDetail("Cancel requested by API");
        updated.ifPresent(snapshot -> emitTaskEvent("task.progress", snapshot, "cancel_requested"));
        emitPyritoneNotice("Python cancel accepted");

        JsonObject result = new JsonObject();
        result.addProperty("canceled", true);
        result.add("task", updated.<JsonElement>map(TaskSnapshot::toJson).orElse(active.orElseThrow().toJson()));
        return ProtocolCodec.successResponse(id, result);
    }

    private JsonObject handleTypedApiRequest(String id, Callable<JsonObject> action) {
        try {
            JsonObject result = runOnClientThread(action);
            return ProtocolCodec.successResponse(id, result);
        } catch (TypedApiException exception) {
            return ProtocolCodec.errorResponse(id, exception.code(), exception.getMessage(), exception.details());
        } catch (TimeoutException exception) {
            return ProtocolCodec.errorResponse(id, "INTERNAL_ERROR", "Timed out waiting for client thread");
        } catch (Exception exception) {
            LOGGER.debug("Typed API request failed", exception);
            return ProtocolCodec.errorResponse(id, "INTERNAL_ERROR", "Typed API invocation failed");
        }
    }

    private JsonObject runOnClientThread(Callable<JsonObject> action) throws Exception {
        MinecraftClient client = MinecraftClient.getInstance();
        if (client == null) {
            throw new IllegalStateException("Minecraft client is unavailable");
        }

        if (client.isOnThread()) {
            return action.call();
        }

        try {
            return client.submit(() -> {
                try {
                    return action.call();
                } catch (Exception exception) {
                    throw new CompletionException(exception);
                }
            }).get(5, TimeUnit.SECONDS);
        } catch (ExecutionException exception) {
            Throwable cause = exception.getCause();
            if (cause instanceof CompletionException completion && completion.getCause() != null) {
                cause = completion.getCause();
            }
            if (cause instanceof Exception typed) {
                throw typed;
            }
            throw new RuntimeException(cause);
        }
    }

    private Object resolvePrimaryBaritone() throws ReflectiveOperationException {
        return baritoneGateway.resolvePrimaryBaritoneForTypedApi();
    }

    public int endPythonSessionsFromPyritoneCommand() {
        clearOperatorPauseStateFromControl();

        WebSocketBridgeServer currentServer = this.server;
        if (currentServer == null || !currentServer.isRunning()) {
            emitPyritoneNotice("Bridge is not running");
            return 0;
        }

        int disconnected = 0;
        for (WebSocketBridgeServer.ClientSession session : currentServer.sessionSnapshot()) {
            if (!session.isAuthenticated()) {
                continue;
            }
            session.close();
            disconnected += 1;
        }

        if (disconnected > 0) {
            emitPyritoneNotice("Ended " + disconnected + " Python websocket session(s)");
        } else {
            emitPyritoneNotice("No authenticated Python websocket sessions");
        }

        return disconnected;
    }

    public boolean pausePythonExecuteFromPyritoneCommand() {
        boolean changed = setOperatorPauseActive(true);

        if (changed) {
            emitPyritoneNotice("Paused Python bridge request dispatch");
        } else {
            emitPyritoneNotice("Python bridge request dispatch is already paused");
        }
        return changed;
    }

    public boolean resumePythonExecuteFromPyritoneCommand() {
        boolean changed = setOperatorPauseActive(false);

        if (changed) {
            emitPyritoneNotice("Resumed Python bridge request dispatch");
        } else {
            emitPyritoneNotice("Python bridge request dispatch was not paused");
        }
        return changed;
    }

    public boolean forceCancelActiveTaskFromPyritoneCommand() {
        Optional<TaskSnapshot> active = taskRegistry.active();
        if (active.isEmpty()) {
            emitPyritoneNotice("No active Py-Ritone task to cancel");
            return false;
        }

        TaskSnapshot snapshot = active.orElseThrow();
        String detail = "Canceled by #pyritone cancel";

        if (!baritoneGateway.isAvailable()) {
            detail = "Canceled by #pyritone cancel (Baritone unavailable)";
            emitPyritoneNotice("Hard cancel: Baritone unavailable, force-ending tracked task");
        } else {
            BaritoneGateway.Outcome outcome = baritoneGateway.cancelCurrent();
            if (outcome.ok()) {
                emitPyritoneNotice("Hard cancel accepted");
            } else {
                detail = "Canceled by #pyritone cancel (" + compactCommand(outcome.message()) + ")";
                emitPyritoneNotice("Hard cancel forced task end even though Baritone cancel returned an error");
            }
        }

        taskLifecycleResolver.clearForTask(snapshot.taskId());
        taskRegistry.transitionActive(TaskState.CANCELED, detail)
            .ifPresent(canceled -> emitTaskEvent("task.canceled", canceled, "pyritone_cancel_command"));
        return true;
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

        TaskSnapshot current = active.orElseThrow();
        taskLifecycleResolver.recordPathEvent(current.taskId(), pathEventName);
    }

    private void tickPauseState(MinecraftClient client) {
        boolean paused = client != null && client.isPaused();
        setGamePauseActive(paused);
    }

    private void tickPlayerLifecycleEvents(MinecraftClient client) {
        if (client == null || client.world == null || client.getNetworkHandler() == null) {
            if (playerLifecycleInWorld && lastKnownSelfPlayer != null) {
                emitPlayerLifecycleEvent("minecraft.player_leave", lastKnownSelfPlayer);
            }
            playerLifecycleTracker.reset();
            playerLifecycleInWorld = false;
            playerLifecycleSelfJoinEmitted = false;
            lastKnownSelfPlayer = null;
            return;
        }

        if (!playerLifecycleInWorld) {
            playerLifecycleInWorld = true;
            playerLifecycleSelfJoinEmitted = false;
        }

        Map<String, Boolean> aliveByUuid = new HashMap<>();
        String localPlayerUuid = null;
        if (client.player != null) {
            localPlayerUuid = client.player.getUuidAsString();
        }

        for (PlayerEntity player : client.world.getPlayers()) {
            if (player == null) {
                continue;
            }
            String uuid = player.getUuidAsString();
            if (uuid == null || uuid.isBlank()) {
                continue;
            }
            aliveByUuid.put(uuid, player.isAlive());
        }

        List<PlayerLifecycleTracker.PlayerSnapshot> players = new ArrayList<>();
        PlayerLifecycleTracker.PlayerSnapshot selfSnapshot = null;
        for (PlayerListEntry entry : client.getNetworkHandler().getPlayerList()) {
            if (entry == null || entry.getProfile() == null || entry.getProfile().getId() == null) {
                continue;
            }
            String uuid = entry.getProfile().getId().toString();
            String name = entry.getProfile().getName();
            if (name == null || name.isBlank()) {
                name = "unknown";
            }
            boolean self = localPlayerUuid != null && localPlayerUuid.equals(uuid);
            Boolean aliveValue = aliveByUuid.get(uuid);
            boolean aliveKnown = aliveValue != null;
            boolean alive = aliveKnown && aliveValue;
            PlayerLifecycleTracker.PlayerSnapshot snapshot =
                new PlayerLifecycleTracker.PlayerSnapshot(uuid, name, alive, self, aliveKnown);
            players.add(snapshot);
            if (self) {
                selfSnapshot = snapshot;
            }
        }

        List<PlayerLifecycleTracker.PlayerEvent> events = playerLifecycleTracker.update(players);
        for (PlayerLifecycleTracker.PlayerEvent event : events) {
            String eventName = switch (event.type()) {
                case JOIN -> "minecraft.player_join";
                case LEAVE -> "minecraft.player_leave";
                case DEATH -> "minecraft.player_death";
                case RESPAWN -> "minecraft.player_respawn";
            };
            emitPlayerLifecycleEvent(eventName, event.player());
            if (event.type() == PlayerLifecycleTracker.PlayerEventType.JOIN
                && event.player() != null
                && event.player().self()) {
                playerLifecycleSelfJoinEmitted = true;
            }
        }

        if (!playerLifecycleSelfJoinEmitted && selfSnapshot != null) {
            emitPlayerLifecycleEvent("minecraft.player_join", selfSnapshot);
            playerLifecycleSelfJoinEmitted = true;
        }
        lastKnownSelfPlayer = selfSnapshot;
    }

    private void tickTaskLifecycle() {
        Optional<TaskSnapshot> active = taskRegistry.active();
        if (active.isEmpty()) {
            taskLifecycleResolver.clear();
            return;
        }

        TaskSnapshot current = active.orElseThrow();
        Optional<TaskLifecycleResolver.LifecycleUpdate> lifecycleUpdate = taskLifecycleResolver.evaluate(
            current.taskId(),
            baritoneGateway.activitySnapshot()
        );

        if (lifecycleUpdate.isEmpty()) {
            return;
        }

        TaskLifecycleResolver.LifecycleUpdate update = lifecycleUpdate.orElseThrow();
        switch (update.kind()) {
            case PAUSED -> handlePausedUpdate(current, update.pauseStatus());
            case RESUMED -> handleResumedUpdate(current, update.pauseStatus());
            case TERMINAL -> {
                TaskLifecycleResolver.TerminalDecision decision = update.terminalDecision();
                if (decision == null) {
                    return;
                }
                taskRegistry.transitionActive(decision.state(), decision.detail())
                    .ifPresent(snapshot -> emitTaskEvent(decision.eventName(), snapshot, decision.stage()));
            }
        }
    }

    private void tickStatusStreams() {
        WebSocketBridgeServer currentServer = this.server;
        if (currentServer == null || !currentServer.isRunning()) {
            statusSubscriptionRegistry.clear();
            typedApiService.clear();
            return;
        }

        Set<WebSocketBridgeServer.ClientSession> sessions = currentServer.sessionSnapshot();
        if (sessions.isEmpty()) {
            statusSubscriptionRegistry.clear();
            typedApiService.clear();
            return;
        }

        Set<String> activeSessionIds = sessions.stream().map(WebSocketBridgeServer.ClientSession::sessionId).collect(java.util.stream.Collectors.toSet());
        statusSubscriptionRegistry.retainSessions(activeSessionIds);
        typedApiService.retainSessions(activeSessionIds);

        long nowMs = System.currentTimeMillis();
        for (WebSocketBridgeServer.ClientSession session : sessions) {
            if (!session.isAuthenticated()) {
                continue;
            }

            JsonObject status = buildStatusPayload(session);
            Optional<StatusSubscriptionRegistry.Emission> emission = statusSubscriptionRegistry.evaluate(
                session.sessionId(),
                statusDigest(status),
                nowMs,
                BridgeConfig.STATUS_HEARTBEAT_INTERVAL_MS
            );
            if (emission.isEmpty()) {
                continue;
            }

            publishStatusEvent(currentServer, session, status, emission.orElseThrow());
        }
    }

    private void publishStatusEvent(
        WebSocketBridgeServer currentServer,
        WebSocketBridgeServer.ClientSession session,
        JsonObject status,
        StatusSubscriptionRegistry.Emission emission
    ) {
        JsonObject data = new JsonObject();
        data.addProperty("reason", emission.reason());
        data.addProperty("seq", emission.sequence());
        data.add("status", status);
        currentServer.publishEvent(session, ProtocolCodec.eventEnvelope("status.update", data));
    }

    private void onIncomingChatMessage(Text message, GameProfile sender) {
        MinecraftClient client = MinecraftClient.getInstance();
        JsonObject authorPayload = null;
        if (sender != null) {
            String uuid = sender.getId() != null ? sender.getId().toString() : null;
            String name = sender.getName() != null && !sender.getName().isBlank() ? sender.getName() : "unknown";
            boolean self = false;
            if (client != null && client.player != null && uuid != null && !uuid.isBlank()) {
                self = uuid.equals(client.player.getUuidAsString());
            }
            authorPayload = playerPayload(uuid, name, self);
        }
        emitChatMessageEvent(message != null ? message.getString() : "", authorPayload);
    }

    private void onIncomingSystemMessage(Text message, boolean overlay) {
        JsonObject data = new JsonObject();
        data.addProperty("message", message != null ? message.getString() : "");
        data.addProperty("overlay", overlay);
        publishEvent("minecraft.system_message", data);
    }

    private void emitChatMessageEvent(String message, JsonObject author) {
        JsonObject data = new JsonObject();
        data.addProperty("message", message == null ? "" : message);
        data.add("author", author != null ? author : JsonNull.INSTANCE);
        publishEvent("minecraft.chat_message", data);
    }

    private void emitPlayerLifecycleEvent(String eventName, PlayerLifecycleTracker.PlayerSnapshot player) {
        if (player == null) {
            return;
        }
        JsonObject data = new JsonObject();
        data.add("player", playerPayload(player.uuid(), player.name(), player.self()));
        publishEvent(eventName, data);
    }

    private static JsonObject playerPayload(String uuid, String name, boolean self) {
        JsonObject payload = new JsonObject();
        if (uuid != null && !uuid.isBlank()) {
            payload.addProperty("uuid", uuid);
        } else {
            payload.add("uuid", JsonNull.INSTANCE);
        }
        payload.addProperty("name", name == null || name.isBlank() ? "unknown" : name);
        payload.addProperty("self", self);
        return payload;
    }

    private static JsonObject currentPlayerPayload(MinecraftClient client) {
        if (client == null || client.player == null) {
            return null;
        }
        String uuid = client.player.getUuidAsString();
        String name = client.player.getName() != null ? client.player.getName().getString() : "unknown";
        return playerPayload(uuid, name, true);
    }

    private void handlePausedUpdate(TaskSnapshot current, TaskLifecycleResolver.PauseStatus pauseStatus) {
        String detail = pauseStatusDetail(pauseStatus);
        Optional<TaskSnapshot> updated = taskRegistry.updateActiveDetail(detail);
        TaskSnapshot snapshot = updated.orElse(current);
        emitPauseEvent("task.paused", snapshot, pauseStatus);
    }

    private void handleResumedUpdate(TaskSnapshot current, TaskLifecycleResolver.PauseStatus pauseStatus) {
        Optional<TaskSnapshot> updated = taskRegistry.updateActiveDetail("Resumed after pause");
        TaskSnapshot snapshot = updated.orElse(current);
        emitPauseEvent("task.resumed", snapshot, pauseStatus);
    }

    private void emitTaskEvent(String eventName, TaskSnapshot taskSnapshot, String stage) {
        JsonObject data = taskSnapshot.toJson();
        if (stage != null) {
            data.addProperty("stage", stage);
        }
        publishEvent(eventName, data);
    }

    private void emitPauseEvent(String eventName, TaskSnapshot taskSnapshot, TaskLifecycleResolver.PauseStatus pauseStatus) {
        JsonObject data = taskSnapshot.toJson();
        data.addProperty("stage", eventName);
        data.add("pause", pauseStatusToJson(pauseStatus));
        publishEvent(eventName, data);
    }

    private static JsonObject pauseStatusToJson(TaskLifecycleResolver.PauseStatus pauseStatus) {
        JsonObject object = new JsonObject();
        if (pauseStatus == null) {
            object.addProperty("reason_code", "PAUSED");
            object.addProperty("source_process", "");
            object.addProperty("command_type", "");
            return object;
        }

        object.addProperty("reason_code", safeString(pauseStatus.reasonCode()));
        object.addProperty("source_process", safeString(pauseStatus.sourceProcess()));
        object.addProperty("command_type", safeString(pauseStatus.commandType()));
        return object;
    }

    private static String pauseStatusDetail(TaskLifecycleResolver.PauseStatus pauseStatus) {
        if (pauseStatus == null) {
            return "Paused";
        }

        return "Paused (" + safeString(pauseStatus.reasonCode()) + ")";
    }

    private static String safeString(String value) {
        return value == null ? "" : value;
    }

    private void publishEvent(String eventName, JsonObject data) {
        WebSocketBridgeServer currentServer = this.server;
        if (currentServer == null || !currentServer.isRunning()) {
            return;
        }
        currentServer.publishEvent(ProtocolCodec.eventEnvelope(eventName, data));
    }

    private boolean applyPyritoneChatControl(String message) {
        String subcommand = pyritoneSubcommand(message);
        if (subcommand == null) {
            return false;
        }

        return switch (subcommand) {
            case "end" -> {
                endPythonSessionsFromPyritoneCommand();
                yield true;
            }
            case "pause" -> {
                pausePythonExecuteFromPyritoneCommand();
                yield true;
            }
            case "resume" -> {
                resumePythonExecuteFromPyritoneCommand();
                yield true;
            }
            default -> false;
        };
    }

    private static String pyritoneSubcommand(String message) {
        if (message == null) {
            return null;
        }
        String trimmed = message.trim();
        if (trimmed.isBlank()) {
            return null;
        }
        String normalized = trimmed.toLowerCase(Locale.ROOT);
        if (!normalized.startsWith("#pyritone")) {
            return null;
        }
        String rest = normalized.substring("#pyritone".length()).trim();
        if (rest.isBlank()) {
            return "";
        }
        int split = rest.indexOf(' ');
        return split >= 0 ? rest.substring(0, split) : rest;
    }

    private boolean isPauseGatedMethod(String method) {
        return PAUSE_GATED_METHODS.contains(method);
    }

    private JsonObject pauseGateError(String id) {
        PauseStateSnapshot snapshot = currentPauseStateSnapshot();
        if (!snapshot.paused()) {
            return null;
        }

        JsonObject payload = pauseStateToJson(snapshot);
        String message = pauseReasonMessage(snapshot);
        return ProtocolCodec.errorResponse(id, "PAUSED", message, payload);
    }

    private static String pauseReasonMessage(PauseStateSnapshot snapshot) {
        if (snapshot.operatorPaused() && snapshot.gamePaused()) {
            return "Bridge request handling is paused (operator + game pause active)";
        }
        if (snapshot.operatorPaused()) {
            return "Bridge request handling is paused by #pyritone pause";
        }
        if (snapshot.gamePaused()) {
            return "Bridge request handling is paused because Minecraft is paused";
        }
        return "Bridge request handling is paused";
    }

    private boolean setOperatorPauseActive(boolean active) {
        PauseStateSnapshot snapshot = null;
        synchronized (pauseStateLock) {
            if (operatorPauseActive == active) {
                return false;
            }
            operatorPauseActive = active;
            snapshot = updatePauseStateLocked();
        }
        publishPauseStateEvent(snapshot);
        return true;
    }

    private boolean setGamePauseActive(boolean active) {
        PauseStateSnapshot snapshot = null;
        synchronized (pauseStateLock) {
            if (gamePauseActive == active) {
                return false;
            }
            gamePauseActive = active;
            snapshot = updatePauseStateLocked();
        }
        publishPauseStateEvent(snapshot);
        return true;
    }

    private void clearOperatorPauseStateFromControl() {
        PauseStateSnapshot snapshot = null;
        synchronized (pauseStateLock) {
            if (!operatorPauseActive) {
                return;
            }
            operatorPauseActive = false;
            snapshot = updatePauseStateLocked();
        }
        publishPauseStateEvent(snapshot);
    }

    private void clearPauseStateForShutdown() {
        PauseStateSnapshot snapshot = null;
        synchronized (pauseStateLock) {
            if (!operatorPauseActive && !gamePauseActive && !effectivePauseActive) {
                return;
            }
            operatorPauseActive = false;
            gamePauseActive = false;
            snapshot = updatePauseStateLocked();
        }
        publishPauseStateEvent(snapshot);
    }

    private PauseStateSnapshot currentPauseStateSnapshot() {
        synchronized (pauseStateLock) {
            return new PauseStateSnapshot(
                effectivePauseActive,
                operatorPauseActive,
                gamePauseActive,
                pauseReason(operatorPauseActive, gamePauseActive),
                pauseStateSeq
            );
        }
    }

    private PauseStateSnapshot updatePauseStateLocked() {
        effectivePauseActive = operatorPauseActive || gamePauseActive;
        pauseStateSeq += 1L;
        return new PauseStateSnapshot(
            effectivePauseActive,
            operatorPauseActive,
            gamePauseActive,
            pauseReason(operatorPauseActive, gamePauseActive),
            pauseStateSeq
        );
    }

    private void publishPauseStateEvent(PauseStateSnapshot snapshot) {
        if (snapshot == null) {
            return;
        }
        publishEvent("bridge.pause_state", pauseStateToJson(snapshot));
    }

    private void emitPauseStateEventToSession(WebSocketBridgeServer.ClientSession session, PauseStateSnapshot snapshot) {
        WebSocketBridgeServer currentServer = this.server;
        if (currentServer == null || !currentServer.isRunning() || session == null || snapshot == null) {
            return;
        }
        JsonObject envelope = ProtocolCodec.eventEnvelope("bridge.pause_state", pauseStateToJson(snapshot));
        currentServer.publishEvent(session, envelope);
    }

    private static JsonObject pauseStateToJson(PauseStateSnapshot snapshot) {
        JsonObject payload = new JsonObject();
        payload.addProperty("paused", snapshot.paused());
        payload.addProperty("operator_paused", snapshot.operatorPaused());
        payload.addProperty("game_paused", snapshot.gamePaused());
        payload.addProperty("reason", snapshot.reason());
        payload.addProperty("seq", snapshot.seq());
        return payload;
    }

    private static String pauseReason(boolean operatorPaused, boolean gamePaused) {
        if (operatorPaused && gamePaused) {
            return "operator_and_game_pause";
        }
        if (operatorPaused) {
            return "operator_pause";
        }
        if (gamePaused) {
            return "game_pause";
        }
        return "resumed";
    }

    private boolean hasAnotherAuthenticatedSession(WebSocketBridgeServer.ClientSession session) {
        WebSocketBridgeServer currentServer = this.server;
        if (currentServer == null || !currentServer.isRunning()) {
            return false;
        }

        for (WebSocketBridgeServer.ClientSession candidate : currentServer.sessionSnapshot()) {
            if (candidate == session) {
                continue;
            }
            if (candidate.isAuthenticated()) {
                return true;
            }
        }
        return false;
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

    private record PauseStateSnapshot(
        boolean paused,
        boolean operatorPaused,
        boolean gamePaused,
        String reason,
        long seq
    ) {
    }
}






