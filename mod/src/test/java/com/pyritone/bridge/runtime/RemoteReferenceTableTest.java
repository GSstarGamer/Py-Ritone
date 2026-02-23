package com.pyritone.bridge.runtime;

import org.junit.jupiter.api.Test;

import java.util.Set;

import static org.junit.jupiter.api.Assertions.assertSame;
import static org.junit.jupiter.api.Assertions.assertTrue;

class RemoteReferenceTableTest {
    @Test
    void storesAndResolvesBySession() {
        RemoteReferenceTable table = new RemoteReferenceTable();
        Object first = new Object();
        Object second = new Object();

        String refA = table.store("session-a", first);
        String refARepeat = table.store("session-a", first);
        String refB = table.store("session-b", second);

        assertSame(first, table.resolve("session-a", refA).orElseThrow());
        assertSame(second, table.resolve("session-b", refB).orElseThrow());
        assertTrue(refA.equals(refARepeat));
    }

    @Test
    void retainSessionsDropsStaleReferences() {
        RemoteReferenceTable table = new RemoteReferenceTable();
        Object first = new Object();
        Object second = new Object();

        String refA = table.store("session-a", first);
        String refB = table.store("session-b", second);
        table.retainSessions(Set.of("session-a"));

        assertTrue(table.resolve("session-a", refA).isPresent());
        assertTrue(table.resolve("session-b", refB).isEmpty());
    }
}
