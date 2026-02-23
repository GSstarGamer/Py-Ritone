package com.pyritone.bridge.runtime;

import net.minecraft.client.MinecraftClient;
import org.slf4j.Logger;

import java.lang.reflect.Field;
import java.lang.reflect.InvocationHandler;
import java.lang.reflect.Method;
import java.lang.reflect.Proxy;
import java.util.List;
import java.util.Locale;
import java.util.Optional;
import java.util.concurrent.Callable;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.CompletionException;
import java.util.concurrent.TimeUnit;
import java.util.function.Consumer;
import java.util.stream.Stream;

public final class BaritoneGateway {
    private final Logger logger;
    private final Consumer<String> pathEventConsumer;

    private volatile Object registeredEventBus;
    private volatile Object registeredListener;
    private volatile Object registeredCommandManager;
    private volatile Object registeredPyritoneCommand;

    public BaritoneGateway(Logger logger, Consumer<String> pathEventConsumer) {
        this.logger = logger;
        this.pathEventConsumer = pathEventConsumer;
    }

    public boolean isAvailable() {
        try {
            Class.forName("baritone.api.BaritoneAPI", false, getClass().getClassLoader());
            return true;
        } catch (ClassNotFoundException exception) {
            return false;
        }
    }

    public boolean isInWorld() {
        return onClientThread(() -> {
            MinecraftClient client = MinecraftClient.getInstance();
            return client != null && client.player != null && client.world != null;
        }, false);
    }

    public Outcome executeRaw(String command) {
        return onClientThread(() -> executeRawOnClientThread(command), new Outcome(false, "Failed to execute on client thread"));
    }

    public Outcome cancelCurrent() {
        return onClientThread(this::cancelOnClientThread, new Outcome(false, "Failed to cancel on client thread"));
    }

    public void tickRegisterPathListener() {
        onClientThread(() -> {
            ensurePathListenerOnClientThread();
            return true;
        }, false);
    }

    public void tickRegisterPyritoneHashCommand(Runnable cancelAction) {
        onClientThread(() -> {
            ensurePyritoneHashCommandOnClientThread(cancelAction);
            return true;
        }, false);
    }

    public void tickApplyPyritoneChatBranding() {
        // Intentionally no-op: native Baritone prefix should remain unchanged.
        // Py-Ritone branding is applied only to bridge-originated notices.
    }

    public ActivitySnapshot activitySnapshot() {
        return onClientThread(this::activitySnapshotOnClientThread, ActivitySnapshot.idle());
    }

    public Object resolvePrimaryBaritoneForTypedApi() throws ReflectiveOperationException {
        return getPrimaryBaritone();
    }

    private Outcome executeRawOnClientThread(String command) {
        if (!isClientReady()) {
            return new Outcome(false, "Client is not in a world");
        }

        try {
            Object baritone = getPrimaryBaritone();
            Object commandManager = invokeNoArgs(baritone, "getCommandManager");
            Object result = invoke(commandManager, "execute", new Class<?>[]{String.class}, new Object[]{command});
            boolean ok = result instanceof Boolean value && value;
            return ok
                ? new Outcome(true, "Command accepted")
                : new Outcome(false, "Baritone command manager rejected the command");
        } catch (ReflectiveOperationException exception) {
            logger.debug("Baritone execute call failed", exception);
            return new Outcome(false, exception.getMessage());
        }
    }

    private Outcome cancelOnClientThread() {
        if (!isClientReady()) {
            return new Outcome(false, "Client is not in a world");
        }

        try {
            Object baritone = getPrimaryBaritone();
            Object pathingBehavior = invokeNoArgs(baritone, "getPathingBehavior");
            Object cancelResult = invokeNoArgs(pathingBehavior, "cancelEverything");
            if (cancelResult instanceof Boolean canceled && canceled) {
                return new Outcome(true, "Canceled by pathing behavior");
            }

            Object commandManager = invokeNoArgs(baritone, "getCommandManager");
            Object stopResult = invoke(commandManager, "execute", new Class<?>[]{String.class}, new Object[]{"stop"});
            boolean stopped = stopResult instanceof Boolean value && value;
            return stopped ? new Outcome(true, "Canceled with stop command") : new Outcome(false, "Failed to cancel active task");
        } catch (ReflectiveOperationException exception) {
            logger.debug("Baritone cancel call failed", exception);
            return new Outcome(false, exception.getMessage());
        }
    }

