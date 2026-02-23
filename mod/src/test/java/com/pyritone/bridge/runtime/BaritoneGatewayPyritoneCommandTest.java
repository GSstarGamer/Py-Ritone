package com.pyritone.bridge.runtime;

import org.junit.jupiter.api.Test;
import org.slf4j.LoggerFactory;

import java.lang.reflect.Method;
import java.util.List;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.stream.Stream;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

class BaritoneGatewayPyritoneCommandTest {
    @Test
    void executeRoutesEndPauseResumeSubcommands() throws Exception {
        BaritoneGateway gateway = new BaritoneGateway(LoggerFactory.getLogger(BaritoneGateway.class), event -> {
        });

        Method executeMethod = PyritoneCommandMethods.class.getMethod("execute", Object.class, Object.class);
        Method handler = commandHandlerMethod();

        AtomicInteger ended = new AtomicInteger();
        AtomicInteger paused = new AtomicInteger();
        AtomicInteger resumed = new AtomicInteger();

        handler.invoke(
            gateway,
            new Object(),
            executeMethod,
            new Object[]{null, new FakeArgConsumer("end")},
            (Runnable) ended::incrementAndGet,
            (Runnable) paused::incrementAndGet,
            (Runnable) resumed::incrementAndGet
        );
        handler.invoke(
            gateway,
            new Object(),
            executeMethod,
            new Object[]{null, new FakeArgConsumer("pause")},
            (Runnable) ended::incrementAndGet,
            (Runnable) paused::incrementAndGet,
            (Runnable) resumed::incrementAndGet
        );
        handler.invoke(
            gateway,
            new Object(),
            executeMethod,
            new Object[]{null, new FakeArgConsumer("resume")},
            (Runnable) ended::incrementAndGet,
            (Runnable) paused::incrementAndGet,
            (Runnable) resumed::incrementAndGet
        );

        assertEquals(1, ended.get());
        assertEquals(1, paused.get());
        assertEquals(1, resumed.get());
    }

    @Test
    void tabCompleteIncludesPauseAndResume() throws Exception {
        BaritoneGateway gateway = new BaritoneGateway(LoggerFactory.getLogger(BaritoneGateway.class), event -> {
        });

        Method tabCompleteMethod = PyritoneCommandMethods.class.getMethod("tabComplete", Object.class, Object.class);
        Method handler = commandHandlerMethod();

        @SuppressWarnings("unchecked")
        Stream<String> all = (Stream<String>) handler.invoke(
            gateway,
            new Object(),
            tabCompleteMethod,
            new Object[]{null, new FakeArgConsumer("")},
            (Runnable) () -> {
            },
            (Runnable) () -> {
            },
            (Runnable) () -> {
            }
        );
        List<String> allOptions = all.toList();
        assertTrue(allOptions.contains("end"));
        assertTrue(allOptions.contains("pause"));
        assertTrue(allOptions.contains("resume"));

        @SuppressWarnings("unchecked")
        Stream<String> resumedOnly = (Stream<String>) handler.invoke(
            gateway,
            new Object(),
            tabCompleteMethod,
            new Object[]{null, new FakeArgConsumer("re")},
            (Runnable) () -> {
            },
            (Runnable) () -> {
            },
            (Runnable) () -> {
            }
        );
        assertEquals(List.of("resume"), resumedOnly.toList());
    }

    private static Method commandHandlerMethod() throws Exception {
        Method method = BaritoneGateway.class.getDeclaredMethod(
            "handlePyritoneCommandCall",
            Object.class,
            Method.class,
            Object[].class,
            Runnable.class,
            Runnable.class,
            Runnable.class
        );
        method.setAccessible(true);
        return method;
    }

    private interface PyritoneCommandMethods {
        void execute(Object label, Object argConsumer);

        Stream<String> tabComplete(Object label, Object argConsumer);
    }

    public static final class FakeArgConsumer {
        private final String rawRest;

        public FakeArgConsumer(String rawRest) {
            this.rawRest = rawRest;
        }

        public String rawRest() {
            return rawRest;
        }
    }
}

