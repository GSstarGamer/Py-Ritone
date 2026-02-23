package com.pyritone.bridge.runtime;

import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;

import java.lang.reflect.Constructor;
import java.lang.reflect.Executable;
import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Method;
import java.lang.reflect.Modifier;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Comparator;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.concurrent.ConcurrentHashMap;
import java.util.stream.Collectors;

public final class TypedApiService {
    public static final String REF_KEY = "$pyritone_ref";
    private static final int METADATA_VERSION = 1;

    private final Map<String, RootBinding> roots = new ConcurrentHashMap<>();
    private final RemoteReferenceTable references = new RemoteReferenceTable();
    private final TypedApiValueCodec codec;

    public TypedApiService(ClassLoader classLoader) {
        this.codec = new TypedApiValueCodec(classLoader, references);
    }

    public void registerRoot(String name, String javaType, RootResolver resolver) {
        if (name == null || name.isBlank()) {
            throw new IllegalArgumentException("name is required");
        }
        if (javaType == null || javaType.isBlank()) {
            throw new IllegalArgumentException("javaType is required");
        }
        if (resolver == null) {
            throw new IllegalArgumentException("resolver is required");
        }
        roots.put(name, new RootBinding(name, javaType, resolver));
    }

    public void clear() {
        references.clear();
    }

    public void retainSessions(Set<String> activeSessionIds) {
        references.retainSessions(activeSessionIds);
    }

    public JsonObject metadata(String sessionId, JsonObject params) throws TypedApiException {
        JsonObject result = new JsonObject();
        result.addProperty("metadata_version", METADATA_VERSION);

        JsonObject targetPayload = readOptionalObject(params, "target");
        if (targetPayload == null) {
            JsonArray rootsArray = new JsonArray();
            roots.keySet().stream().sorted().forEach(rootName -> {
                RootBinding binding = roots.get(rootName);
                JsonObject root = new JsonObject();
                root.addProperty("name", binding.name());
                root.addProperty("java_type", binding.javaType());
                rootsArray.add(root);
            });
            result.add("roots", rootsArray);
            return result;
        }

        ResolvedTarget target = resolveTarget(sessionId, targetPayload, false);
        result.add("target", describeTarget(target));
        result.add("type", describeType(target.targetClass()));
        return result;
    }

    public JsonObject construct(String sessionId, JsonObject params) throws TypedApiException {
        String typeName = requireString(params, "type", "Missing type");
        Class<?> targetType = codec.resolveTypeByName(typeName);
        JsonArray args = readArgs(params);
        String[] parameterTypeNames = readOptionalTypeNames(params);

        ConstructSelection selection = selectConstructor(targetType, args, parameterTypeNames, sessionId);
        Object instance;
        try {
            instance = selection.constructor().newInstance(selection.arguments());
        } catch (InvocationTargetException exception) {
            Throwable cause = exception.getTargetException() == null ? exception : exception.getTargetException();
            throw invocationError("construct", typeName, cause);
        } catch (ReflectiveOperationException exception) {
            throw invocationError("construct", typeName, exception);
        }

        JsonObject result = new JsonObject();
        result.add("value", codec.encodeValue(sessionId, instance));
        result.addProperty("java_type", instance == null ? targetType.getName() : instance.getClass().getName());
        return result;
    }

    public JsonObject invoke(String sessionId, JsonObject params) throws TypedApiException {
        JsonObject targetPayload = requireObject(params, "target", "Missing target");
        String methodName = requireString(params, "method", "Missing method");
        JsonArray args = readArgs(params);
        String[] parameterTypeNames = readOptionalTypeNames(params);

        ResolvedTarget target = resolveTarget(sessionId, targetPayload, true);
        MethodSelection selection = selectMethod(target, methodName, args, parameterTypeNames, sessionId);

        Object value;
        try {
            value = selection.method().invoke(selection.invokeTarget(), selection.arguments());
        } catch (InvocationTargetException exception) {
            Throwable cause = exception.getTargetException() == null ? exception : exception.getTargetException();
            throw invocationError("invoke", methodName, cause);
        } catch (ReflectiveOperationException exception) {
            throw invocationError("invoke", methodName, exception);
        }

        JsonObject result = new JsonObject();
        result.add("value", codec.encodeValue(sessionId, value));
        result.addProperty("return_type", selection.method().getReturnType().getName());
        return result;
    }

