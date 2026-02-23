package com.pyritone.bridge.runtime;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonNull;
import com.google.gson.JsonObject;
import com.google.gson.JsonPrimitive;

import java.lang.reflect.Array;
import java.lang.reflect.Modifier;
import java.util.ArrayList;
import java.util.Collection;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;

final class TypedApiValueCodec {
    private final Gson gson = new GsonBuilder().disableHtmlEscaping().create();
    private final ClassLoader classLoader;
    private final RemoteReferenceTable references;

    TypedApiValueCodec(ClassLoader classLoader, RemoteReferenceTable references) {
        this.classLoader = classLoader;
        this.references = references;
    }

    Object[] coerceArguments(String sessionId, JsonArray args, Class<?>[] parameterTypes) throws TypedApiException {
        if (args.size() != parameterTypes.length) {
            JsonObject details = new JsonObject();
            details.addProperty("expected_count", parameterTypes.length);
            details.addProperty("actual_count", args.size());
            throw new TypedApiException("BAD_REQUEST", "Argument count mismatch", details);
        }

        Object[] values = new Object[parameterTypes.length];
        for (int index = 0; index < parameterTypes.length; index += 1) {
            values[index] = coerceArgument(sessionId, args.get(index), parameterTypes[index], index);
        }
        return values;
    }

    JsonElement encodeValue(String sessionId, Object value) {
        if (value == null) {
            return JsonNull.INSTANCE;
        }
        if (value instanceof JsonElement element) {
            return element.deepCopy();
        }
        if (value instanceof Boolean bool) {
            return new JsonPrimitive(bool);
        }
        if (value instanceof Number number) {
            return new JsonPrimitive(number);
        }
        if (value instanceof Character character) {
            return new JsonPrimitive(String.valueOf(character));
        }
        if (value instanceof String text) {
            return new JsonPrimitive(text);
        }
        if (value instanceof Enum<?> enumValue) {
            return new JsonPrimitive(enumValue.name());
        }
        if (value instanceof Class<?> type) {
            return new JsonPrimitive(type.getName());
        }
        if (value instanceof Optional<?> optional) {
            return encodeValue(sessionId, optional.orElse(null));
        }

        Class<?> valueType = value.getClass();
        if (valueType.isArray()) {
            JsonArray array = new JsonArray();
            int length = Array.getLength(value);
            for (int index = 0; index < length; index += 1) {
                array.add(encodeValue(sessionId, Array.get(value, index)));
            }
            return array;
        }
        if (value instanceof Iterable<?> iterable) {
            JsonArray array = new JsonArray();
            for (Object item : iterable) {
                array.add(encodeValue(sessionId, item));
            }
            return array;
        }
        if (value instanceof Map<?, ?> map) {
            JsonObject object = new JsonObject();
            for (Map.Entry<?, ?> entry : map.entrySet()) {
                object.add(String.valueOf(entry.getKey()), encodeValue(sessionId, entry.getValue()));
            }
            return object;
        }

        String referenceId = references.store(sessionId, value);
        JsonObject reference = new JsonObject();
        reference.addProperty(TypedApiService.REF_KEY, referenceId);
        reference.addProperty("java_type", valueType.getName());
        return reference;
    }

    Class<?> resolveTypeByName(String typeName) throws TypedApiException {
        return switch (typeName) {
            case "boolean" -> boolean.class;
            case "byte" -> byte.class;
            case "short" -> short.class;
            case "int" -> int.class;
            case "long" -> long.class;
            case "float" -> float.class;
            case "double" -> double.class;
            case "char" -> char.class;
            case "void" -> void.class;
            default -> {
                try {
                    yield Class.forName(typeName, true, classLoader);
                } catch (ClassNotFoundException exception) {
                    JsonObject details = new JsonObject();
                    details.addProperty("type", typeName);
                    throw new TypedApiException("API_TYPE_NOT_FOUND", "Unknown Java type: " + typeName, details);
                }
            }
        };
    }

