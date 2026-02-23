from __future__ import annotations

import asyncio
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, Awaitable, Callable
from uuid import uuid4

from .minecraft._identifiers import BlockLike, coerce_block_id
from .models import BridgeError, RemoteRef

if TYPE_CHECKING:
    from .client_async import Client


BARITONE_PROVIDER_TYPE = "baritone.api.IBaritoneProvider"
BARITONE_TYPE = "baritone.api.IBaritone"
GOAL_TYPE = "baritone.api.pathing.goals.Goal"
WORLD_PROVIDER_TYPE = "baritone.api.cache.IWorldProvider"
WORLD_DATA_TYPE = "baritone.api.cache.IWorldData"
CACHED_WORLD_TYPE = "baritone.api.cache.ICachedWorld"
WAYPOINT_COLLECTION_TYPE = "baritone.api.cache.IWaypointCollection"
WAYPOINT_TYPE = "baritone.api.cache.IWaypoint"
WORLD_SCANNER_TYPE = "baritone.api.cache.IWorldScanner"
SELECTION_MANAGER_TYPE = "baritone.api.selection.ISelectionManager"
SELECTION_TYPE = "baritone.api.selection.ISelection"
SCHEMATIC_SYSTEM_TYPE = "baritone.api.schematic.ISchematicSystem"
SCHEMATIC_FORMAT_TYPE = "baritone.api.schematic.format.ISchematicFormat"
SCHEMATIC_TYPE = "baritone.api.schematic.ISchematic"
STATIC_SCHEMATIC_TYPE = "baritone.api.schematic.IStaticSchematic"
FILL_SCHEMATIC_TYPE = "baritone.api.schematic.FillSchematic"
COMPOSITE_SCHEMATIC_TYPE = "baritone.api.schematic.CompositeSchematic"
MASK_TYPE = "baritone.api.schematic.mask.Mask"
STATIC_MASK_TYPE = "baritone.api.schematic.mask.StaticMask"
SPHERE_MASK_TYPE = "baritone.api.schematic.mask.shape.SphereMask"
CYLINDER_MASK_TYPE = "baritone.api.schematic.mask.shape.CylinderMask"
COMMAND_MANAGER_TYPE = "baritone.api.command.manager.ICommandManager"
COMMAND_SYSTEM_TYPE = "baritone.api.command.ICommandSystem"
ARG_PARSER_MANAGER_TYPE = "baritone.api.command.argparser.IArgParserManager"
COMMAND_TYPE = "baritone.api.command.ICommand"
REGISTRY_TYPE = "baritone.api.command.registry.Registry"
PLAYER_CONTEXT_TYPE = "baritone.api.utils.IPlayerContext"
INPUT_OVERRIDE_HANDLER_TYPE = "baritone.api.utils.IInputOverrideHandler"
BETTER_BLOCK_POS_TYPE = "baritone.api.utils.BetterBlockPos"
BLOCK_OPTIONAL_META_TYPE = "baritone.api.utils.BlockOptionalMeta"
BLOCK_OPTIONAL_META_LOOKUP_TYPE = "baritone.api.utils.BlockOptionalMetaLookup"
INPUT_TYPE = "baritone.api.utils.input.Input"
WAYPOINT_TAG_TYPE = "baritone.api.cache.IWaypoint$Tag"
EVENT_BUS_TYPE = "baritone.api.event.listener.IEventBus"
GAME_EVENT_LISTENER_TYPE = "baritone.api.event.listener.IGameEventListener"
DIRECTION_TYPE = "net.minecraft.class_2350"
AXIS_TYPE = "net.minecraft.class_2350$class_2351"
JAVA_FILE_TYPE = "java.io.File"


def _require_remote_ref(value: Any, *, context: str, expected_type: str | None = None) -> RemoteRef:
    if isinstance(value, RemoteRef):
        return value

    payload: dict[str, Any] = {"context": context, "value": value}
    if expected_type is not None:
        payload["expected_type"] = expected_type
    raise BridgeError("BAD_RESPONSE", f"Expected remote reference for {context}", payload)


def _unwrap_goal(goal: GoalRef | RemoteRef) -> RemoteRef:
    if isinstance(goal, GoalRef):
        return goal.ref
    if isinstance(goal, RemoteRef):
        return goal
    raise TypeError(f"Expected GoalRef or RemoteRef, got {type(goal)!r}")


def _unwrap_ref(value: Any) -> RemoteRef:
    if isinstance(value, RemoteRef):
        return value
    if isinstance(value, _RemoteWrapper):
        return value.ref
    raise TypeError(f"Expected RemoteRef or wrapper, got {type(value)!r}")


def _unwrap_ref_or_value(value: Any) -> Any:
    if isinstance(value, RemoteRef):
        return value
    if isinstance(value, _RemoteWrapper):
        return value.ref
    return value


def _require_remote_ref_list(value: Any, *, context: str, expected_type: str | None = None) -> list[RemoteRef]:
    if not isinstance(value, list):
        raise BridgeError("BAD_RESPONSE", f"Expected list from {context}", {"value": value})
    return [_require_remote_ref(item, context=context, expected_type=expected_type) for item in value]


def _require_string_list(value: Any, *, context: str) -> list[str]:
    if not isinstance(value, list):
        raise BridgeError("BAD_RESPONSE", f"Expected list from {context}", {"value": value})
    if not all(isinstance(item, str) for item in value):
        raise BridgeError("BAD_RESPONSE", f"Expected list[str] from {context}", {"value": value})
    return [str(item) for item in value]


async def _coerce_array_like(client: "Client", value: Any, *, context: str) -> list[Any]:
    if isinstance(value, list):
        return value
    if isinstance(value, RemoteRef):
        resolved = await client.api_invoke(value, "toArray", parameter_types=[])
        if isinstance(resolved, list):
            return resolved
        raise BridgeError("BAD_RESPONSE", f"Expected array value from {context}", {"value": resolved})
    raise BridgeError("BAD_RESPONSE", f"Expected list or stream reference from {context}", {"value": value})


@dataclass(slots=True, frozen=True)
class TypedTaskResult:
    handle_id: str
    action: str
    started: bool
    pathing: bool
    calculating: bool
    has_path: bool
    goal: GoalRef | None

    @property
    def busy(self) -> bool:
        return self.pathing or self.calculating


class TypedTaskHandle:
    def __init__(
        self,
        *,
        handle_id: str,
        action: str,
        waiter: Callable[[float | None, float, float], Awaitable[TypedTaskResult]],
    ) -> None:
        self.handle_id = handle_id
        self.action = action
        self._waiter = waiter

    async def wait(
        self,
        timeout: float | None = None,
        *,
        poll_interval: float = 0.1,
        startup_timeout: float = 1.0,
    ) -> TypedTaskResult:
        if poll_interval <= 0:
            raise ValueError("poll_interval must be > 0")
        if startup_timeout < 0:
            raise ValueError("startup_timeout must be >= 0")
        return await self._waiter(timeout, poll_interval, startup_timeout)


class _RemoteWrapper:
    def __init__(self, client: "Client", ref: RemoteRef) -> None:
        self._client = client
        self._ref = ref

    @property
    def ref(self) -> RemoteRef:
        return self._ref

    async def _invoke(
        self,
        method: str,
        *args: Any,
        parameter_types: list[str] | tuple[str, ...],
    ) -> Any:
        return await self._client.api_invoke(
            self._ref,
            method,
            *args,
            parameter_types=list(parameter_types),
        )


class _BaritoneWrapper(_RemoteWrapper):
    def __init__(self, client: "Client", baritone: "BaritoneNamespace", ref: RemoteRef) -> None:
        super().__init__(client, ref)
        self._baritone = baritone


class GoalRef(_RemoteWrapper):
    async def is_in_goal(self, x: int, y: int, z: int) -> bool:
        return bool(await self._invoke("isInGoal", x, y, z, parameter_types=["int", "int", "int"]))

    async def heuristic(self, x: int, y: int, z: int) -> float:
        return float(await self._invoke("heuristic", x, y, z, parameter_types=["int", "int", "int"]))

    async def heuristic_current(self) -> float:
        return float(await self._invoke("heuristic", parameter_types=[]))


class PathRef(_RemoteWrapper):
    async def length(self) -> int:
        return int(await self._invoke("length", parameter_types=[]))

    async def goal(self) -> GoalRef:
        value = await self._invoke("getGoal", parameter_types=[])
        return GoalRef(self._client, _require_remote_ref(value, context="IPath.getGoal", expected_type=GOAL_TYPE))

    async def num_nodes_considered(self) -> int:
        return int(await self._invoke("getNumNodesConsidered", parameter_types=[]))


