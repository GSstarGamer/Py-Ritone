package com.pyritone.bridge.runtime;

import com.google.gson.JsonObject;

public final class TypedApiException extends Exception {
    private final String code;
    private final JsonObject details;

    public TypedApiException(String code, String message) {
        this(code, message, null);
    }

    public TypedApiException(String code, String message, JsonObject details) {
        super(message);
        this.code = code;
        this.details = details;
    }

    public String code() {
        return code;
    }

    public JsonObject details() {
        return details;
    }
}