    private ResolvedTarget resolveTarget(String sessionId, JsonObject targetPayload, boolean requireInstance) throws TypedApiException {
        String kind = requireString(targetPayload, "kind", "Missing target kind");
        return switch (kind) {
            case "root" -> {
                String name = requireString(targetPayload, "name", "Missing root target name");
                RootBinding binding = roots.get(name);
                if (binding == null) {
                    throw typedError("API_TARGET_NOT_FOUND", "Unknown root target: " + name, "root", name);
                }

                Class<?> declaredType = codec.resolveTypeByName(binding.javaType());
                Object instance;
                try {
                    instance = binding.resolver().resolve();
                } catch (Exception exception) {
                    JsonObject details = new JsonObject();
                    details.addProperty("root", name);
                    details.addProperty("cause", exception.toString());
                    throw new TypedApiException("API_TARGET_UNAVAILABLE", "Root target is unavailable: " + name, details);
                }

                if (requireInstance && instance == null) {
                    throw typedError("API_TARGET_UNAVAILABLE", "Root target is unavailable: " + name, "root", name);
                }

                Class<?> targetClass = instance != null ? instance.getClass() : declaredType;
                yield new ResolvedTarget("root", name, null, targetClass, instance);
            }
            case "ref" -> {
                String referenceId = requireString(targetPayload, "id", "Missing reference id");
                Object instance = references.resolve(sessionId, referenceId).orElse(null);
                if (instance == null) {
                    throw typedError("API_REFERENCE_NOT_FOUND", "Unknown remote reference: " + referenceId, "reference_id", referenceId);
                }
                yield new ResolvedTarget("ref", null, referenceId, instance.getClass(), instance);
            }
            case "type" -> {
                String typeName = requireString(targetPayload, "name", "Missing type target name");
                Class<?> type = codec.resolveTypeByName(typeName);
                yield new ResolvedTarget("type", typeName, null, type, null);
            }
            default -> throw new TypedApiException("BAD_REQUEST", "Unknown target kind: " + kind);
        };
    }

    private ConstructSelection selectConstructor(
        Class<?> type,
        JsonArray args,
        String[] parameterTypeNames,
        String sessionId
    ) throws TypedApiException {
        if (parameterTypeNames != null) {
            Class<?>[] parameterTypes = resolveParameterTypes(parameterTypeNames);
            Constructor<?> constructor;
            try {
                constructor = type.getConstructor(parameterTypes);
            } catch (NoSuchMethodException exception) {
                JsonObject details = new JsonObject();
                details.addProperty("type", type.getName());
                details.add("parameter_types", toTypeArray(parameterTypes));
                throw new TypedApiException("API_CONSTRUCTOR_NOT_FOUND", "No matching constructor for type: " + type.getName(), details);
            }

            Object[] parameters = codec.coerceArguments(sessionId, args, constructor.getParameterTypes());
            return new ConstructSelection(constructor, parameters);
        }

        List<ConstructSelection> matches = new ArrayList<>();
        List<Constructor<?>> candidates = Arrays.stream(type.getConstructors())
            .filter(constructor -> constructor.getParameterCount() == args.size())
            .toList();

        for (Constructor<?> candidate : candidates) {
            try {
                Object[] parameters = codec.coerceArguments(sessionId, args, candidate.getParameterTypes());
                matches.add(new ConstructSelection(candidate, parameters));
            } catch (TypedApiException ignored) {
                // Continue searching for a compatible constructor.
            }
        }

        if (matches.isEmpty()) {
            if (candidates.isEmpty()) {
                throw typedError(
                    "API_CONSTRUCTOR_NOT_FOUND",
                    "No constructor found for type with " + args.size() + " args: " + type.getName(),
                    "type",
                    type.getName()
                );
            }
            throw typedError(
                "API_ARGUMENT_COERCION_FAILED",
                "Arguments could not be coerced for constructor: " + type.getName(),
                "type",
                type.getName()
            );
        }

        if (matches.size() > 1) {
            JsonObject details = new JsonObject();
            details.addProperty("type", type.getName());
            JsonArray signatures = new JsonArray();
            matches.stream().map(ConstructSelection::constructor).map(this::signatureOf).distinct().forEach(signatures::add);
            details.add("candidates", signatures);
            throw new TypedApiException("API_AMBIGUOUS_CALL", "Ambiguous constructor overloads for type: " + type.getName(), details);
        }

        return matches.get(0);
    }

