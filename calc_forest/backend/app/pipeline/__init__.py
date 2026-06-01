from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Generic, TypeVar

T = TypeVar("T")


class NodeStatus(str, Enum):
    SUCCESS = "success"
    SKIPPED = "skipped"
    FAILED = "failed"


class NodeResult:
    def __init__(
        self,
        status: NodeStatus,
        output: dict[str, Any] | None = None,
        error: str | None = None,
    ):
        self.status = status
        self.output = output or {}
        self.error = error

    @property
    def success(self) -> bool:
        return self.status == NodeStatus.SUCCESS


class BaseNode(ABC):
    @property
    @abstractmethod
    def name(self) -> str: ...

    @property
    def description(self) -> str:
        return ""

    @abstractmethod
    async def execute(self, context: dict[str, Any]) -> NodeResult:
        ...

    async def should_run(self, context: dict[str, Any]) -> bool:
        return True


class Pipeline:
    def __init__(self, name: str, *, stop_on_fail: bool = True):
        self.name = name
        self.stop_on_fail = stop_on_fail
        self._nodes: list[BaseNode] = []

    def add(self, node: BaseNode) -> "Pipeline":
        self._nodes.append(node)
        return self

    async def run(self, context: dict[str, Any] | None = None) -> dict[str, Any]:
        ctx = dict(context or {})
        ctx.setdefault("_results", {})
        ctx.setdefault("_errors", [])

        for node in self._nodes:
            try:
                if not await node.should_run(ctx):
                    ctx["_results"][node.name] = NodeResult(NodeStatus.SKIPPED)
                    continue
                result = await node.execute(ctx)
                ctx["_results"][node.name] = result
                if result.output:
                    ctx.update(result.output)
                if not result.success:
                    ctx["_errors"].append(
                        {"node": node.name, "error": result.error}
                    )
                    if self.stop_on_fail:
                        break
            except Exception as exc:
                ctx["_results"][node.name] = NodeResult(
                    NodeStatus.FAILED, error=str(exc)
                )
                ctx["_errors"].append({"node": node.name, "error": str(exc)})
                if self.stop_on_fail:
                    break

        return ctx