class PathCalculationResultRef(_RemoteWrapper):
    async def result_type(self) -> str:
        value = await self._invoke("getType", parameter_types=[])
        if not isinstance(value, str):
            raise BridgeError("BAD_RESPONSE", "Expected enum string from PathCalculationResult.getType", {"value": value})
        return value

    async def path(self) -> PathRef | None:
        value = await self._invoke("getPath", parameter_types=[])
        if value is None:
            return None
        return PathRef(self._client, _require_remote_ref(value, context="PathCalculationResult.getPath"))


class PathFinderRef(_RemoteWrapper):
    async def goal(self) -> GoalRef:
        value = await self._invoke("getGoal", parameter_types=[])
        return GoalRef(self._client, _require_remote_ref(value, context="IPathFinder.getGoal", expected_type=GOAL_TYPE))

    async def calculate(self, primary_timeout_ms: int, failure_timeout_ms: int) -> PathCalculationResultRef:
        value = await self._invoke(
            "calculate",
            int(primary_timeout_ms),
            int(failure_timeout_ms),
            parameter_types=["long", "long"],
        )
        return PathCalculationResultRef(
            self._client,
            _require_remote_ref(value, context="IPathFinder.calculate", expected_type="baritone.api.utils.PathCalculationResult"),
        )

    async def is_finished(self) -> bool:
        return bool(await self._invoke("isFinished", parameter_types=[]))

    async def best_path_so_far(self) -> PathRef | None:
        value = await self._invoke("bestPathSoFar", parameter_types=[])
        if value is None:
            return None
        return PathRef(self._client, _require_remote_ref(value, context="IPathFinder.bestPathSoFar"))


class PathExecutorRef(_RemoteWrapper):
    async def path(self) -> PathRef:
        value = await self._invoke("getPath", parameter_types=[])
        return PathRef(self._client, _require_remote_ref(value, context="IPathExecutor.getPath"))

    async def position(self) -> int:
        return int(await self._invoke("getPosition", parameter_types=[]))


class PathingBehaviorRef(_RemoteWrapper):
    async def is_pathing(self) -> bool:
        return bool(await self._invoke("isPathing", parameter_types=[]))

    async def has_path(self) -> bool:
        return bool(await self._invoke("hasPath", parameter_types=[]))

    async def cancel_everything(self) -> bool:
        return bool(await self._invoke("cancelEverything", parameter_types=[]))

    async def force_cancel(self) -> None:
        await self._invoke("forceCancel", parameter_types=[])

    async def goal(self) -> GoalRef | None:
        value = await self._invoke("getGoal", parameter_types=[])
        if value is None:
            return None
        return GoalRef(self._client, _require_remote_ref(value, context="IPathingBehavior.getGoal", expected_type=GOAL_TYPE))

    async def path(self) -> PathRef | None:
        value = await self._invoke("getPath", parameter_types=[])
        if value is None:
            return None
        return PathRef(self._client, _require_remote_ref(value, context="IPathingBehavior.getPath"))

    async def in_progress(self) -> PathFinderRef | None:
        value = await self._invoke("getInProgress", parameter_types=[])
        if value is None:
            return None
        return PathFinderRef(self._client, _require_remote_ref(value, context="IPathingBehavior.getInProgress"))

    async def current(self) -> PathExecutorRef | None:
        value = await self._invoke("getCurrent", parameter_types=[])
        if value is None:
            return None
        return PathExecutorRef(self._client, _require_remote_ref(value, context="IPathingBehavior.getCurrent"))

    async def next(self) -> PathExecutorRef | None:
        value = await self._invoke("getNext", parameter_types=[])
        if value is None:
            return None
        return PathExecutorRef(self._client, _require_remote_ref(value, context="IPathingBehavior.getNext"))


class _ProcessRef(_BaritoneWrapper):
    async def is_active(self) -> bool:
        return bool(await self._invoke("isActive", parameter_types=[]))

    async def is_temporary(self) -> bool:
        return bool(await self._invoke("isTemporary", parameter_types=[]))

    async def priority(self) -> float:
        return float(await self._invoke("priority", parameter_types=[]))

    async def display_name(self) -> str:
        value = await self._invoke("displayName", parameter_types=[])
        if not isinstance(value, str):
            raise BridgeError("BAD_RESPONSE", "Expected string from IBaritoneProcess.displayName", {"value": value})
        return value

    def _new_task_handle(self, action: str) -> TypedTaskHandle:
        return self._baritone._new_task_handle(action)


class CustomGoalProcessRef(_ProcessRef):
    async def set_goal(self, goal: GoalRef | RemoteRef) -> None:
        await self._invoke("setGoal", _unwrap_goal(goal), parameter_types=[GOAL_TYPE])

    async def path_dispatch(self) -> TypedTaskHandle:
        await self._invoke("path", parameter_types=[])
        return self._new_task_handle("ICustomGoalProcess.path")

    async def path(
        self,
        timeout: float | None = None,
        *,
        poll_interval: float = 0.1,
        startup_timeout: float = 1.0,
    ) -> TypedTaskResult:
        handle = await self.path_dispatch()
        return await handle.wait(timeout, poll_interval=poll_interval, startup_timeout=startup_timeout)

    async def set_goal_and_path_dispatch(self, goal: GoalRef | RemoteRef) -> TypedTaskHandle:
        await self._invoke("setGoalAndPath", _unwrap_goal(goal), parameter_types=[GOAL_TYPE])
        return self._new_task_handle("ICustomGoalProcess.setGoalAndPath")

    async def set_goal_and_path(
        self,
        goal: GoalRef | RemoteRef,
        timeout: float | None = None,
        *,
        poll_interval: float = 0.1,
        startup_timeout: float = 1.0,
    ) -> TypedTaskResult:
        handle = await self.set_goal_and_path_dispatch(goal)
        return await handle.wait(timeout, poll_interval=poll_interval, startup_timeout=startup_timeout)

    async def goal(self) -> GoalRef | None:
        value = await self._invoke("getGoal", parameter_types=[])
        if value is None:
            return None
        return GoalRef(self._client, _require_remote_ref(value, context="ICustomGoalProcess.getGoal", expected_type=GOAL_TYPE))


class GetToBlockProcessRef(_ProcessRef):
    async def get_to_block_dispatch(self, block: RemoteRef | _RemoteWrapper | BlockLike) -> TypedTaskHandle:
        block_arg = await self._baritone.block_optional_meta(coerce_block_id(block)) if isinstance(block, str) else _unwrap_ref(block)
        await self._invoke("getToBlock", block_arg, parameter_types=["baritone.api.utils.BlockOptionalMeta"])
        return self._new_task_handle("IGetToBlockProcess.getToBlock")

    async def get_to_block(
        self,
        block: RemoteRef | _RemoteWrapper | BlockLike,
        timeout: float | None = None,
        *,
        poll_interval: float = 0.1,
        startup_timeout: float = 1.0,
    ) -> TypedTaskResult:
        handle = await self.get_to_block_dispatch(block)
        return await handle.wait(timeout, poll_interval=poll_interval, startup_timeout=startup_timeout)


class MineProcessRef(_ProcessRef):
    async def mine_by_name_dispatch(self, quantity: int, *block_names: BlockLike) -> TypedTaskHandle:
        if not block_names:
            raise ValueError("mine_by_name_dispatch requires at least one block name")
        resolved_names = [coerce_block_id(name) for name in block_names]
        await self._invoke(
            "mineByName",
            int(quantity),
            resolved_names,
            parameter_types=["int", "java.lang.String[]"],
        )
        return self._new_task_handle("IMineProcess.mineByName")

    async def mine_by_name(
        self,
        quantity: int,
        *block_names: BlockLike,
        timeout: float | None = None,
        poll_interval: float = 0.1,
        startup_timeout: float = 1.0,
    ) -> TypedTaskResult:
        handle = await self.mine_by_name_dispatch(quantity, *block_names)
        return await handle.wait(timeout, poll_interval=poll_interval, startup_timeout=startup_timeout)

    async def cancel(self) -> None:
        await self._invoke("cancel", parameter_types=[])


class ExploreProcessRef(_ProcessRef):
    async def explore_dispatch(self, x: int, z: int) -> TypedTaskHandle:
        await self._invoke("explore", int(x), int(z), parameter_types=["int", "int"])
        return self._new_task_handle("IExploreProcess.explore")

    async def explore(
        self,
        x: int,
        z: int,
        timeout: float | None = None,
        *,
        poll_interval: float = 0.1,
        startup_timeout: float = 1.0,
    ) -> TypedTaskResult:
        handle = await self.explore_dispatch(x, z)
        return await handle.wait(timeout, poll_interval=poll_interval, startup_timeout=startup_timeout)

    async def apply_json_filter(self, path: str | Path, invert: bool = False) -> None:
        path_ref = await self._baritone.java_path(path)
        await self._invoke("applyJsonFilter", path_ref, bool(invert), parameter_types=["java.nio.file.Path", "boolean"])


