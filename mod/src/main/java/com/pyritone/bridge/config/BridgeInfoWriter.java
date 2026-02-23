package com.pyritone.bridge.config;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import com.google.gson.JsonObject;
import org.slf4j.Logger;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;

public final class BridgeInfoWriter {
    private static final Gson GSON = new GsonBuilder().setPrettyPrinting().disableHtmlEscaping().create();

    private BridgeInfoWriter() {
    }

    public static void write(Logger logger, String host, int port, String token, int protocolVersion, String serverVersion) {
        Path infoFile = BridgeConfig.bridgeInfoFile();

        JsonObject payload = new JsonObject();
        payload.addProperty("host", host);
        payload.addProperty("port", port);
        payload.addProperty("transport", "websocket");
        payload.addProperty("ws_path", BridgeConfig.DEFAULT_WS_PATH);
        payload.addProperty("ws_url", "ws://" + host + ":" + port + BridgeConfig.DEFAULT_WS_PATH);
        payload.addProperty("token", token);
        payload.addProperty("protocol_version", protocolVersion);
        payload.addProperty("server_version", serverVersion);
        payload.addProperty("mod_id", BridgeConfig.MOD_ID);

        try {
            Files.createDirectories(infoFile.getParent());
            Files.writeString(infoFile, GSON.toJson(payload) + System.lineSeparator(), StandardCharsets.UTF_8);
        } catch (IOException exception) {
            logger.error("Failed to write bridge info file {}", infoFile.toAbsolutePath(), exception);
        }
    }
}