    private void ensurePathListenerOnClientThread() {
        if (!isClientReady()) {
            return;
        }

        try {
            Object baritone = getPrimaryBaritone();
            Object eventBus = invokeNoArgs(baritone, "getGameEventHandler");
            if (eventBus == registeredEventBus) {
                return;
            }

            ClassLoader loader = getClass().getClassLoader();
            Class<?> gameEventListener = Class.forName("baritone.api.event.listener.IGameEventListener", true, loader);
            Class<?> abstractListener = Class.forName("baritone.api.event.listener.AbstractGameEventListener", true, loader);

            InvocationHandler handler = this::handleEventListenerCall;
            Object listener = Proxy.newProxyInstance(loader, new Class<?>[]{abstractListener}, handler);

            invoke(eventBus, "registerEventListener", new Class<?>[]{gameEventListener}, new Object[]{listener});

            registeredEventBus = eventBus;
            registeredListener = listener;
            logger.info("Registered Baritone path event listener");
        } catch (ReflectiveOperationException exception) {
            logger.debug("Unable to register Baritone path listener", exception);
        }
    }

    private void ensurePyritoneHashCommandOnClientThread(Runnable cancelAction) {
        if (cancelAction == null) {
            return;
        }

        try {
            Object baritone = getPrimaryBaritone();
            Object commandManager = invokeNoArgs(baritone, "getCommandManager");
            if (commandManager == null) {
                return;
            }

            if (commandManager == registeredCommandManager && registeredPyritoneCommand != null) {
                return;
            }

            Object existing = invoke(commandManager, "getCommand", new Class<?>[]{String.class}, new Object[]{"pyritone"});
            if (existing != null) {
                registeredCommandManager = commandManager;
                registeredPyritoneCommand = existing;
                return;
            }

            Object registry = invokeNoArgs(commandManager, "getRegistry");
            if (registry == null) {
                return;
            }

            ClassLoader loader = getClass().getClassLoader();
            Class<?> iCommand = Class.forName("baritone.api.command.ICommand", true, loader);
            InvocationHandler handler = (proxy, method, args) -> handlePyritoneCommandCall(proxy, method, args, cancelAction);
            Object commandProxy = Proxy.newProxyInstance(loader, new Class<?>[]{iCommand}, handler);

            Object registered = invoke(registry, "register", new Class<?>[]{Object.class}, new Object[]{commandProxy});
            boolean accepted = !(registered instanceof Boolean value) || value;
            if (!accepted) {
                return;
            }

            registeredCommandManager = commandManager;
            registeredPyritoneCommand = commandProxy;
            logger.info("Registered Baritone hash command: #pyritone");
        } catch (ReflectiveOperationException exception) {
            logger.debug("Unable to register #pyritone Baritone command", exception);
        }
    }

    private ActivitySnapshot activitySnapshotOnClientThread() {
        if (!isClientReady()) {
            return ActivitySnapshot.idle();
        }

        try {
            Object baritone = getPrimaryBaritone();
            Object pathingBehavior = tryInvokeNoArgs(baritone, "getPathingBehavior");
            ControlSnapshot controlSnapshot = detectControlSnapshot(baritone);
            BuilderSnapshot builderSnapshot = detectBuilderSnapshot(baritone);

            boolean isPathing = tryInvokeBooleanNoArgs(pathingBehavior, "isPathing");
            boolean hasPath = detectHasPath(pathingBehavior);
            boolean calcInProgress = detectCalcInProgress(pathingBehavior);
            boolean processInControlActive = controlSnapshot.processInControlActive();

            return new ActivitySnapshot(
                isPathing,
                hasPath,
                calcInProgress,
                processInControlActive,
                controlSnapshot.commandType(),
                controlSnapshot.sourceProcess(),
                builderSnapshot.active(),
                builderSnapshot.paused()
            );
        } catch (ReflectiveOperationException exception) {
            logger.debug("Unable to gather Baritone runtime snapshot", exception);
            return ActivitySnapshot.idle();
        }
    }