class BuilderProcessRef(_ProcessRef):
    async def build_open_schematic_dispatch(self) -> TypedTaskHandle:
        await self._invoke("buildOpenSchematic", parameter_types=[])
        return self._new_task_handle("IBuilderProcess.buildOpenSchematic")

    async def build_open_schematic(
        self,
        timeout: float | None = None,
        *,
        poll_interval: float = 0.1,
        startup_timeout: float = 1.0,
    ) -> TypedTaskResult:
        handle = await self.build_open_schematic_dispatch()
        return await handle.wait(timeout, poll_interval=poll_interval, startup_timeout=startup_timeout)

    async def build_open_litematic_dispatch(self, index: int) -> TypedTaskHandle:
        await self._invoke("buildOpenLitematic", int(index), parameter_types=["int"])
        return self._new_task_handle("IBuilderProcess.buildOpenLitematic")

    async def build_open_litematic(
        self,
        index: int,
        timeout: float | None = None,
        *,
        poll_interval: float = 0.1,
        startup_timeout: float = 1.0,
    ) -> TypedTaskResult:
        handle = await self.build_open_litematic_dispatch(index)
        return await handle.wait(timeout, poll_interval=poll_interval, startup_timeout=startup_timeout)

    async def pause(self) -> None:
        await self._invoke("pause", parameter_types=[])

    async def resume(self) -> None:
        await self._invoke("resume", parameter_types=[])

    async def is_paused(self) -> bool:
        return bool(await self._invoke("isPaused", parameter_types=[]))


class FollowProcessRef(_ProcessRef):
    async def follow_dispatch(self, entity_filter: RemoteRef | _RemoteWrapper) -> TypedTaskHandle:
        await self._invoke("follow", _unwrap_ref(entity_filter), parameter_types=["java.util.function.Predicate"])
        return self._new_task_handle("IFollowProcess.follow")

    async def follow(
        self,
        entity_filter: RemoteRef | _RemoteWrapper,
        timeout: float | None = None,
        *,
        poll_interval: float = 0.1,
        startup_timeout: float = 1.0,
    ) -> TypedTaskResult:
        handle = await self.follow_dispatch(entity_filter)
        return await handle.wait(timeout, poll_interval=poll_interval, startup_timeout=startup_timeout)

    async def pickup_dispatch(self, item_filter: RemoteRef | _RemoteWrapper) -> TypedTaskHandle:
        await self._invoke("pickup", _unwrap_ref(item_filter), parameter_types=["java.util.function.Predicate"])
        return self._new_task_handle("IFollowProcess.pickup")

    async def pickup(
        self,
        item_filter: RemoteRef | _RemoteWrapper,
        timeout: float | None = None,
        *,
        poll_interval: float = 0.1,
        startup_timeout: float = 1.0,
    ) -> TypedTaskResult:
        handle = await self.pickup_dispatch(item_filter)
        return await handle.wait(timeout, poll_interval=poll_interval, startup_timeout=startup_timeout)

    async def current_filter(self) -> RemoteRef | None:
        value = await self._invoke("currentFilter", parameter_types=[])
        if value is None:
            return None
        return _require_remote_ref(value, context="IFollowProcess.currentFilter")

    async def cancel(self) -> None:
        await self._invoke("cancel", parameter_types=[])


class WaypointRef(_RemoteWrapper):
    async def name(self) -> str:
        value = await self._invoke("getName", parameter_types=[])
        if not isinstance(value, str):
            raise BridgeError("BAD_RESPONSE", "Expected string from IWaypoint.getName", {"value": value})
        return value

    async def tag(self) -> str:
        value = await self._invoke("getTag", parameter_types=[])
        if not isinstance(value, str):
            raise BridgeError("BAD_RESPONSE", "Expected enum string from IWaypoint.getTag", {"value": value})
        return value

    async def creation_timestamp(self) -> int:
        return int(await self._invoke("getCreationTimestamp", parameter_types=[]))

    async def location(self) -> RemoteRef:
        value = await self._invoke("getLocation", parameter_types=[])
        return _require_remote_ref(value, context="IWaypoint.getLocation", expected_type=BETTER_BLOCK_POS_TYPE)


class WaypointCollectionRef(_BaritoneWrapper):
    async def add_waypoint(self, waypoint: WaypointRef | RemoteRef) -> None:
        await self._invoke("addWaypoint", _unwrap_ref(waypoint), parameter_types=[WAYPOINT_TYPE])

    async def remove_waypoint(self, waypoint: WaypointRef | RemoteRef) -> None:
        await self._invoke("removeWaypoint", _unwrap_ref(waypoint), parameter_types=[WAYPOINT_TYPE])

    async def most_recent_by_tag(self, tag: str | RemoteRef) -> WaypointRef | None:
        tag_ref = await self._baritone.waypoint_tag(tag) if isinstance(tag, str) else _unwrap_ref(tag)
        value = await self._invoke("getMostRecentByTag", tag_ref, parameter_types=[WAYPOINT_TAG_TYPE])
        if value is None:
            return None
        return WaypointRef(self._client, _require_remote_ref(value, context="IWaypointCollection.getMostRecentByTag", expected_type=WAYPOINT_TYPE))

    async def by_tag(self, tag: str | RemoteRef) -> list[WaypointRef]:
        tag_ref = await self._baritone.waypoint_tag(tag) if isinstance(tag, str) else _unwrap_ref(tag)
        value = await self._invoke("getByTag", tag_ref, parameter_types=[WAYPOINT_TAG_TYPE])
        refs = _require_remote_ref_list(value, context="IWaypointCollection.getByTag", expected_type=WAYPOINT_TYPE)
        return [WaypointRef(self._client, item) for item in refs]

    async def all(self) -> list[WaypointRef]:
        value = await self._invoke("getAllWaypoints", parameter_types=[])
        refs = _require_remote_ref_list(value, context="IWaypointCollection.getAllWaypoints", expected_type=WAYPOINT_TYPE)
        return [WaypointRef(self._client, item) for item in refs]


class CachedWorldRef(_BaritoneWrapper):
    async def region(self, region_x: int, region_z: int) -> RemoteRef | None:
        value = await self._invoke("getRegion", int(region_x), int(region_z), parameter_types=["int", "int"])
        if value is None:
            return None
        return _require_remote_ref(value, context="ICachedWorld.getRegion")

    async def queue_for_packing(self, chunk: RemoteRef | _RemoteWrapper) -> None:
        await self._invoke("queueForPacking", _unwrap_ref(chunk), parameter_types=["net.minecraft.class_2818"])

    async def is_cached(self, x: int, z: int) -> bool:
        return bool(await self._invoke("isCached", int(x), int(z), parameter_types=["int", "int"]))

    async def locations_of(
        self,
        block: BlockLike,
        maximum: int,
        center_x: int,
        center_z: int,
        max_region_distance_sq: int,
    ) -> list[RemoteRef]:
        value = await self._invoke(
            "getLocationsOf",
            coerce_block_id(block),
            int(maximum),
            int(center_x),
            int(center_z),
            int(max_region_distance_sq),
            parameter_types=["java.lang.String", "int", "int", "int", "int"],
        )
        return _require_remote_ref_list(value, context="ICachedWorld.getLocationsOf", expected_type="net.minecraft.class_2338")

    async def reload_all_from_disk(self) -> None:
        await self._invoke("reloadAllFromDisk", parameter_types=[])

    async def save(self) -> None:
        await self._invoke("save", parameter_types=[])


class WorldDataRef(_BaritoneWrapper):
    async def cached_world(self) -> CachedWorldRef:
        value = await self._invoke("getCachedWorld", parameter_types=[])
        ref = _require_remote_ref(value, context="IWorldData.getCachedWorld", expected_type=CACHED_WORLD_TYPE)
        return CachedWorldRef(self._client, self._baritone, ref)

    async def waypoints(self) -> WaypointCollectionRef:
        value = await self._invoke("getWaypoints", parameter_types=[])
        ref = _require_remote_ref(value, context="IWorldData.getWaypoints", expected_type=WAYPOINT_COLLECTION_TYPE)
        return WaypointCollectionRef(self._client, self._baritone, ref)


class WorldProviderRef(_BaritoneWrapper):
    async def current_world(self) -> WorldDataRef | None:
        value = await self._invoke("getCurrentWorld", parameter_types=[])
        if value is None:
            return None
        ref = _require_remote_ref(value, context="IWorldProvider.getCurrentWorld", expected_type=WORLD_DATA_TYPE)
        return WorldDataRef(self._client, self._baritone, ref)

    async def if_world_loaded(self, consumer: RemoteRef | _RemoteWrapper) -> None:
        await self._invoke("ifWorldLoaded", _unwrap_ref(consumer), parameter_types=["java.util.function.Consumer"])