    private MethodSelection selectMethod(
        ResolvedTarget target,
        String methodName,
        JsonArray args,
        String[] parameterTypeNames,
        String sessionId
    ) throws TypedApiException {
        Class<?> type = target.targetClass();
        boolean staticOnly = "type".equals(target.kind());

        if (parameterTypeNames != null) {
            Class<?>[] parameterTypes = resolveParameterTypes(parameterTypeNames);
            Method method;
            try {
                method = type.getMethod(methodName, parameterTypes);
            } catch (NoSuchMethodException exception) {
                JsonObject details = new JsonObject();
                details.addProperty("method", methodName);
                details.addProperty("target_type", type.getName());
                details.add("parameter_types", toTypeArray(parameterTypes));
                throw new TypedApiException("API_METHOD_NOT_FOUND", "No matching method: " + methodName, details);
            }

            if (staticOnly && !Modifier.isStatic(method.getModifiers())) {
                throw typedError("API_METHOD_NOT_FOUND", "Type target requires static method: " + methodName, "target_type", type.getName());
            }
            if (!staticOnly && Modifier.isStatic(method.getModifiers())) {
                throw typedError("API_METHOD_NOT_FOUND", "Instance target does not allow static method invocation: " + methodName, "target_type", type.getName());
            }

            Object[] parameters = codec.coerceArguments(sessionId, args, method.getParameterTypes());
            Object invokeTarget = Modifier.isStatic(method.getModifiers()) ? null : target.targetObject();
            return new MethodSelection(method, invokeTarget, parameters);
        }

        List<MethodSelection> matches = new ArrayList<>();
        List<Method> candidates = Arrays.stream(type.getMethods())
            .filter(method -> method.getName().equals(methodName))
            .filter(method -> method.getParameterCount() == args.size())
            .filter(method -> staticOnly == Modifier.isStatic(method.getModifiers()))
            .toList();

        for (Method candidate : candidates) {
            try {
                Object[] parameters = codec.coerceArguments(sessionId, args, candidate.getParameterTypes());
                Object invokeTarget = Modifier.isStatic(candidate.getModifiers()) ? null : target.targetObject();
                matches.add(new MethodSelection(candidate, invokeTarget, parameters));
            } catch (TypedApiException ignored) {
                // Continue searching for a compatible overload.
            }
        }

        if (matches.isEmpty()) {
            if (candidates.isEmpty()) {
                JsonObject details = new JsonObject();
                details.addProperty("method", methodName);
                details.addProperty("target_type", type.getName());
                throw new TypedApiException("API_METHOD_NOT_FOUND", "No method found: " + methodName, details);
            }
            JsonObject details = new JsonObject();
            details.addProperty("method", methodName);
            details.addProperty("target_type", type.getName());
            throw new TypedApiException("API_ARGUMENT_COERCION_FAILED", "Arguments could not be coerced for method: " + methodName, details);
        }

        if (matches.size() > 1) {
            JsonObject details = new JsonObject();
            details.addProperty("method", methodName);
            details.addProperty("target_type", type.getName());
            JsonArray signatures = new JsonArray();
            matches.stream().map(MethodSelection::method).map(this::signatureOf).distinct().forEach(signatures::add);
            details.add("candidates", signatures);
            throw new TypedApiException("API_AMBIGUOUS_CALL", "Ambiguous method overloads: " + methodName, details);
        }

        return matches.get(0);
    }

    private JsonObject describeTarget(ResolvedTarget target) {
        JsonObject object = new JsonObject();
        object.addProperty("kind", target.kind());
        if (target.name() != null) {
            object.addProperty("name", target.name());
        }
        if (target.referenceId() != null) {
            object.addProperty("id", target.referenceId());
        }
        object.addProperty("java_type", target.targetClass().getName());
        return object;
    }

    private JsonObject describeType(Class<?> type) {
        JsonObject object = new JsonObject();
        object.addProperty("java_type", type.getName());
        object.addProperty("simple_name", type.getSimpleName());
        object.addProperty("is_interface", type.isInterface());
        object.addProperty("is_enum", type.isEnum());
        object.addProperty("is_array", type.isArray());
        object.addProperty("is_primitive", type.isPrimitive());
        object.add("constructors", describeConstructors(type));
        object.add("methods", describeMethods(type));
        return object;
    }

    private JsonArray describeConstructors(Class<?> type) {
        JsonArray constructors = new JsonArray();
        Arrays.stream(type.getConstructors())
            .sorted(Comparator.comparing(this::signatureOf))
            .forEach(constructor -> {
                JsonObject descriptor = new JsonObject();
                descriptor.add("parameter_types", toTypeArray(constructor.getParameterTypes()));
                constructors.add(descriptor);
            });
        return constructors;
    }

