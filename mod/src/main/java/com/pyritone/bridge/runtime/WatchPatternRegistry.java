package com.pyritone.bridge.runtime;

import com.google.gson.JsonArray;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Locale;
import java.util.concurrent.CopyOnWriteArrayList;

public final class WatchPatternRegistry {
    private final CopyOnWriteArrayList<String> patterns = new CopyOnWriteArrayList<>();

    public int addPattern(String pattern) {
        String normalized = pattern.trim();
        if (normalized.isEmpty()) {
            return patterns.size();
        }
        if (!patterns.contains(normalized)) {
            patterns.add(normalized);
        }
        return patterns.size();
    }

    public void clear() {
        patterns.clear();
    }

    public List<String> list() {
        return Collections.unmodifiableList(new ArrayList<>(patterns));
    }

    public List<String> matches(String message) {
        if (message == null || message.isBlank()) {
            return List.of();
        }
        String haystack = message.toLowerCase(Locale.ROOT);
        List<String> matched = new ArrayList<>();
        for (String pattern : patterns) {
            if (haystack.contains(pattern.toLowerCase(Locale.ROOT))) {
                matched.add(pattern);
            }
        }
        return matched;
    }

    public JsonArray toJsonArray() {
        JsonArray array = new JsonArray();
        for (String pattern : patterns) {
            array.add(pattern);
        }
        return array;
    }
}