class SelectionRef(_BaritoneWrapper):
    async def pos1(self) -> RemoteRef:
        value = await self._invoke("pos1", parameter_types=[])
        return _require_remote_ref(value, context="ISelection.pos1", expected_type=BETTER_BLOCK_POS_TYPE)

    async def pos2(self) -> RemoteRef:
        value = await self._invoke("pos2", parameter_types=[])
        return _require_remote_ref(value, context="ISelection.pos2", expected_type=BETTER_BLOCK_POS_TYPE)

    async def min(self) -> RemoteRef:
        value = await self._invoke("min", parameter_types=[])
        return _require_remote_ref(value, context="ISelection.min", expected_type=BETTER_BLOCK_POS_TYPE)

    async def max(self) -> RemoteRef:
        value = await self._invoke("max", parameter_types=[])
        return _require_remote_ref(value, context="ISelection.max", expected_type=BETTER_BLOCK_POS_TYPE)

    async def size(self) -> RemoteRef:
        value = await self._invoke("size", parameter_types=[])
        return _require_remote_ref(value, context="ISelection.size", expected_type="net.minecraft.class_2382")

    async def aabb(self) -> RemoteRef:
        value = await self._invoke("aabb", parameter_types=[])
        return _require_remote_ref(value, context="ISelection.aabb", expected_type="net.minecraft.class_238")

    async def expand(self, direction: str | RemoteRef, blocks: int) -> SelectionRef:
        direction_ref = await self._baritone.direction(direction) if isinstance(direction, str) else _unwrap_ref(direction)
        value = await self._invoke("expand", direction_ref, int(blocks), parameter_types=[DIRECTION_TYPE, "int"])
        return SelectionRef(
            self._client,
            self._baritone,
            _require_remote_ref(value, context="ISelection.expand", expected_type=SELECTION_TYPE),
        )

    async def contract(self, direction: str | RemoteRef, blocks: int) -> SelectionRef:
        direction_ref = await self._baritone.direction(direction) if isinstance(direction, str) else _unwrap_ref(direction)
        value = await self._invoke("contract", direction_ref, int(blocks), parameter_types=[DIRECTION_TYPE, "int"])
        return SelectionRef(
            self._client,
            self._baritone,
            _require_remote_ref(value, context="ISelection.contract", expected_type=SELECTION_TYPE),
        )

    async def shift(self, direction: str | RemoteRef, blocks: int) -> SelectionRef:
        direction_ref = await self._baritone.direction(direction) if isinstance(direction, str) else _unwrap_ref(direction)
        value = await self._invoke("shift", direction_ref, int(blocks), parameter_types=[DIRECTION_TYPE, "int"])
        return SelectionRef(
            self._client,
            self._baritone,
            _require_remote_ref(value, context="ISelection.shift", expected_type=SELECTION_TYPE),
        )


class SelectionManagerRef(_BaritoneWrapper):
    async def add_selection(self, selection: SelectionRef | RemoteRef) -> SelectionRef:
        value = await self._invoke("addSelection", _unwrap_ref(selection), parameter_types=[SELECTION_TYPE])
        return SelectionRef(
            self._client,
            self._baritone,
            _require_remote_ref(value, context="ISelectionManager.addSelection(selection)", expected_type=SELECTION_TYPE),
        )

    async def add_selection_points(
        self,
        pos1: tuple[int, int, int] | RemoteRef | _RemoteWrapper,
        pos2: tuple[int, int, int] | RemoteRef | _RemoteWrapper,
    ) -> SelectionRef:
        pos1_ref = await self._baritone._coerce_better_block_pos(pos1)
        pos2_ref = await self._baritone._coerce_better_block_pos(pos2)
        value = await self._invoke("addSelection", pos1_ref, pos2_ref, parameter_types=[BETTER_BLOCK_POS_TYPE, BETTER_BLOCK_POS_TYPE])
        return SelectionRef(
            self._client,
            self._baritone,
            _require_remote_ref(value, context="ISelectionManager.addSelection(pos1,pos2)", expected_type=SELECTION_TYPE),
        )

    async def remove_selection(self, selection: SelectionRef | RemoteRef) -> SelectionRef | None:
        value = await self._invoke("removeSelection", _unwrap_ref(selection), parameter_types=[SELECTION_TYPE])
        if value is None:
            return None
        return SelectionRef(
            self._client,
            self._baritone,
            _require_remote_ref(value, context="ISelectionManager.removeSelection", expected_type=SELECTION_TYPE),
        )

    async def remove_all(self) -> list[SelectionRef]:
        value = await self._invoke("removeAllSelections", parameter_types=[])
        refs = _require_remote_ref_list(value, context="ISelectionManager.removeAllSelections", expected_type=SELECTION_TYPE)
        return [SelectionRef(self._client, self._baritone, ref) for ref in refs]

    async def selections(self) -> list[SelectionRef]:
        value = await self._invoke("getSelections", parameter_types=[])
        refs = _require_remote_ref_list(value, context="ISelectionManager.getSelections", expected_type=SELECTION_TYPE)
        return [SelectionRef(self._client, self._baritone, ref) for ref in refs]

    async def only_selection(self) -> SelectionRef | None:
        value = await self._invoke("getOnlySelection", parameter_types=[])
        if value is None:
            return None
        return SelectionRef(
            self._client,
            self._baritone,
            _require_remote_ref(value, context="ISelectionManager.getOnlySelection", expected_type=SELECTION_TYPE),
        )

    async def last_selection(self) -> SelectionRef | None:
        value = await self._invoke("getLastSelection", parameter_types=[])
        if value is None:
            return None
        return SelectionRef(
            self._client,
            self._baritone,
            _require_remote_ref(value, context="ISelectionManager.getLastSelection", expected_type=SELECTION_TYPE),
        )

    async def expand(self, selection: SelectionRef | RemoteRef, direction: str | RemoteRef, blocks: int) -> SelectionRef:
        direction_ref = await self._baritone.direction(direction) if isinstance(direction, str) else _unwrap_ref(direction)
        value = await self._invoke(
            "expand",
            _unwrap_ref(selection),
            direction_ref,
            int(blocks),
            parameter_types=[SELECTION_TYPE, DIRECTION_TYPE, "int"],
        )
        return SelectionRef(
            self._client,
            self._baritone,
            _require_remote_ref(value, context="ISelectionManager.expand", expected_type=SELECTION_TYPE),
        )

    async def contract(self, selection: SelectionRef | RemoteRef, direction: str | RemoteRef, blocks: int) -> SelectionRef:
        direction_ref = await self._baritone.direction(direction) if isinstance(direction, str) else _unwrap_ref(direction)
        value = await self._invoke(
            "contract",
            _unwrap_ref(selection),
            direction_ref,
            int(blocks),
            parameter_types=[SELECTION_TYPE, DIRECTION_TYPE, "int"],
        )
        return SelectionRef(
            self._client,
            self._baritone,
            _require_remote_ref(value, context="ISelectionManager.contract", expected_type=SELECTION_TYPE),
        )

    async def shift(self, selection: SelectionRef | RemoteRef, direction: str | RemoteRef, blocks: int) -> SelectionRef:
        direction_ref = await self._baritone.direction(direction) if isinstance(direction, str) else _unwrap_ref(direction)
        value = await self._invoke(
            "shift",
            _unwrap_ref(selection),
            direction_ref,
            int(blocks),
            parameter_types=[SELECTION_TYPE, DIRECTION_TYPE, "int"],
        )
        return SelectionRef(
            self._client,
            self._baritone,
            _require_remote_ref(value, context="ISelectionManager.shift", expected_type=SELECTION_TYPE),
        )


class RegistryRef(_BaritoneWrapper):
    async def registered(self, entry: Any) -> bool:
        return bool(await self._invoke("registered", _unwrap_ref_or_value(entry), parameter_types=["java.lang.Object"]))

    async def register(self, entry: Any) -> bool:
        return bool(await self._invoke("register", _unwrap_ref_or_value(entry), parameter_types=["java.lang.Object"]))

    async def unregister(self, entry: Any) -> None:
        await self._invoke("unregister", _unwrap_ref_or_value(entry), parameter_types=["java.lang.Object"])

    async def values(self) -> list[Any]:
        stream = await self._invoke("stream", parameter_types=[])
        return await _coerce_array_like(self._client, stream, context="Registry.stream")

    async def descending_values(self) -> list[Any]:
        stream = await self._invoke("descendingStream", parameter_types=[])
        return await _coerce_array_like(self._client, stream, context="Registry.descendingStream")


