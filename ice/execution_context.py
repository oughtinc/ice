# I am an async thread-safe way to store high-level information about the
# current execution.
# I'm specific about my parameters because it would be too easy to hang all
# sorts of information off me, when all I'm supposed to do is know about the
# original parameters an execution was started with.
from contextvars import ContextVar
from typing import Optional
from typing import TypedDict

from ice.utils import make_id


class ExecutionContext(TypedDict):
    id: str
    document_id: Optional[str]
    task: str


__execution_context = ContextVar[ExecutionContext]("execution_context")


def new_context(*, document_id: Optional[str], task: str) -> None:
    context: ExecutionContext = {
        "id": make_id(),
        "document_id": document_id,
        "task": task,
    }
    global __execution_context
    __execution_context.set(context)


def context() -> ExecutionContext:
    return __execution_context.get()