    private Object coerceArgument(String sessionId, JsonElement element, Class<?> expectedType, int argIndex) throws TypedApiException {
        String referenceId = extractReferenceId(element);
        if (referenceId != null) {
            Object resolved = references.resolve(sessionId, referenceId).orElse(null);
            if (resolved == null) {
                JsonObject details = new JsonObject();
                details.addProperty("reference_id", referenceId);
                details.addProperty("arg_index", argIndex);
                throw new TypedApiException("API_REFERENCE_NOT_FOUND", "Unknown remote reference: " + referenceId, details);
            }
            Class<?> boxedExpected = boxType(expectedType);
            if (boxedExpected != Object.class && !boxedExpected.isAssignableFrom(resolved.getClass())) {
                JsonObject details = new JsonObject();
                details.addProperty("reference_id", referenceId);
                details.addProperty("arg_index", argIndex);
                details.addProperty("expected_type", boxedExpected.getName());
                details.addProperty("actual_type", resolved.getClass().getName());
                throw new TypedApiException("API_ARGUMENT_COERCION_FAILED", "Remote reference type mismatch", details);
            }
            return resolved;
        }

        if (element == null || element.isJsonNull()) {
            if (expectedType.isPrimitive()) {
                throw coercionError(argIndex, expectedType, JsonNull.INSTANCE, "Null is not allowed for primitive");
            }
            return null;
        }

        if (JsonElement.class.isAssignableFrom(expectedType)) {
            return element.deepCopy();
        }
        if (expectedType == String.class) {
            if (!element.isJsonPrimitive()) {
                throw coercionError(argIndex, expectedType, element, "Expected string primitive");
            }
            return element.getAsString();
        }
        if (expectedType == boolean.class || expectedType == Boolean.class) {
            if (!element.isJsonPrimitive()) {
                throw coercionError(argIndex, expectedType, element, "Expected boolean primitive");
            }
            return element.getAsBoolean();
        }
        if (expectedType == byte.class || expectedType == Byte.class) {
            return numberValue(expectedType, argIndex, element).byteValue();
        }
        if (expectedType == short.class || expectedType == Short.class) {
            return numberValue(expectedType, argIndex, element).shortValue();
        }
        if (expectedType == int.class || expectedType == Integer.class) {
            return numberValue(expectedType, argIndex, element).intValue();
        }
        if (expectedType == long.class || expectedType == Long.class) {
            return numberValue(expectedType, argIndex, element).longValue();
        }
        if (expectedType == float.class || expectedType == Float.class) {
            return numberValue(expectedType, argIndex, element).floatValue();
        }
        if (expectedType == double.class || expectedType == Double.class) {
            return numberValue(expectedType, argIndex, element).doubleValue();
        }
        if (expectedType == char.class || expectedType == Character.class) {
            if (!element.isJsonPrimitive()) {
                throw coercionError(argIndex, expectedType, element, "Expected character primitive");
            }
            String value = element.getAsString();
            if (value.length() != 1) {
                throw coercionError(argIndex, expectedType, element, "Expected single-character string");
            }
            return value.charAt(0);
        }
        if (expectedType == Class.class) {
            if (!element.isJsonPrimitive()) {
                throw coercionError(argIndex, expectedType, element, "Expected class name string");
            }
            return resolveTypeByName(element.getAsString());
        }

        if (expectedType.isEnum()) {
            if (!element.isJsonPrimitive()) {
                throw coercionError(argIndex, expectedType, element, "Expected enum name string");
            }
            String enumName = element.getAsString();
            @SuppressWarnings({"unchecked", "rawtypes"})
            Class<? extends Enum> enumType = (Class<? extends Enum>) expectedType;
            try {
                return Enum.valueOf(enumType, enumName);
            } catch (IllegalArgumentException exception) {
                throw coercionError(argIndex, expectedType, element, "Unknown enum constant: " + enumName);
            }
        }

        if (expectedType.isArray()) {
            if (!element.isJsonArray()) {
                throw coercionError(argIndex, expectedType, element, "Expected array");
            }
            Class<?> componentType = expectedType.getComponentType();
            JsonArray array = element.getAsJsonArray();
            Object targetArray = Array.newInstance(componentType, array.size());
            for (int index = 0; index < array.size(); index += 1) {
                Object item = coerceArgument(sessionId, array.get(index), componentType, argIndex);
                Array.set(targetArray, index, item);
            }
            return targetArray;
        }

        if (Collection.class.isAssignableFrom(expectedType)) {
            if (!element.isJsonArray()) {
                throw coercionError(argIndex, expectedType, element, "Expected array");
            }
            Collection<Object> collection = instantiateCollection(expectedType);
            for (JsonElement item : element.getAsJsonArray()) {
                collection.add(decodeUntyped(sessionId, item));
            }
            return collection;
        }

        if (Map.class.isAssignableFrom(expectedType)) {
            if (!element.isJsonObject()) {
                throw coercionError(argIndex, expectedType, element, "Expected object");
            }
            Map<String, Object> map = instantiateMap(expectedType);
            for (Map.Entry<String, JsonElement> entry : element.getAsJsonObject().entrySet()) {
                map.put(entry.getKey(), decodeUntyped(sessionId, entry.getValue()));
            }
            return map;
        }

        if (expectedType == Object.class) {
            return decodeUntyped(sessionId, element);
        }

        try {
            Object value = gson.fromJson(element, expectedType);
            if (value == null && expectedType.isPrimitive()) {
                throw coercionError(argIndex, expectedType, element, "Expected non-null primitive");
            }
            return value;
        } catch (TypedApiException exception) {
            throw exception;
        } catch (Exception exception) {
            throw coercionError(argIndex, expectedType, element, "Unable to coerce argument");
        }
    }