class CommandRef(_BaritoneWrapper):
    async def execute(self, label: str, arg_consumer: RemoteRef | _RemoteWrapper) -> None:
        await self._invoke(
            "execute",
            str(label),
            _unwrap_ref(arg_consumer),
            parameter_types=["java.lang.String", "baritone.api.command.argument.IArgConsumer"],
        )

    async def tab_complete(self, label: str, arg_consumer: RemoteRef | _RemoteWrapper) -> list[str]:
        value = await self._invoke(
            "tabComplete",
            str(label),
            _unwrap_ref(arg_consumer),
            parameter_types=["java.lang.String", "baritone.api.command.argument.IArgConsumer"],
        )
        options = await _coerce_array_like(self._client, value, context="ICommand.tabComplete")
        return _require_string_list(options, context="ICommand.tabComplete")

    async def short_desc(self) -> str:
        value = await self._invoke("getShortDesc", parameter_types=[])
        if not isinstance(value, str):
            raise BridgeError("BAD_RESPONSE", "Expected string from ICommand.getShortDesc", {"value": value})
        return value

    async def long_desc(self) -> list[str]:
        value = await self._invoke("getLongDesc", parameter_types=[])
        return _require_string_list(value, context="ICommand.getLongDesc")

    async def names(self) -> list[str]:
        value = await self._invoke("getNames", parameter_types=[])
        return _require_string_list(value, context="ICommand.getNames")

    async def hidden_from_help(self) -> bool:
        return bool(await self._invoke("hiddenFromHelp", parameter_types=[]))


class ArgParserManagerRef(_BaritoneWrapper):
    async def registry(self) -> RegistryRef:
        value = await self._invoke("getRegistry", parameter_types=[])
        ref = _require_remote_ref(value, context="IArgParserManager.getRegistry", expected_type=REGISTRY_TYPE)
        return RegistryRef(self._client, self._baritone, ref)

    async def parser_stateless(self, target_type: str) -> RemoteRef | None:
        value = await self._invoke("getParserStateless", str(target_type), parameter_types=["java.lang.Class"])
        if value is None:
            return None
        return _require_remote_ref(value, context="IArgParserManager.getParserStateless")

    async def parse_stateless(self, target_type: str, argument: RemoteRef | _RemoteWrapper) -> Any:
        return await self._invoke(
            "parseStateless",
            str(target_type),
            _unwrap_ref(argument),
            parameter_types=["java.lang.Class", "baritone.api.command.argument.ICommandArgument"],
        )


class CommandSystemRef(_BaritoneWrapper):
    async def parser_manager(self) -> ArgParserManagerRef:
        value = await self._invoke("getParserManager", parameter_types=[])
        ref = _require_remote_ref(value, context="ICommandSystem.getParserManager", expected_type=ARG_PARSER_MANAGER_TYPE)
        return ArgParserManagerRef(self._client, self._baritone, ref)


class CommandManagerRef(_BaritoneWrapper):
    async def baritone(self) -> RemoteRef:
        value = await self._invoke("getBaritone", parameter_types=[])
        return _require_remote_ref(value, context="ICommandManager.getBaritone", expected_type=BARITONE_TYPE)

    async def registry(self) -> RegistryRef:
        value = await self._invoke("getRegistry", parameter_types=[])
        ref = _require_remote_ref(value, context="ICommandManager.getRegistry", expected_type=REGISTRY_TYPE)
        return RegistryRef(self._client, self._baritone, ref)

    async def command(self, name: str) -> CommandRef | None:
        value = await self._invoke("getCommand", str(name), parameter_types=["java.lang.String"])
        if value is None:
            return None
        return CommandRef(self._client, self._baritone, _require_remote_ref(value, context="ICommandManager.getCommand", expected_type=COMMAND_TYPE))

    async def execute(self, command_text: str) -> bool:
        return bool(await self._invoke("execute", str(command_text), parameter_types=["java.lang.String"]))

    async def tab_complete(self, command_text: str) -> list[str]:
        value = await self._invoke("tabComplete", str(command_text), parameter_types=["java.lang.String"])
        options = await _coerce_array_like(self._client, value, context="ICommandManager.tabComplete")
        return _require_string_list(options, context="ICommandManager.tabComplete")


class WorldScannerRef(_BaritoneWrapper):
    async def repack(self, player_context: PlayerContextRef | RemoteRef, chunk_radius: int | None = None) -> int:
        if chunk_radius is None:
            return int(await self._invoke("repack", _unwrap_ref(player_context), parameter_types=[PLAYER_CONTEXT_TYPE]))
        return int(
            await self._invoke(
                "repack",
                _unwrap_ref(player_context),
                int(chunk_radius),
                parameter_types=[PLAYER_CONTEXT_TYPE, "int"],
            )
        )

    async def scan_chunk_radius(
        self,
        player_context: PlayerContextRef | RemoteRef,
        block_lookup: RemoteRef | _RemoteWrapper,
        max_chunk_radius: int,
        y_level_threshold: int,
        max_results: int,
    ) -> list[RemoteRef]:
        value = await self._invoke(
            "scanChunkRadius",
            _unwrap_ref(player_context),
            _unwrap_ref(block_lookup),
            int(max_chunk_radius),
            int(y_level_threshold),
            int(max_results),
            parameter_types=[PLAYER_CONTEXT_TYPE, BLOCK_OPTIONAL_META_LOOKUP_TYPE, "int", "int", "int"],
        )
        return _require_remote_ref_list(value, context="IWorldScanner.scanChunkRadius", expected_type="net.minecraft.class_2338")


class SchematicRef(_BaritoneWrapper):
    async def width_x(self) -> int:
        return int(await self._invoke("widthX", parameter_types=[]))

    async def height_y(self) -> int:
        return int(await self._invoke("heightY", parameter_types=[]))

    async def length_z(self) -> int:
        return int(await self._invoke("lengthZ", parameter_types=[]))

    async def reset(self) -> None:
        await self._invoke("reset", parameter_types=[])


class StaticSchematicRef(SchematicRef):
    async def direct(self, x: int, y: int, z: int) -> RemoteRef:
        value = await self._invoke("getDirect", int(x), int(y), int(z), parameter_types=["int", "int", "int"])
        return _require_remote_ref(value, context="IStaticSchematic.getDirect")

    async def column(self, x: int, z: int) -> list[RemoteRef]:
        value = await self._invoke("getColumn", int(x), int(z), parameter_types=["int", "int"])
        return _require_remote_ref_list(value, context="IStaticSchematic.getColumn")


class FillSchematicRef(SchematicRef):
    async def block_optional_meta(self) -> RemoteRef:
        value = await self._invoke("getBom", parameter_types=[])
        return _require_remote_ref(value, context="FillSchematic.getBom", expected_type=BLOCK_OPTIONAL_META_TYPE)


class CompositeSchematicRef(SchematicRef):
    async def put(self, schematic: SchematicRef | RemoteRef, x: int, y: int, z: int) -> None:
        await self._invoke("put", _unwrap_ref(schematic), int(x), int(y), int(z), parameter_types=[SCHEMATIC_TYPE, "int", "int", "int"])


class MaskRef(_BaritoneWrapper):
    async def part_of_mask(self, x: int, y: int, z: int, current: RemoteRef | _RemoteWrapper) -> bool:
        return bool(
            await self._invoke(
                "partOfMask",
                int(x),
                int(y),
                int(z),
                _unwrap_ref(current),
                parameter_types=["int", "int", "int", "net.minecraft.class_2680"],
            )
        )

    async def width_x(self) -> int:
        return int(await self._invoke("widthX", parameter_types=[]))

    async def height_y(self) -> int:
        return int(await self._invoke("heightY", parameter_types=[]))

    async def length_z(self) -> int:
        return int(await self._invoke("lengthZ", parameter_types=[]))


class StaticMaskRef(MaskRef):
    async def part_of_mask_static(self, x: int, y: int, z: int) -> bool:
        return bool(await self._invoke("partOfMask", int(x), int(y), int(z), parameter_types=["int", "int", "int"]))

    async def compute(self) -> StaticMaskRef:
        value = await self._invoke("compute", parameter_types=[])
        return StaticMaskRef(
            self._client,
            self._baritone,
            _require_remote_ref(value, context="StaticMask.compute", expected_type=STATIC_MASK_TYPE),
        )


class SchematicFormatRef(_BaritoneWrapper):
    async def file_extensions(self) -> list[str]:
        value = await self._invoke("getFileExtensions", parameter_types=[])
        return _require_string_list(value, context="ISchematicFormat.getFileExtensions")

    async def is_file_type(self, path_or_file: str | Path | RemoteRef | _RemoteWrapper) -> bool:
        file_ref = await self._baritone.java_file(path_or_file) if isinstance(path_or_file, (str, Path)) else _unwrap_ref(path_or_file)
        return bool(await self._invoke("isFileType", file_ref, parameter_types=[JAVA_FILE_TYPE]))

    async def parse(self, input_stream: RemoteRef | _RemoteWrapper) -> StaticSchematicRef:
        value = await self._invoke("parse", _unwrap_ref(input_stream), parameter_types=["java.io.InputStream"])
        return StaticSchematicRef(
            self._client,
            self._baritone,
            _require_remote_ref(value, context="ISchematicFormat.parse", expected_type=STATIC_SCHEMATIC_TYPE),
        )