    private static boolean detectHasPath(Object pathingBehavior) {
        if (pathingBehavior == null) {
            return false;
        }
        if (tryInvokeBooleanNoArgs(pathingBehavior, "hasPath")) {
            return true;
        }
        if (tryInvokeNoArgs(pathingBehavior, "getCurrent") != null) {
            return true;
        }
        return tryInvokeNoArgs(pathingBehavior, "getPath") != null;
    }

    private static boolean detectCalcInProgress(Object pathingBehavior) {
        if (pathingBehavior == null) {
            return false;
        }
        if (tryInvokeBooleanNoArgs(pathingBehavior, "isPathCalcInProgress")) {
            return true;
        }
        if (tryInvokeBooleanNoArgs(pathingBehavior, "isCalcInProgress")) {
            return true;
        }
        if (tryInvokeBooleanNoArgs(pathingBehavior, "isCalculating")) {
            return true;
        }
        if (tryInvokeBooleanNoArgs(pathingBehavior, "isPlanning")) {
            return true;
        }
        return false;
    }

    private static ControlSnapshot detectControlSnapshot(Object baritone) {
        if (baritone == null) {
            return ControlSnapshot.empty();
        }

        Object pathingControlManager = tryInvokeNoArgs(baritone, "getPathingControlManager");
        if (pathingControlManager == null) {
            return ControlSnapshot.empty();
        }

        // Prefer current in-control signals; mostRecentInControl can stay latched after work ends.
        Object inControl = unwrapOptional(tryInvokeNoArgs(pathingControlManager, "inControlThisTick"));
        if (inControl == null) {
            inControl = unwrapOptional(tryInvokeNoArgs(pathingControlManager, "getInControl"));
        }
        if (inControl == null) {
            inControl = unwrapOptional(tryInvokeNoArgs(pathingControlManager, "mostRecentInControl"));
        }

        boolean processInControlActive = detectProcessActive(inControl);
        String sourceProcess = detectProcessDisplayName(inControl);

        Object command = unwrapOptional(tryInvokeNoArgs(pathingControlManager, "inControlThisTickCommand"));
        if (command == null) {
            command = unwrapOptional(tryInvokeNoArgs(pathingControlManager, "inControlCommand"));
        }
        if (command == null) {
            command = unwrapOptional(tryInvokeNoArgs(pathingControlManager, "getCurrentCommand"));
        }
        if (command == null) {
            command = unwrapOptional(tryInvokeNoArgs(pathingControlManager, "mostRecentCommand"));
        }
        String commandType = detectPathingCommandType(command);

        return new ControlSnapshot(processInControlActive, sourceProcess, commandType);
    }

    private static BuilderSnapshot detectBuilderSnapshot(Object baritone) {
        if (baritone == null) {
            return BuilderSnapshot.inactive();
        }

        Object builderProcess = tryInvokeNoArgs(baritone, "getBuilderProcess");
        if (builderProcess == null) {
            return BuilderSnapshot.inactive();
        }

        boolean paused = tryInvokeBooleanNoArgs(builderProcess, "isPaused");
        boolean active = tryInvokeBooleanNoArgs(builderProcess, "isActive")
            || tryInvokeBooleanNoArgs(builderProcess, "isBuilding")
            || paused;

        return new BuilderSnapshot(active, paused);
    }

    private static boolean detectProcessActive(Object inControl) {
        if (inControl == null) {
            return false;
        }
        if (inControl instanceof Boolean value) {
            return value;
        }
        if (tryInvokeBooleanNoArgs(inControl, "isActive")) {
            return true;
        }
        if (tryInvokeBooleanNoArgs(inControl, "isPathing")) {
            return true;
        }
        Object pausedValue = tryInvokeNoArgs(inControl, "isPaused");
        if (pausedValue instanceof Boolean paused) {
            return !paused;
        }
        return false;
    }

    private static String detectProcessDisplayName(Object inControl) {
        if (inControl == null) {
            return null;
        }

        Object displayName = tryInvokeNoArgs(inControl, "displayName");
        if (displayName instanceof String value && !value.isBlank()) {
            return value;
        }

        Object displayName0 = tryInvokeNoArgs(inControl, "displayName0");
        if (displayName0 instanceof String value && !value.isBlank()) {
            return value;
        }
        return null;
    }

