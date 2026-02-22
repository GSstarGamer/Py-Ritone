package com.pyritone.bridge.runtime;

import com.google.gson.JsonObject;

public record TaskSnapshot(
    String taskId,
    String command,
    TaskState state,
    String startedAt,
    String updatedAt,
    String detail
) {
    public JsonObject toJson() {
        JsonObject object = new JsonObject();
        object.addProperty("task_id", taskId);
        object.addProperty("command", command);
        object.addProperty("state", state.name());
        object.addProperty("started_at", startedAt);
        object.addProperty("updated_at", updatedAt);
        if (detail != null && !detail.isBlank()) {
            object.addProperty("detail", detail);
        }
        return object;
    }
}