class SchematicSystemRef(_BaritoneWrapper):
    async def registry(self) -> RegistryRef:
        value = await self._invoke("getRegistry", parameter_types=[])
        ref = _require_remote_ref(value, context="ISchematicSystem.getRegistry", expected_type=REGISTRY_TYPE)
        return RegistryRef(self._client, self._baritone, ref)

    async def by_file(self, path_or_file: str | Path | RemoteRef | _RemoteWrapper) -> SchematicFormatRef | None:
        file_ref = await self._baritone.java_file(path_or_file) if isinstance(path_or_file, (str, Path)) else _unwrap_ref(path_or_file)
        value = await self._invoke("getByFile", file_ref, parameter_types=[JAVA_FILE_TYPE])
        if value is None:
            return None
        return SchematicFormatRef(
            self._client,
            self._baritone,
            _require_remote_ref(value, context="ISchematicSystem.getByFile", expected_type=SCHEMATIC_FORMAT_TYPE),
        )

    async def file_extensions(self) -> list[str]:
        value = await self._invoke("getFileExtensions", parameter_types=[])
        return _require_string_list(value, context="ISchematicSystem.getFileExtensions")


class PlayerContextRef(_BaritoneWrapper):
    async def world_data(self) -> WorldDataRef:
        value = await self._invoke("worldData", parameter_types=[])
        ref = _require_remote_ref(value, context="IPlayerContext.worldData", expected_type=WORLD_DATA_TYPE)
        return WorldDataRef(self._client, self._baritone, ref)

    async def minecraft(self) -> RemoteRef:
        value = await self._invoke("minecraft", parameter_types=[])
        return _require_remote_ref(value, context="IPlayerContext.minecraft")

    async def player(self) -> RemoteRef | None:
        value = await self._invoke("player", parameter_types=[])
        if value is None:
            return None
        return _require_remote_ref(value, context="IPlayerContext.player")

    async def player_controller(self) -> RemoteRef | None:
        value = await self._invoke("playerController", parameter_types=[])
        if value is None:
            return None
        return _require_remote_ref(value, context="IPlayerContext.playerController")

    async def world(self) -> RemoteRef | None:
        value = await self._invoke("world", parameter_types=[])
        if value is None:
            return None
        return _require_remote_ref(value, context="IPlayerContext.world")

    async def object_mouse_over(self) -> RemoteRef | None:
        value = await self._invoke("objectMouseOver", parameter_types=[])
        if value is None:
            return None
        return _require_remote_ref(value, context="IPlayerContext.objectMouseOver")

    async def viewer_pos(self) -> RemoteRef:
        value = await self._invoke("viewerPos", parameter_types=[])
        return _require_remote_ref(value, context="IPlayerContext.viewerPos", expected_type=BETTER_BLOCK_POS_TYPE)

    async def player_feet(self) -> RemoteRef:
        value = await self._invoke("playerFeet", parameter_types=[])
        return _require_remote_ref(value, context="IPlayerContext.playerFeet", expected_type=BETTER_BLOCK_POS_TYPE)

    async def selected_block(self) -> RemoteRef | None:
        value = await self._invoke("getSelectedBlock", parameter_types=[])
        if value is None:
            return None
        return _require_remote_ref(value, context="IPlayerContext.getSelectedBlock", expected_type="net.minecraft.class_2338")

    async def is_looking_at(self, block_pos: RemoteRef | _RemoteWrapper) -> bool:
        return bool(await self._invoke("isLookingAt", _unwrap_ref(block_pos), parameter_types=["net.minecraft.class_2338"]))


class InputOverrideHandlerRef(_BaritoneWrapper):
    async def is_input_forced_down(self, input_key: str | RemoteRef) -> bool:
        input_ref = await self._baritone.input_key(input_key) if isinstance(input_key, str) else _unwrap_ref(input_key)
        return bool(await self._invoke("isInputForcedDown", input_ref, parameter_types=[INPUT_TYPE]))

    async def set_input_force_state(self, input_key: str | RemoteRef, forced: bool) -> None:
        input_ref = await self._baritone.input_key(input_key) if isinstance(input_key, str) else _unwrap_ref(input_key)
        await self._invoke("setInputForceState", input_ref, bool(forced), parameter_types=[INPUT_TYPE, "boolean"])

    async def clear_all_keys(self) -> None:
        await self._invoke("clearAllKeys", parameter_types=[])


class GameEventListenerRef(_RemoteWrapper):
    async def on_tick(self, event: RemoteRef | _RemoteWrapper) -> None:
        await self._invoke("onTick", _unwrap_ref(event), parameter_types=["baritone.api.event.events.TickEvent"])

    async def on_post_tick(self, event: RemoteRef | _RemoteWrapper) -> None:
        await self._invoke("onPostTick", _unwrap_ref(event), parameter_types=["baritone.api.event.events.TickEvent"])

    async def on_path_event(self, event: RemoteRef | _RemoteWrapper) -> None:
        await self._invoke("onPathEvent", _unwrap_ref(event), parameter_types=["baritone.api.event.events.PathEvent"])

    async def on_player_death(self) -> None:
        await self._invoke("onPlayerDeath", parameter_types=[])


class EventBusRef(GameEventListenerRef):
    async def register_event_listener(self, listener: GameEventListenerRef | RemoteRef | _RemoteWrapper) -> None:
        await self._invoke("registerEventListener", _unwrap_ref(listener), parameter_types=[GAME_EVENT_LISTENER_TYPE])


class BaritoneProviderRef(_BaritoneWrapper):
    async def primary_baritone(self) -> RemoteRef:
        value = await self._invoke("getPrimaryBaritone", parameter_types=[])
        return _require_remote_ref(value, context="IBaritoneProvider.getPrimaryBaritone", expected_type=BARITONE_TYPE)

    async def all_baritones(self) -> list[RemoteRef]:
        value = await self._invoke("getAllBaritones", parameter_types=[])
        return _require_remote_ref_list(value, context="IBaritoneProvider.getAllBaritones", expected_type=BARITONE_TYPE)

    async def command_system(self) -> CommandSystemRef:
        value = await self._invoke("getCommandSystem", parameter_types=[])
        ref = _require_remote_ref(value, context="IBaritoneProvider.getCommandSystem", expected_type=COMMAND_SYSTEM_TYPE)
        return CommandSystemRef(self._client, self._baritone, ref)

    async def schematic_system(self) -> SchematicSystemRef:
        value = await self._invoke("getSchematicSystem", parameter_types=[])
        ref = _require_remote_ref(value, context="IBaritoneProvider.getSchematicSystem", expected_type=SCHEMATIC_SYSTEM_TYPE)
        return SchematicSystemRef(self._client, self._baritone, ref)

    async def world_scanner(self) -> WorldScannerRef:
        value = await self._invoke("getWorldScanner", parameter_types=[])
        ref = _require_remote_ref(value, context="IBaritoneProvider.getWorldScanner", expected_type=WORLD_SCANNER_TYPE)
        return WorldScannerRef(self._client, self._baritone, ref)


