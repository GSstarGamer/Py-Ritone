from __future__ import annotations

import pyritone

client = pyritone.client()


@client.event
async def on_ready() -> None:
    print("connected to client")


@client.event
async def on_chat_message(ctx: pyritone.minecraft.chat.message) -> None:
    print(f"[chat] {ctx.message}")


@client.event
async def on_system_message(ctx: pyritone.minecraft.chat.system_message) -> None:
    print(f"[system]{' [overlay]' if ctx.overlay else ''} {ctx.message}")


@client.event
async def on_player_join(ctx: pyritone.minecraft.player.join) -> None:
    print(f"[join] {ctx.player.name}")


@client.event
async def on_player_leave(ctx: pyritone.minecraft.player.leave) -> None:
    print(f"[leave] {ctx.player.name}")


@client.event
async def on_player_death(ctx: pyritone.minecraft.player.death) -> None:
    print(f"[death] {ctx.player.name}")


@client.event
async def on_player_respawn(ctx: pyritone.minecraft.player.respawn) -> None:
    print(f"[respawn] {ctx.player.name}")


@client.event
async def on_disconnect() -> None:
    print("disconnected from client")


if __name__ == "__main__":
    client.connect()