    private static String detectPathingCommandType(Object pathingCommand) {
        if (pathingCommand == null) {
            return null;
        }

        Object commandType = tryReadField(pathingCommand, "commandType");
        if (commandType == null) {
            commandType = tryInvokeNoArgs(pathingCommand, "getCommandType");
        }
        if (commandType instanceof Enum<?> enumValue) {
            return enumValue.name();
        }
        if (commandType instanceof String value && !value.isBlank()) {
            return value;
        }
        return commandType != null ? String.valueOf(commandType) : null;
    }

    private Object handleEventListenerCall(Object proxy, Method method, Object[] args) {
        String methodName = method.getName();
        if ("onPathEvent".equals(methodName) && args != null && args.length == 1 && args[0] != null) {
            Object event = args[0];
            if (event instanceof Enum<?> enumEvent) {
                pathEventConsumer.accept(enumEvent.name());
            } else {
                pathEventConsumer.accept(String.valueOf(event));
            }
        }

        if (method.getDeclaringClass() == Object.class) {
            return switch (methodName) {
                case "toString" -> "PyritoneBaritoneListenerProxy";
                case "hashCode" -> System.identityHashCode(proxy);
                case "equals" -> proxy == (args != null && args.length > 0 ? args[0] : null);
                default -> null;
            };
        }

        return defaultValue(method.getReturnType());
    }

    private Object handlePyritoneCommandCall(Object proxy, Method method, Object[] args, Runnable cancelAction) {
        String methodName = method.getName();
        switch (methodName) {
            case "execute" -> {
                String subcommand = extractFirstArg(args);
                if ("cancel".equals(subcommand)) {
                    cancelAction.run();
                }
                return null;
            }
            case "tabComplete" -> {
                String prefix = extractFirstArg(args);
                if (prefix.isBlank()) {
                    return Stream.of("cancel");
                }
                return Stream.of("cancel").filter(option -> option.startsWith(prefix));
            }
            case "getShortDesc" -> {
                return "Py-Ritone controls";
            }
            case "getLongDesc" -> {
                return List.of(
                    "Py-Ritone command bridge",
                    "Usage: #pyritone cancel"
                );
            }
            case "getNames" -> {
                return List.of("pyritone");
            }
            case "hiddenFromHelp" -> {
                return false;
            }
            default -> {
                if (method.getDeclaringClass() == Object.class) {
                    return switch (methodName) {
                        case "toString" -> "PyritoneCommandProxy";
                        case "hashCode" -> System.identityHashCode(proxy);
                        case "equals" -> proxy == (args != null && args.length > 0 ? args[0] : null);
                        default -> null;
                    };
                }
                return defaultValue(method.getReturnType());
            }
        }
    }

    private static String extractFirstArg(Object[] args) {
        if (args == null || args.length < 2 || args[1] == null) {
            return "";
        }

        Object argConsumer = args[1];
        Object rawRest = tryInvokeNoArgs(argConsumer, "rawRest");
        if (rawRest instanceof String text && !text.isBlank()) {
            return firstToken(text);
        }

        Object hasAny = tryInvokeNoArgs(argConsumer, "hasAny");
        if (hasAny instanceof Boolean value && value) {
            Object peek = tryInvokeNoArgs(argConsumer, "peekString");
            if (peek instanceof String text && !text.isBlank()) {
                return firstToken(text);
            }
        }
        return "";
    }

    private static String firstToken(String text) {
        String trimmed = text.trim().toLowerCase(Locale.ROOT);
        if (trimmed.isBlank()) {
            return "";
        }
        int spaceIndex = trimmed.indexOf(' ');
        if (spaceIndex < 0) {
            return trimmed;
        }
        return trimmed.substring(0, spaceIndex);
    }

    private static Object defaultValue(Class<?> returnType) {
        if (!returnType.isPrimitive()) {
            return null;
        }
        if (returnType == boolean.class) {
            return false;
        }
        if (returnType == byte.class) {
            return (byte) 0;
        }
        if (returnType == short.class) {
            return (short) 0;
        }
        if (returnType == int.class) {
            return 0;
        }
        if (returnType == long.class) {
            return 0L;
        }
        if (returnType == float.class) {
            return 0F;
        }
        if (returnType == double.class) {
            return 0D;
        }
        if (returnType == char.class) {
            return '\0';
        }
        return null;
    }