class GoalFactory:
    def __init__(self, baritone: "BaritoneNamespace") -> None:
        self._baritone = baritone

    async def axis(self) -> GoalRef:
        ref = await self._baritone._construct_ref("baritone.api.pathing.goals.GoalAxis", parameter_types=[], context="GoalAxis")
        return GoalRef(self._baritone._client, ref)

    async def block(self, x: int, y: int, z: int) -> GoalRef:
        ref = await self._baritone._construct_ref(
            "baritone.api.pathing.goals.GoalBlock",
            int(x),
            int(y),
            int(z),
            parameter_types=["int", "int", "int"],
            context="GoalBlock",
        )
        return GoalRef(self._baritone._client, ref)

    async def xz(self, x: int, z: int) -> GoalRef:
        ref = await self._baritone._construct_ref(
            "baritone.api.pathing.goals.GoalXZ",
            int(x),
            int(z),
            parameter_types=["int", "int"],
            context="GoalXZ",
        )
        return GoalRef(self._baritone._client, ref)

    async def y_level(self, y: int) -> GoalRef:
        ref = await self._baritone._construct_ref(
            "baritone.api.pathing.goals.GoalYLevel",
            int(y),
            parameter_types=["int"],
            context="GoalYLevel",
        )
        return GoalRef(self._baritone._client, ref)

    async def near(self, x: int, y: int, z: int, range_blocks: int) -> GoalRef:
        block_pos = await self._baritone.block_pos(x, y, z)
        ref = await self._baritone._construct_ref(
            "baritone.api.pathing.goals.GoalNear",
            block_pos,
            int(range_blocks),
            parameter_types=["net.minecraft.class_2338", "int"],
            context="GoalNear",
        )
        return GoalRef(self._baritone._client, ref)

    async def composite(self, *goals: GoalRef | RemoteRef) -> GoalRef:
        if not goals:
            raise ValueError("composite requires at least one goal")
        goal_refs = [_unwrap_goal(goal) for goal in goals]
        ref = await self._baritone._construct_ref(
            "baritone.api.pathing.goals.GoalComposite",
            goal_refs,
            parameter_types=[f"{GOAL_TYPE}[]"],
            context="GoalComposite",
        )
        return GoalRef(self._baritone._client, ref)

    async def inverted(self, goal: GoalRef | RemoteRef) -> GoalRef:
        ref = await self._baritone._construct_ref(
            "baritone.api.pathing.goals.GoalInverted",
            _unwrap_goal(goal),
            parameter_types=[GOAL_TYPE],
            context="GoalInverted",
        )
        return GoalRef(self._baritone._client, ref)

    async def run_away(
        self,
        distance: float,
        *positions: tuple[int, int, int],
        maintain_y: int | None = None,
    ) -> GoalRef:
        if not positions:
            raise ValueError("run_away requires at least one (x, y, z) tuple")
        pos_refs = [await self._baritone.block_pos(x, y, z) for x, y, z in positions]

        if maintain_y is None:
            ref = await self._baritone._construct_ref(
                "baritone.api.pathing.goals.GoalRunAway",
                float(distance),
                pos_refs,
                parameter_types=["double", "net.minecraft.class_2338[]"],
                context="GoalRunAway(distance,positions)",
            )
        else:
            ref = await self._baritone._construct_ref(
                "baritone.api.pathing.goals.GoalRunAway",
                float(distance),
                int(maintain_y),
                pos_refs,
                parameter_types=["double", "java.lang.Integer", "net.minecraft.class_2338[]"],
                context="GoalRunAway(distance,maintainY,positions)",
            )
        return GoalRef(self._baritone._client, ref)