    private Number numberValue(Class<?> expectedType, int argIndex, JsonElement element) throws TypedApiException {
        if (!element.isJsonPrimitive()) {
            throw coercionError(argIndex, expectedType, element, "Expected numeric primitive");
        }
        JsonPrimitive primitive = element.getAsJsonPrimitive();
        if (!primitive.isNumber() && !primitive.isString()) {
            throw coercionError(argIndex, expectedType, element, "Expected numeric primitive");
        }
        try {
            String raw = primitive.getAsString();
            if (raw.contains(".") || raw.contains("e") || raw.contains("E")) {
                return Double.parseDouble(raw);
            }
            return Long.parseLong(raw);
        } catch (Exception exception) {
            throw coercionError(argIndex, expectedType, element, "Invalid numeric value");
        }
    }

    private Object decodeUntyped(String sessionId, JsonElement element) throws TypedApiException {
        String referenceId = extractReferenceId(element);
        if (referenceId != null) {
            Object resolved = references.resolve(sessionId, referenceId).orElse(null);
            if (resolved == null) {
                JsonObject details = new JsonObject();
                details.addProperty("reference_id", referenceId);
                throw new TypedApiException("API_REFERENCE_NOT_FOUND", "Unknown remote reference: " + referenceId, details);
            }
            return resolved;
        }

        if (element == null || element.isJsonNull()) {
            return null;
        }
        if (element.isJsonPrimitive()) {
            JsonPrimitive primitive = element.getAsJsonPrimitive();
            if (primitive.isBoolean()) {
                return primitive.getAsBoolean();
            }
            if (primitive.isNumber()) {
                String raw = primitive.getAsString();
                if (raw.contains(".") || raw.contains("e") || raw.contains("E")) {
                    return primitive.getAsDouble();
                }
                try {
                    long value = Long.parseLong(raw);
                    if (value >= Integer.MIN_VALUE && value <= Integer.MAX_VALUE) {
                        return (int) value;
                    }
                    return value;
                } catch (NumberFormatException exception) {
                    return primitive.getAsDouble();
                }
            }
            return primitive.getAsString();
        }

        if (element.isJsonArray()) {
            List<Object> values = new ArrayList<>();
            for (JsonElement item : element.getAsJsonArray()) {
                values.add(decodeUntyped(sessionId, item));
            }
            return values;
        }

        Map<String, Object> values = new LinkedHashMap<>();
        for (Map.Entry<String, JsonElement> entry : element.getAsJsonObject().entrySet()) {
            values.put(entry.getKey(), decodeUntyped(sessionId, entry.getValue()));
        }
        return values;
    }

    private static String extractReferenceId(JsonElement element) {
        if (element == null || !element.isJsonObject()) {
            return null;
        }
        JsonObject object = element.getAsJsonObject();
        if (!object.has(TypedApiService.REF_KEY) || !object.get(TypedApiService.REF_KEY).isJsonPrimitive()) {
            return null;
        }
        String referenceId = object.get(TypedApiService.REF_KEY).getAsString();
        return referenceId == null || referenceId.isBlank() ? null : referenceId;
    }

    private static Class<?> boxType(Class<?> type) {
        if (!type.isPrimitive()) {
            return type;
        }
        if (type == boolean.class) {
            return Boolean.class;
        }
        if (type == byte.class) {
            return Byte.class;
        }
        if (type == short.class) {
            return Short.class;
        }
        if (type == int.class) {
            return Integer.class;
        }
        if (type == long.class) {
            return Long.class;
        }
        if (type == float.class) {
            return Float.class;
        }
        if (type == double.class) {
            return Double.class;
        }
        if (type == char.class) {
            return Character.class;
        }
        return type;
    }

    @SuppressWarnings("unchecked")
    private static Collection<Object> instantiateCollection(Class<?> collectionType) throws TypedApiException {
        if (collectionType.isInterface() || Modifier.isAbstract(collectionType.getModifiers())) {
            if (Set.class.isAssignableFrom(collectionType)) {
                return new LinkedHashSet<>();
            }
            return new ArrayList<>();
        }
        try {
            return (Collection<Object>) collectionType.getDeclaredConstructor().newInstance();
        } catch (Exception exception) {
            throw new TypedApiException("API_ARGUMENT_COERCION_FAILED", "Unable to create collection argument");
        }
    }

    @SuppressWarnings("unchecked")
    private static Map<String, Object> instantiateMap(Class<?> mapType) throws TypedApiException {
        if (mapType.isInterface() || Modifier.isAbstract(mapType.getModifiers())) {
            return new LinkedHashMap<>();
        }
        try {
            return (Map<String, Object>) mapType.getDeclaredConstructor().newInstance();
        } catch (Exception exception) {
            throw new TypedApiException("API_ARGUMENT_COERCION_FAILED", "Unable to create map argument");
        }
    }

    private static TypedApiException coercionError(int argIndex, Class<?> expectedType, JsonElement value, String reason) {
        JsonObject details = new JsonObject();
        details.addProperty("arg_index", argIndex);
        details.addProperty("expected_type", expectedType.getName());
        details.addProperty("reason", reason);
        details.add("value", value == null ? JsonNull.INSTANCE : value.deepCopy());
        return new TypedApiException("API_ARGUMENT_COERCION_FAILED", "Unable to coerce typed API argument", details);
    }
}
