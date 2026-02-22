package com.pyritone.bridge.config;

import org.slf4j.Logger;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.SecureRandom;
import java.util.Base64;

public final class TokenManager {
    private static final SecureRandom RANDOM = new SecureRandom();

    private TokenManager() {
    }

    public static String loadOrCreateToken(Logger logger) {
        Path directory = BridgeConfig.configDirectory();
        Path tokenFile = BridgeConfig.tokenFile();

        try {
            Files.createDirectories(directory);
            if (Files.exists(tokenFile)) {
                String token = Files.readString(tokenFile, StandardCharsets.UTF_8).trim();
                if (!token.isEmpty()) {
                    return token;
                }
            }

            String token = generateToken();
            Files.writeString(tokenFile, token + System.lineSeparator(), StandardCharsets.UTF_8);
            logger.info("Generated bridge token at {}", tokenFile.toAbsolutePath());
            return token;
        } catch (IOException exception) {
            logger.error("Failed to load or create token file {}", tokenFile.toAbsolutePath(), exception);
            return generateToken();
        }
    }

    private static String generateToken() {
        byte[] value = new byte[24];
        RANDOM.nextBytes(value);
        return Base64.getUrlEncoder().withoutPadding().encodeToString(value);
    }
}