class BaritoneNamespace:
    ROOT = "baritone"

    def __init__(self, client: "Client") -> None:
        self._client = client
        self.goals = GoalFactory(self)

    async def _invoke_root(
        self,
        method: str,
        *args: Any,
        parameter_types: list[str] | tuple[str, ...],
    ) -> Any:
        return await self._client.api_invoke(self.ROOT, method, *args, parameter_types=list(parameter_types))

    async def _invoke_root_ref(
        self,
        method: str,
        *,
        expected_type: str,
        parameter_types: list[str] | tuple[str, ...] = (),
    ) -> RemoteRef:
        value = await self._invoke_root(method, parameter_types=parameter_types)
        return _require_remote_ref(value, context=f"IBaritone.{method}", expected_type=expected_type)

    async def _construct_ref(
        self,
        type_name: str,
        *args: Any,
        parameter_types: list[str] | tuple[str, ...],
        context: str,
    ) -> RemoteRef:
        value = await self._client.api_construct(type_name, *args, parameter_types=list(parameter_types))
        return _require_remote_ref(value, context=context, expected_type=type_name)

    async def _invoke_type(
        self,
        type_name: str,
        method: str,
        *args: Any,
        parameter_types: list[str] | tuple[str, ...],
    ) -> Any:
        target = {"kind": "type", "name": type_name}
        return await self._client.api_invoke(target, method, *args, parameter_types=list(parameter_types))

    async def _enum_ref(self, enum_type: str, value: str, *, context: str) -> RemoteRef:
        normalized = value.strip().upper()
        if not normalized:
            raise ValueError(f"{context} requires a non-empty enum name")
        enum_value = await self._invoke_type(enum_type, "valueOf", normalized, parameter_types=["java.lang.String"])
        return _require_remote_ref(enum_value, context=context, expected_type=enum_type)

    async def _coerce_better_block_pos(self, value: tuple[int, int, int] | RemoteRef | _RemoteWrapper) -> RemoteRef:
        if isinstance(value, tuple):
            if len(value) != 3:
                raise ValueError("Expected (x, y, z) tuple for BetterBlockPos")
            x, y, z = value
            return await self.better_block_pos(int(x), int(y), int(z))
        return _unwrap_ref(value)

    async def metadata(self) -> dict[str, Any]:
        return await self._client.api_metadata_get(self.ROOT)

    async def pathing_behavior(self) -> PathingBehaviorRef:
        ref = await self._invoke_root_ref(
            "getPathingBehavior",
            expected_type="baritone.api.behavior.IPathingBehavior",
        )
        return PathingBehaviorRef(self._client, ref)

    async def custom_goal_process(self) -> CustomGoalProcessRef:
        ref = await self._invoke_root_ref(
            "getCustomGoalProcess",
            expected_type="baritone.api.process.ICustomGoalProcess",
        )
        return CustomGoalProcessRef(self._client, self, ref)

    async def get_to_block_process(self) -> GetToBlockProcessRef:
        ref = await self._invoke_root_ref(
            "getGetToBlockProcess",
            expected_type="baritone.api.process.IGetToBlockProcess",
        )
        return GetToBlockProcessRef(self._client, self, ref)

    async def mine_process(self) -> MineProcessRef:
        ref = await self._invoke_root_ref("getMineProcess", expected_type="baritone.api.process.IMineProcess")
        return MineProcessRef(self._client, self, ref)

    async def explore_process(self) -> ExploreProcessRef:
        ref = await self._invoke_root_ref("getExploreProcess", expected_type="baritone.api.process.IExploreProcess")
        return ExploreProcessRef(self._client, self, ref)

    async def builder_process(self) -> BuilderProcessRef:
        ref = await self._invoke_root_ref("getBuilderProcess", expected_type="baritone.api.process.IBuilderProcess")
        return BuilderProcessRef(self._client, self, ref)

    async def follow_process(self) -> FollowProcessRef:
        ref = await self._invoke_root_ref("getFollowProcess", expected_type="baritone.api.process.IFollowProcess")
        return FollowProcessRef(self._client, self, ref)

    async def world_provider(self) -> WorldProviderRef:
        ref = await self._invoke_root_ref("getWorldProvider", expected_type=WORLD_PROVIDER_TYPE)
        return WorldProviderRef(self._client, self, ref)

    async def selection_manager(self) -> SelectionManagerRef:
        ref = await self._invoke_root_ref("getSelectionManager", expected_type=SELECTION_MANAGER_TYPE)
        return SelectionManagerRef(self._client, self, ref)

    async def command_manager(self) -> CommandManagerRef:
        ref = await self._invoke_root_ref("getCommandManager", expected_type=COMMAND_MANAGER_TYPE)
        return CommandManagerRef(self._client, self, ref)

    async def player_context(self) -> PlayerContextRef:
        ref = await self._invoke_root_ref("getPlayerContext", expected_type=PLAYER_CONTEXT_TYPE)
        return PlayerContextRef(self._client, self, ref)

    async def input_override_handler(self) -> InputOverrideHandlerRef:
        ref = await self._invoke_root_ref("getInputOverrideHandler", expected_type=INPUT_OVERRIDE_HANDLER_TYPE)
        return InputOverrideHandlerRef(self._client, self, ref)

    async def game_event_handler(self) -> EventBusRef:
        ref = await self._invoke_root_ref("getGameEventHandler", expected_type=EVENT_BUS_TYPE)
        return EventBusRef(self._client, ref)

    async def provider(self) -> BaritoneProviderRef:
        value = await self._invoke_type("baritone.api.BaritoneAPI", "getProvider", parameter_types=[])
        ref = _require_remote_ref(value, context="BaritoneAPI.getProvider", expected_type=BARITONE_PROVIDER_TYPE)
        return BaritoneProviderRef(self._client, self, ref)

    async def command_system(self) -> CommandSystemRef:
        provider = await self.provider()
        return await provider.command_system()

    async def schematic_system(self) -> SchematicSystemRef:
        provider = await self.provider()
        return await provider.schematic_system()

    async def world_scanner(self) -> WorldScannerRef:
        provider = await self.provider()
        return await provider.world_scanner()

    async def block_pos(self, x: int, y: int, z: int) -> RemoteRef:
        return await self._construct_ref(
            "net.minecraft.class_2338",
            int(x),
            int(y),
            int(z),
            parameter_types=["int", "int", "int"],
            context="net.minecraft.class_2338",
        )

    async def better_block_pos(self, x: int, y: int, z: int) -> RemoteRef:
        return await self._construct_ref(
            BETTER_BLOCK_POS_TYPE,
            int(x),
            int(y),
            int(z),
            parameter_types=["int", "int", "int"],
            context=BETTER_BLOCK_POS_TYPE,
        )

    async def block_optional_meta(self, value: BlockLike) -> RemoteRef:
        return await self._construct_ref(
            BLOCK_OPTIONAL_META_TYPE,
            coerce_block_id(value),
            parameter_types=["java.lang.String"],
            context=BLOCK_OPTIONAL_META_TYPE,
        )

    async def block_optional_meta_lookup(self, *blocks: BlockLike) -> RemoteRef:
        if not blocks:
            raise ValueError("block_optional_meta_lookup requires at least one block id")
        names = [coerce_block_id(block) for block in blocks]
        return await self._construct_ref(
            BLOCK_OPTIONAL_META_LOOKUP_TYPE,
            names,
            parameter_types=["java.lang.String[]"],
            context=BLOCK_OPTIONAL_META_LOOKUP_TYPE,
        )

    async def direction(self, value: str) -> RemoteRef:
        return await self._enum_ref(DIRECTION_TYPE, value, context="Direction")

    async def axis_direction(self, value: str) -> RemoteRef:
        return await self._enum_ref(AXIS_TYPE, value, context="Direction.Axis")

    async def waypoint_tag(self, value: str) -> RemoteRef:
        return await self._enum_ref(WAYPOINT_TAG_TYPE, value, context="IWaypoint.Tag")

    async def input_key(self, value: str) -> RemoteRef:
        return await self._enum_ref(INPUT_TYPE, value, context="Input")

    async def java_path(self, value: str | Path) -> RemoteRef:
        path_target = {"kind": "type", "name": "java.nio.file.Path"}
        java_path = await self._client.api_invoke(
            path_target,
            "of",
            str(value),
            [],
            parameter_types=["java.lang.String", "java.lang.String[]"],
        )
        return _require_remote_ref(java_path, context="java.nio.file.Path.of", expected_type="java.nio.file.Path")

    async def java_file(self, value: str | Path | RemoteRef | _RemoteWrapper) -> RemoteRef:
        if isinstance(value, (RemoteRef, _RemoteWrapper)):
            return _unwrap_ref(value)
        return await self._construct_ref(
            JAVA_FILE_TYPE,
            str(value),
            parameter_types=["java.lang.String"],
            context=JAVA_FILE_TYPE,
        )

    async def waypoint(
        self,
        name: str,
        tag: str | RemoteRef,
        location: tuple[int, int, int] | RemoteRef | _RemoteWrapper,
        *,
        created_at: int | None = None,
    ) -> WaypointRef:
        tag_ref = await self.waypoint_tag(tag) if isinstance(tag, str) else _unwrap_ref(tag)
        location_ref = await self._coerce_better_block_pos(location)
        if created_at is None:
            ref = await self._construct_ref(
                "baritone.api.cache.Waypoint",
                str(name),
                tag_ref,
                location_ref,
                parameter_types=["java.lang.String", WAYPOINT_TAG_TYPE, BETTER_BLOCK_POS_TYPE],
                context="baritone.api.cache.Waypoint",
            )
        else:
            ref = await self._construct_ref(
                "baritone.api.cache.Waypoint",
                str(name),
                tag_ref,
                location_ref,
                int(created_at),
                parameter_types=["java.lang.String", WAYPOINT_TAG_TYPE, BETTER_BLOCK_POS_TYPE, "long"],
                context="baritone.api.cache.Waypoint",
            )
        return WaypointRef(self._client, ref)

    async def fill_schematic(self, width_x: int, height_y: int, length_z: int, block: BlockLike | RemoteRef | _RemoteWrapper) -> FillSchematicRef:
        block_arg = await self.block_optional_meta(block) if isinstance(block, str) else _unwrap_ref(block)
        ref = await self._construct_ref(
            FILL_SCHEMATIC_TYPE,
            int(width_x),
            int(height_y),
            int(length_z),
            block_arg,
            parameter_types=["int", "int", "int", BLOCK_OPTIONAL_META_TYPE],
            context=FILL_SCHEMATIC_TYPE,
        )
        return FillSchematicRef(self._client, self, ref)

    async def composite_schematic(self, width_x: int, height_y: int, length_z: int) -> CompositeSchematicRef:
        ref = await self._construct_ref(
            COMPOSITE_SCHEMATIC_TYPE,
            int(width_x),
            int(height_y),
            int(length_z),
            parameter_types=["int", "int", "int"],
            context=COMPOSITE_SCHEMATIC_TYPE,
        )
        return CompositeSchematicRef(self._client, self, ref)

    async def sphere_mask(self, width_x: int, height_y: int, length_z: int, *, hollow: bool = False) -> StaticMaskRef:
        ref = await self._construct_ref(
            SPHERE_MASK_TYPE,
            int(width_x),
            int(height_y),
            int(length_z),
            bool(hollow),
            parameter_types=["int", "int", "int", "boolean"],
            context=SPHERE_MASK_TYPE,
        )
        return StaticMaskRef(self._client, self, ref)

    async def cylinder_mask(
        self,
        width_x: int,
        height_y: int,
        length_z: int,
        *,
        hollow: bool = False,
        axis: str | RemoteRef = "Y",
    ) -> StaticMaskRef:
        axis_ref = await self.axis_direction(axis) if isinstance(axis, str) else _unwrap_ref(axis)
        ref = await self._construct_ref(
            CYLINDER_MASK_TYPE,
            int(width_x),
            int(height_y),
            int(length_z),
            bool(hollow),
            axis_ref,
            parameter_types=["int", "int", "int", "boolean", AXIS_TYPE],
            context=CYLINDER_MASK_TYPE,
        )
        return StaticMaskRef(self._client, self, ref)

    async def mask_schematic(self, schematic: SchematicRef | RemoteRef, mask: MaskRef | RemoteRef) -> SchematicRef:
        value = await self._invoke_type(
            "baritone.api.schematic.MaskSchematic",
            "create",
            _unwrap_ref(schematic),
            _unwrap_ref(mask),
            parameter_types=[SCHEMATIC_TYPE, MASK_TYPE],
        )
        ref = _require_remote_ref(value, context="MaskSchematic.create", expected_type="baritone.api.schematic.MaskSchematic")
        return SchematicRef(self._client, self, ref)

    async def open_click(self) -> None:
        await self._invoke_root("openClick", parameter_types=[])

    def _new_task_handle(self, action: str) -> TypedTaskHandle:
        handle_id = f"typed-{uuid4().hex}"

        async def _waiter(timeout: float | None, poll_interval: float, startup_timeout: float) -> TypedTaskResult:
            return await self._wait_for_pathing_idle(
                handle_id=handle_id,
                action=action,
                timeout=timeout,
                poll_interval=poll_interval,
                startup_timeout=startup_timeout,
            )

        return TypedTaskHandle(handle_id=handle_id, action=action, waiter=_waiter)

    async def _wait_for_pathing_idle(
        self,
        *,
        handle_id: str,
        action: str,
        timeout: float | None,
        poll_interval: float,
        startup_timeout: float,
    ) -> TypedTaskResult:
        loop = asyncio.get_running_loop()
        deadline = None if timeout is None else loop.time() + timeout
        startup_deadline = loop.time() + startup_timeout

        started = False
        behavior = await self.pathing_behavior()

        while True:
            if deadline is not None and loop.time() >= deadline:
                raise TimeoutError(f"Timed out waiting for typed Baritone task: {action}")

            pathing = await behavior.is_pathing()
            calculating = (await behavior.in_progress()) is not None
            busy = pathing or calculating

            if busy:
                started = True
            elif started or loop.time() >= startup_deadline:
                return TypedTaskResult(
                    handle_id=handle_id,
                    action=action,
                    started=started,
                    pathing=False,
                    calculating=False,
                    has_path=await behavior.has_path(),
                    goal=await behavior.goal(),
                )

            await asyncio.sleep(poll_interval)


__all__ = [
    "ArgParserManagerRef",
    "BaritoneNamespace",
    "BaritoneProviderRef",
    "BuilderProcessRef",
    "CachedWorldRef",
    "CommandManagerRef",
    "CommandRef",
    "CommandSystemRef",
    "CompositeSchematicRef",
    "CustomGoalProcessRef",
    "EventBusRef",
    "ExploreProcessRef",
    "FillSchematicRef",
    "FollowProcessRef",
    "GameEventListenerRef",
    "GetToBlockProcessRef",
    "GoalFactory",
    "GoalRef",
    "InputOverrideHandlerRef",
    "MaskRef",
    "MineProcessRef",
    "PathCalculationResultRef",
    "PathExecutorRef",
    "PathFinderRef",
    "PathRef",
    "PathingBehaviorRef",
    "PlayerContextRef",
    "RegistryRef",
    "SchematicFormatRef",
    "SchematicRef",
    "SchematicSystemRef",
    "SelectionManagerRef",
    "SelectionRef",
    "StaticMaskRef",
    "StaticSchematicRef",
    "TypedTaskHandle",
    "TypedTaskResult",
    "WaypointCollectionRef",
    "WaypointRef",
    "WorldDataRef",
    "WorldProviderRef",
    "WorldScannerRef",
]
