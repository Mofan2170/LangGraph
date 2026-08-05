"""FastAPI entry point for the DataMentor AI demo."""

import logging

from fastapi import FastAPI, File, HTTPException, UploadFile, status
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel, ConfigDict, Field

from app.graph import graph
from app.state import AgentState
from app.utils.file_parser import infer_task_type_by_suffix, parse_file_by_suffix

logger = logging.getLogger(__name__)
MAX_UPLOAD_BYTES = 5 * 1024 * 1024

app = FastAPI(
    title="DataMentor AI API",
    description="A LangGraph routing demo for learning and file analysis.",
    version="1.0.0",
)


class ChatRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    user_input: str = Field(min_length=1, max_length=20_000)


class ChatResponse(BaseModel):
    task_type: str
    result: str


def _invoke_graph(initial_state: AgentState) -> AgentState:
    try:
        return graph.invoke(initial_state)
    except Exception as exc:
        logger.exception("Graph execution failed")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="模型服务暂时不可用，请检查配置后重试",
        ) from exc


def _to_response(result: AgentState) -> ChatResponse:
    return ChatResponse(
        task_type=result.get("task_type", ""),
        result=result.get("result", ""),
    )


@app.get("/", tags=["meta"])
def root() -> dict[str, str]:
    return {"message": "DataMentor AI API is running"}


@app.post("/analyze", response_model=ChatResponse, tags=["analysis"])
def analyze(request: ChatRequest) -> ChatResponse:
    result = _invoke_graph({"user_input": request.user_input})
    return _to_response(result)


@app.post("/upload", response_model=ChatResponse, tags=["analysis"])
async def upload_file(file: UploadFile = File(...)) -> ChatResponse:
    filename = file.filename or ""
    if not filename or "." not in filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="文件名无效，必须包含后缀",
        )

    suffix = filename.rsplit(".", 1)[-1].lower()
    try:
        file_bytes = await file.read(MAX_UPLOAD_BYTES + 1)
    finally:
        await file.close()

    if not file_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="上传文件不能为空",
        )
    if len(file_bytes) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail="上传文件不能超过 5 MB",
        )

    try:
        file_content = parse_file_by_suffix(file_bytes, suffix)
        task_type = infer_task_type_by_suffix(suffix)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        logger.info("Upload parsing failed for %s: %s", filename, type(exc).__name__)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="文件内容无法解析，请检查格式是否正确",
        ) from exc

    if task_type == "analyze_code":
        user_input = f"请分析这个 .{suffix} 代码文件"
    elif task_type == "analyze_data":
        user_input = f"请分析这个 .{suffix} 数据文件"
    else:
        user_input = f"请分析这个 .{suffix} 文本文件"

    initial_state: AgentState = {
        "user_input": user_input,
        "task_type": task_type,
        "file_name": filename,
        "file_type": suffix,
        "file_content": file_content,
    }
    result = await run_in_threadpool(_invoke_graph, initial_state)
    return _to_response(result)
