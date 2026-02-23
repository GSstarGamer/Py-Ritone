package com.pyritone.bridge.command;

import com.mojang.brigadier.arguments.StringArgumentType;
import com.pyritone.bridge.PyritoneBridgeClientMod;
import net.fabricmc.fabric.api.client.command.v2.ClientCommandManager;
import net.fabricmc.fabric.api.client.command.v2.ClientCommandRegistrationCallback;
import net.minecraft.text.Text;

public final class PyritoneCommand {
    private PyritoneCommand() {
    }

    public static void register(PyritoneBridgeClientMod mod) {
        ClientCommandRegistrationCallback.EVENT.register((dispatcher, registryAccess) -> {
            dispatcher.register(
                ClientCommandManager.literal("pyritone")
                    .then(ClientCommandManager.literal("status")
                        .executes(context -> {
                            context.getSource().sendFeedback(Text.literal(mod.commandStatusLine()));
                            return 1;
                        }))
                    .then(ClientCommandManager.literal("end")
                        .executes(context -> {
                            int disconnected = mod.endPythonSessionsFromPyritoneCommand();
                            if (disconnected > 0) {
                                context.getSource().sendFeedback(Text.literal("Ended " + disconnected + " Python websocket session(s)"));
                            } else {
                                context.getSource().sendFeedback(Text.literal("No authenticated Python websocket sessions"));
                            }
                            return 1;
                        }))
                    .then(ClientCommandManager.literal("bridge-info")
                        .executes(context -> {
                            context.getSource().sendFeedback(Text.literal(mod.bridgeInfoPath().toString()));
                            return 1;
                        }))
                    .then(ClientCommandManager.literal("watch")
                        .then(ClientCommandManager.literal("add")
                            .then(ClientCommandManager.argument("pattern", StringArgumentType.greedyString())
                                .executes(context -> {
                                    String pattern = StringArgumentType.getString(context, "pattern");
                                    int size = mod.addWatchPattern(pattern);
                                    context.getSource().sendFeedback(Text.literal("Added watch pattern. Total patterns=" + size));
                                    return 1;
                                })))
                        .then(ClientCommandManager.literal("clear")
                            .executes(context -> {
                                mod.clearWatchPatterns();
                                context.getSource().sendFeedback(Text.literal("Cleared watch patterns"));
                                return 1;
                            }))
                        .then(ClientCommandManager.literal("list")
                            .executes(context -> {
                                context.getSource().sendFeedback(Text.literal("Watch patterns: " + mod.listWatchPatterns()));
                                return 1;
                            })))
            );
        });
    }
}
