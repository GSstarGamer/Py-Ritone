package com.pyritone.bridge.runtime;

import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

class TypedApiServiceTest {
    @Test
    void metadataListsRootsAndTypeMethods() throws Exception {
        TypedApiService service = new TypedApiService(getClass().getClassLoader());
        service.registerRoot("sample", SampleRoot.class.getName(), SampleRoot::new);

        JsonObject metadata = service.metadata("session-a", new JsonObject());
        JsonArray roots = metadata.getAsJsonArray("roots");
        assertEquals(1, roots.size());
        assertEquals("sample", roots.get(0).getAsJsonObject().get("name").getAsString());

        JsonObject targetRequest = new JsonObject();
        JsonObject target = new JsonObject();
        target.addProperty("kind", "root");
        target.addProperty("name", "sample");
        targetRequest.add("target", target);

        JsonObject targetMetadata = service.metadata("session-a", targetRequest);
        JsonObject type = targetMetadata.getAsJsonObject("type");
        JsonArray methods = type.getAsJsonArray("methods");

        boolean foundPlus = false;
        for (int index = 0; index < methods.size(); index += 1) {
            JsonObject method = methods.get(index).getAsJsonObject();
            if ("plus".equals(method.get("name").getAsString())) {
                foundPlus = true;
                break;
            }
        }
        assertTrue(foundPlus);
    }

    @Test
    void constructAndInvokeUseSessionScopedReferences() throws Exception {
        TypedApiService service = new TypedApiService(getClass().getClassLoader());

        JsonObject constructRequest = new JsonObject();
        constructRequest.addProperty("type", SampleBox.class.getName());
        JsonArray constructArgs = new JsonArray();
        constructArgs.add(5);
        constructRequest.add("args", constructArgs);

        JsonObject construct = service.construct("session-a", constructRequest);
        JsonObject reference = construct.getAsJsonObject("value");
        String refId = reference.get(TypedApiService.REF_KEY).getAsString();
        assertNotNull(refId);

        JsonObject invokeAddRequest = new JsonObject();
        invokeAddRequest.add("target", refTarget(refId));
        invokeAddRequest.addProperty("method", "add");
        JsonArray addArgs = new JsonArray();
        addArgs.add(3);
        invokeAddRequest.add("args", addArgs);

        JsonObject addResponse = service.invoke("session-a", invokeAddRequest);
        assertEquals(8, addResponse.get("value").getAsInt());

        JsonObject invokeChildRequest = new JsonObject();
        invokeChildRequest.add("target", refTarget(refId));
        invokeChildRequest.addProperty("method", "child");
        JsonArray childArgs = new JsonArray();
        childArgs.add(2);
        invokeChildRequest.add("args", childArgs);

        JsonObject childResponse = service.invoke("session-a", invokeChildRequest);
        JsonObject childRef = childResponse.getAsJsonObject("value");
        String childRefId = childRef.get(TypedApiService.REF_KEY).getAsString();

        JsonObject invokeChildAddRequest = new JsonObject();
        invokeChildAddRequest.add("target", refTarget(childRefId));
        invokeChildAddRequest.addProperty("method", "add");
        JsonArray childAddArgs = new JsonArray();
        childAddArgs.add(1);
        invokeChildAddRequest.add("args", childAddArgs);

        JsonObject childAdd = service.invoke("session-a", invokeChildAddRequest);
        assertEquals(8, childAdd.get("value").getAsInt());

        TypedApiException staleRefError = assertThrows(
            TypedApiException.class,
            () -> service.invoke("session-b", invokeAddRequest)
        );
        assertEquals("API_REFERENCE_NOT_FOUND", staleRefError.code());
    }

    @Test
    void ambiguousMethodRequiresExplicitParameterTypes() throws Exception {
        TypedApiService service = new TypedApiService(getClass().getClassLoader());
        service.registerRoot("sample", SampleRoot.class.getName(), SampleRoot::new);

        JsonObject invokeRequest = new JsonObject();
        invokeRequest.add("target", rootTarget("sample"));
        invokeRequest.addProperty("method", "pick");
        JsonArray args = new JsonArray();
        args.add(1);
        invokeRequest.add("args", args);

        TypedApiException ambiguous = assertThrows(
            TypedApiException.class,
            () -> service.invoke("session-a", invokeRequest)
        );
        assertEquals("API_AMBIGUOUS_CALL", ambiguous.code());

        JsonArray parameterTypes = new JsonArray();
        parameterTypes.add("java.lang.Integer");
        invokeRequest.add("parameter_types", parameterTypes);
        JsonObject resolved = service.invoke("session-a", invokeRequest);
        assertEquals("int:1", resolved.get("value").getAsString());
    }

    @Test
    void argumentCoercionErrorIncludesDetails() throws Exception {
        TypedApiService service = new TypedApiService(getClass().getClassLoader());
        service.registerRoot("sample", SampleRoot.class.getName(), SampleRoot::new);

        JsonObject invokeRequest = new JsonObject();
        invokeRequest.add("target", rootTarget("sample"));
        invokeRequest.addProperty("method", "plus");
        JsonArray args = new JsonArray();
        args.add("oops");
        args.add(2);
        invokeRequest.add("args", args);

        TypedApiException error = assertThrows(
            TypedApiException.class,
            () -> service.invoke("session-a", invokeRequest)
        );

        assertEquals("API_ARGUMENT_COERCION_FAILED", error.code());
        assertNotNull(error.details());
        assertTrue(error.details().has("target_type"));
    }

    private static JsonObject rootTarget(String rootName) {
        JsonObject target = new JsonObject();
        target.addProperty("kind", "root");
        target.addProperty("name", rootName);
        return target;
    }

    private static JsonObject refTarget(String referenceId) {
        JsonObject target = new JsonObject();
        target.addProperty("kind", "ref");
        target.addProperty("id", referenceId);
        return target;
    }

    private static final class SampleRoot {
        public int plus(int left, int right) {
            return left + right;
        }

        public String pick(String value) {
            return "string:" + value;
        }

        public String pick(Integer value) {
            return "int:" + value;
        }
    }

    public static final class SampleBox {
        private final int base;

        public SampleBox(int base) {
            this.base = base;
        }

        public int add(int delta) {
            return base + delta;
        }

        public SampleBox child(int offset) {
            return new SampleBox(base + offset);
        }
    }
}
