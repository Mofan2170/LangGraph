"""Convert supported uploads into compact text for model analysis."""

import io
import json
from collections.abc import Callable
from typing import Any

import pandas as pd

MAX_PARSED_CHARS = 30_000
TRUNCATION_NOTICE = "\n\n……内容过长，已截断。"


def _truncate(text: str) -> str:
    if len(text) <= MAX_PARSED_CHARS:
        return text
    keep_chars = MAX_PARSED_CHARS - len(TRUNCATION_NOTICE)
    return text[:keep_chars] + TRUNCATION_NOTICE


def _decode_text(file_bytes: bytes) -> str:
    for encoding in ("utf-8-sig", "gb18030"):
        try:
            return file_bytes.decode(encoding)
        except UnicodeDecodeError:
            continue
    return file_bytes.decode("utf-8", errors="replace")


def _join_text(value: Any) -> str:
    if isinstance(value, list):
        return "".join(str(item) for item in value)
    return "" if value is None else str(value)


def parse_text_file(file_bytes: bytes) -> str:
    return _decode_text(file_bytes)


def parse_csv_file(file_bytes: bytes) -> str:
    last_encoding_error: UnicodeDecodeError | None = None
    dataframe = None

    for encoding in ("utf-8-sig", "gb18030"):
        try:
            dataframe = pd.read_csv(io.BytesIO(file_bytes), encoding=encoding)
            break
        except UnicodeDecodeError as exc:
            last_encoding_error = exc

    if dataframe is None:
        raise ValueError("CSV 文件编码无法识别") from last_encoding_error

    preview = dataframe.head(5).to_string(index=False)
    columns = ", ".join(dataframe.columns.astype(str).tolist())
    return f"""这是一个 CSV 数据文件。

字段名：
{columns}

数据规模：
数据共有 {dataframe.shape[0]} 行，{dataframe.shape[1]} 列

前 5 行预览：
{preview}
"""


def parse_xlsx_file(file_bytes: bytes) -> str:
    with pd.ExcelFile(io.BytesIO(file_bytes)) as workbook:
        sheet_names = workbook.sheet_names
        parts = [f"这是一个 Excel 文件，共有 {len(sheet_names)} 个工作表。"]
        parts.append("工作表名称：" + ", ".join(sheet_names))

        for sheet_name in sheet_names[:3]:
            dataframe = pd.read_excel(workbook, sheet_name=sheet_name)
            parts.extend(
                [
                    f"\n[Sheet: {sheet_name}]",
                    f"行列规模：{dataframe.shape[0]} 行，{dataframe.shape[1]} 列",
                    "字段名：" + ", ".join(dataframe.columns.astype(str).tolist()),
                    "前 5 行预览：",
                    dataframe.head(5).to_string(index=False),
                ]
            )

    return "\n".join(parts)


def parse_ipynb_file(file_bytes: bytes) -> str:
    try:
        notebook = json.loads(file_bytes.decode("utf-8-sig"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("Notebook 不是有效的 UTF-8 JSON 文件") from exc

    if not isinstance(notebook, dict):
        raise ValueError("Notebook 顶层结构无效")

    cells = notebook.get("cells", [])
    if not isinstance(cells, list):
        raise ValueError("Notebook cells 字段无效")

    parts = [f"这是一个 Jupyter Notebook 文件，共有 {len(cells)} 个单元格。"]
    for index, cell in enumerate(cells[:80], start=1):
        if not isinstance(cell, dict):
            continue

        cell_type = cell.get("cell_type", "unknown")
        source = _join_text(cell.get("source", []))
        if cell_type == "markdown":
            parts.append(f"\n[Markdown Cell {index}]\n{source}")
            continue
        if cell_type != "code":
            continue

        parts.append(f"\n[Code Cell {index}]\n{source}")
        output_texts: list[str] = []
        outputs = cell.get("outputs", [])
        if not isinstance(outputs, list):
            continue

        for output in outputs[:3]:
            if not isinstance(output, dict):
                continue
            if "text" in output:
                output_texts.append(_join_text(output["text"]))
                continue
            data = output.get("data", {})
            if isinstance(data, dict) and "text/plain" in data:
                output_texts.append(_join_text(data["text/plain"]))

        if output_texts:
            parts.append(f"[Output Cell {index}]\n" + "\n".join(output_texts))

    return "\n".join(parts)


PARSER_REGISTRY: dict[str, Callable[[bytes], str]] = {
    "py": parse_text_file,
    "r": parse_text_file,
    "txt": parse_text_file,
    "md": parse_text_file,
    "sql": parse_text_file,
    "json": parse_text_file,
    "csv": parse_csv_file,
    "xlsx": parse_xlsx_file,
    "ipynb": parse_ipynb_file,
}

SUPPORTED_SUFFIXES = tuple(sorted(PARSER_REGISTRY))


def parse_file_by_suffix(file_bytes: bytes, suffix: str) -> str:
    normalized_suffix = suffix.lower().strip().lstrip(".")
    parser = PARSER_REGISTRY.get(normalized_suffix)
    if parser is None:
        raise ValueError(f"暂不支持的文件类型: .{normalized_suffix}")
    return _truncate(parser(file_bytes))


def infer_task_type_by_suffix(suffix: str) -> str:
    normalized_suffix = suffix.lower().strip().lstrip(".")
    if normalized_suffix in {"py", "r", "ipynb"}:
        return "analyze_code"
    if normalized_suffix in {"csv", "xlsx"}:
        return "analyze_data"
    if normalized_suffix in {"txt", "md", "sql", "json"}:
        return "explain_question"
    raise ValueError(f"无法根据后缀推断任务类型: .{normalized_suffix}")
