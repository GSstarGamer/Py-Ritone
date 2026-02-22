package com.pyritone.bridge.config;

import net.fabricmc.loader.api.FabricLoader;

import java.nio.file.Path;

public final class BridgeConfig {
    public static final String MOD_ID = "pyritone_bridge";
    public static final String DEFAULT_HOST = "127.0.0.1";
    public static final int DEFAULT_PORT = 27841;
    public static final int PROTOCOL_VERSION = 1;
    public static final String TOKEN_FILE_NAME = "token.txt";
    public static final String BRIDGE_INFO_FILE_NAME = "bridge-info.json";

    private BridgeConfig() {
    }

    public static Path configDirectory() {
        return FabricLoader.getInstance().getConfigDir().resolve(MOD_ID);
    }

    public static Path tokenFile() {
        return configDirectory().resolve(TOKEN_FILE_NAME);
    }

    public static Path bridgeInfoFile() {
        return configDirectory().resolve(BRIDGE_INFO_FILE_NAME);
    }
}