    private Object getPrimaryBaritone() throws ReflectiveOperationException {
        Class<?> apiClass = Class.forName("baritone.api.BaritoneAPI", true, getClass().getClassLoader());
        Object provider = apiClass.getMethod("getProvider").invoke(null);
        return provider.getClass().getMethod("getPrimaryBaritone").invoke(provider);
    }

    private static Object invokeNoArgs(Object target, String methodName) throws ReflectiveOperationException {
        return target.getClass().getMethod(methodName).invoke(target);
    }

    private static Object tryInvokeNoArgs(Object target, String methodName) {
        if (target == null) {
            return null;
        }
        try {
            return invokeNoArgs(target, methodName);
        } catch (ReflectiveOperationException exception) {
            return null;
        }
    }

    private static boolean tryInvokeBooleanNoArgs(Object target, String methodName) {
        Object value = tryInvokeNoArgs(target, methodName);
        return value instanceof Boolean bool && bool;
    }

    private static Object tryReadField(Object target, String fieldName) {
        if (target == null) {
            return null;
        }
        try {
            Field field = target.getClass().getField(fieldName);
            return field.get(target);
        } catch (ReflectiveOperationException exception) {
            return null;
        }
    }

    private static Object unwrapOptional(Object value) {
        if (value instanceof Optional<?> optional) {
            return optional.orElse(null);
        }
        return value;
    }

    private static Object invoke(Object target, String methodName, Class<?>[] parameterTypes, Object[] values) throws ReflectiveOperationException {
        return target.getClass().getMethod(methodName, parameterTypes).invoke(target, values);
    }

    private boolean isClientReady() {
        MinecraftClient client = MinecraftClient.getInstance();
        return client != null && client.player != null && client.world != null;
    }

    private <T> T onClientThread(Callable<T> callable, T fallback) {
        MinecraftClient client = MinecraftClient.getInstance();
        if (client == null) {
            return fallback;
        }

        if (client.isOnThread()) {
            try {
                return callable.call();
            } catch (Exception exception) {
                logger.debug("Client thread call failed", exception);
                return fallback;
            }
        }

        try {
            CompletableFuture<T> future = client.submit(() -> {
                try {
                    return callable.call();
                } catch (Exception exception) {
                    throw new CompletionException(exception);
                }
            });
            return future.get(5, TimeUnit.SECONDS);
        } catch (Exception exception) {
            logger.debug("Client thread call failed", exception);
            return fallback;
        }
    }

    public record Outcome(boolean ok, String message) {
    }

    public record ActivitySnapshot(
        boolean isPathing,
        boolean hasPath,
        boolean calcInProgress,
        boolean processInControlActive,
        String commandType,
        String sourceProcess,
        boolean builderActive,
        boolean builderPaused
    ) {
        public boolean isBusy() {
            // `hasPath` can remain true briefly (or stale) even after real work ends.
            // Busy should track active motion/calc/build work only.
            return isPathing || calcInProgress || builderActive;
        }

        public boolean isPaused() {
            return builderPaused
                || (processInControlActive
                    && ("REQUEST_PAUSE".equals(commandType) || "SET_GOAL_AND_PAUSE".equals(commandType)));
        }

        public String pauseReasonCode() {
            if (!isPaused()) {
                return null;
            }
            if (builderPaused) {
                return "BUILDER_PAUSED";
            }
            if ("SET_GOAL_AND_PAUSE".equals(commandType)) {
                return "SET_GOAL_AND_PAUSE";
            }
            if ("REQUEST_PAUSE".equals(commandType)) {
                return "REQUEST_PAUSE";
            }
            return "PAUSED";
        }

        public static ActivitySnapshot idle() {
            return new ActivitySnapshot(
                false,
                false,
                false,
                false,
                null,
                null,
                false,
                false
            );
        }
    }

    private record ControlSnapshot(
        boolean processInControlActive,
        String sourceProcess,
        String commandType
    ) {
        private static ControlSnapshot empty() {
            return new ControlSnapshot(false, null, null);
        }
    }

    private record BuilderSnapshot(
        boolean active,
        boolean paused
    ) {
        private static BuilderSnapshot inactive() {
            return new BuilderSnapshot(false, false);
        }
    }

}
