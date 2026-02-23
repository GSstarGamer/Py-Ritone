from __future__ import annotations

import asyncio
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, Awaitable, Callable
from uuid import uuid4

from .models import BridgeError, RemoteRef

if TYPE_CHECKING:
    from .client_async import Client


GOAL_TYPE = "baritone.api.pathing.goals.Goal"


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


class _ProcessRef(_RemoteWrapper):
    def __init__(self, client: "Client", baritone: "BaritoneNamespace", ref: RemoteRef) -> None:
        super().__init__(client, ref)
        self._baritone = baritone

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
    async def get_to_block_dispatch(self, block: RemoteRef | _RemoteWrapper | str) -> TypedTaskHandle:
        block_arg = await self._baritone.block_optional_meta(block) if isinstance(block, str) else _unwrap_ref(block)
        await self._invoke("getToBlock", block_arg, parameter_types=["baritone.api.utils.BlockOptionalMeta"])
        return self._new_task_handle("IGetToBlockProcess.getToBlock")

    async def get_to_block(
        self,
        block: RemoteRef | _RemoteWrapper | str,
        timeout: float | None = None,
        *,
        poll_interval: float = 0.1,
        startup_timeout: float = 1.0,
    ) -> TypedTaskResult:
        handle = await self.get_to_block_dispatch(block)
        return await handle.wait(timeout, poll_interval=poll_interval, startup_timeout=startup_timeout)


class MineProcessRef(_ProcessRef):
    async def mine_by_name_dispatch(self, quantity: int, *block_names: str) -> TypedTaskHandle:
        if not block_names:
            raise ValueError("mine_by_name_dispatch requires at least one block name")
        await self._invoke(
            "mineByName",
            int(quantity),
            list(block_names),
            parameter_types=["int", "java.lang.String[]"],
        )
        return self._new_task_handle("IMineProcess.mineByName")

    async def mine_by_name(
        self,
        quantity: int,
        *block_names: str,
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

    async def block_pos(self, x: int, y: int, z: int) -> RemoteRef:
        return await self._construct_ref(
            "net.minecraft.class_2338",
            int(x),
            int(y),
            int(z),
            parameter_types=["int", "int", "int"],
            context="net.minecraft.class_2338",
        )

    async def block_optional_meta(self, value: str) -> RemoteRef:
        return await self._construct_ref(
            "baritone.api.utils.BlockOptionalMeta",
            value,
            parameter_types=["java.lang.String"],
            context="baritone.api.utils.BlockOptionalMeta",
        )

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
    "BaritoneNamespace",
    "BuilderProcessRef",
    "CustomGoalProcessRef",
    "ExploreProcessRef",
    "FollowProcessRef",
    "GetToBlockProcessRef",
    "GoalFactory",
    "GoalRef",
    "MineProcessRef",
    "PathCalculationResultRef",
    "PathExecutorRef",
    "PathFinderRef",
    "PathRef",
    "PathingBehaviorRef",
    "TypedTaskHandle",
    "TypedTaskResult",
]
