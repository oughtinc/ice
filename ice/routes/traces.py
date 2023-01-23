from pathlib import Path
from typing import Optional

from fastapi import APIRouter
from fastapi import Header
from fastapi import HTTPException
from starlette.responses import FileResponse
from starlette.responses import PlainTextResponse

from ice.trace import traces_dir

router = APIRouter(prefix="/api/traces", tags=["traces"])


@router.get("/")
async def list_traces():
    # e.g. if trace_dir contains files trace1/trace.jsonl, trace2/trace.jsonl, other.txt,
    # return ["trace1", "trace2"]
    return sorted(
        folder.name
        for folder in traces_dir.iterdir()
        if folder.is_dir() and (folder / "trace.jsonl").exists()
    )


@router.get("/{trace_id}/trace.jsonl")
async def get_trace(trace_id: str, Range: Optional[str] = Header(None)):
    """
    Return the contents of the trace file with the given trace_id.
    Uses the Range header to support partial content requests.
    This route comes before the StaticFiles mounted at /api/traces/ so it takes precedence.
    We need this because StaticFiles doesn't support Range headers.
    We still have the StaticFiles to support HEAD requests used for getting Content-length.
    """
    return get_file(traces_dir / trace_id / "trace.jsonl", Range)


@router.get("/{trace_id}/block_{block_id}.jsonl")
async def get_block(trace_id: str, block_id: int, Range: Optional[str] = Header(None)):
    return get_file(traces_dir / trace_id / f"block_{block_id}.jsonl", Range)


def get_file(path: Path, Range: Optional[str]):
    if not path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    if Range is None:
        return FileResponse(path)

    try:
        start, end = map(int, Range.removeprefix("bytes=").split("-"))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid Range header")

    with open(path, "rb") as f:
        f.seek(start)
        length = end - start + 1
        byts = f.read(length)
        text = byts.decode("utf-8", errors="ignore")
        return PlainTextResponse(text, status_code=206)