    private JsonArray describeMethods(Class<?> type) {
        JsonArray methods = new JsonArray();
        Arrays.stream(type.getMethods())
            .filter(method -> !method.isSynthetic() && !method.isBridge())
            .filter(method -> method.getDeclaringClass() != Object.class)
            .sorted(Comparator.comparing(this::signatureOf))
            .forEach(method -> {
                JsonObject descriptor = new JsonObject();
                descriptor.addProperty("name", method.getName());
                descriptor.add("parameter_types", toTypeArray(method.getParameterTypes()));
                descriptor.addProperty("return_type", method.getReturnType().getName());
                descriptor.addProperty("declaring_type", method.getDeclaringClass().getName());
                descriptor.addProperty("static", Modifier.isStatic(method.getModifiers()));
                methods.add(descriptor);
            });
        return methods;
    }

    private String signatureOf(Executable executable) {
        String parameterTypes = Arrays.stream(executable.getParameterTypes())
            .map(Class::getName)
            .collect(Collectors.joining(","));
        if (executable instanceof Constructor<?> constructor) {
            return constructor.getDeclaringClass().getName() + "(" + parameterTypes + ")";
        }
        return executable.getName() + "(" + parameterTypes + ")";
    }

    private JsonArray toTypeArray(Class<?>[] parameterTypes) {
        JsonArray array = new JsonArray();
        for (Class<?> parameterType : parameterTypes) {
            array.add(parameterType.getName());
        }
        return array;
    }

    private Class<?>[] resolveParameterTypes(String[] names) throws TypedApiException {
        Class<?>[] parameterTypes = new Class<?>[names.length];
        for (int index = 0; index < names.length; index += 1) {
            parameterTypes[index] = codec.resolveTypeByName(names[index]);
        }
        return parameterTypes;
    }

    private static TypedApiException typedError(String code, String message, String key, String value) {
        JsonObject details = new JsonObject();
        details.addProperty(key, value);
        return new TypedApiException(code, message, details);
    }

    private static JsonArray readArgs(JsonObject source) throws TypedApiException {
        if (source == null || !source.has("args")) {
            return new JsonArray();
        }
        JsonElement value = source.get("args");
        if (!value.isJsonArray()) {
            throw new TypedApiException("BAD_REQUEST", "Expected args to be an array");
        }
        return value.getAsJsonArray();
    }

    private static String[] readOptionalTypeNames(JsonObject source) throws TypedApiException {
        if (source == null || !source.has("parameter_types")) {
            return null;
        }
        JsonElement value = source.get("parameter_types");
        if (!value.isJsonArray()) {
            throw new TypedApiException("BAD_REQUEST", "Expected parameter_types to be an array");
        }

        JsonArray array = value.getAsJsonArray();
        String[] names = new String[array.size()];
        for (int index = 0; index < array.size(); index += 1) {
            JsonElement item = array.get(index);
            if (!item.isJsonPrimitive()) {
                throw new TypedApiException("BAD_REQUEST", "Expected parameter_types items to be strings");
            }
            names[index] = item.getAsString();
        }
        return names;
    }

    private static String requireString(JsonObject source, String key, String message) throws TypedApiException {
        if (source == null || !source.has(key) || !source.get(key).isJsonPrimitive()) {
            throw new TypedApiException("BAD_REQUEST", message);
        }
        String value = source.get(key).getAsString();
        if (value == null || value.isBlank()) {
            throw new TypedApiException("BAD_REQUEST", message);
        }
        return value;
    }

    private static JsonObject readOptionalObject(JsonObject source, String key) {
        if (source == null || !source.has(key) || !source.get(key).isJsonObject()) {
            return null;
        }
        return source.getAsJsonObject(key);
    }

    private static JsonObject requireObject(JsonObject source, String key, String message) throws TypedApiException {
        JsonObject value = readOptionalObject(source, key);
        if (value == null) {
            throw new TypedApiException("BAD_REQUEST", message);
        }
        return value;
    }

    private static TypedApiException invocationError(String phase, String subject, Throwable cause) {
        JsonObject details = new JsonObject();
        details.addProperty("phase", phase);
        details.addProperty("subject", subject);
        if (cause != null) {
            details.addProperty("cause_type", cause.getClass().getName());
            details.addProperty("cause_message", cause.getMessage());
        }
        return new TypedApiException("API_INVOCATION_ERROR", "Typed API invocation failed", details);
    }

    @FunctionalInterface
    public interface RootResolver {
        Object resolve() throws Exception;
    }

    private record RootBinding(String name, String javaType, RootResolver resolver) {
    }

    private record ResolvedTarget(String kind, String name, String referenceId, Class<?> targetClass, Object targetObject) {
    }

    private record ConstructSelection(Constructor<?> constructor, Object[] arguments) {
    }

    private record MethodSelection(Method method, Object invokeTarget, Object[] arguments) {
    }
}
