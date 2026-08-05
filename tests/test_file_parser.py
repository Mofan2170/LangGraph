import io
import json

import pandas as pd
import pytest

from app.utils.file_parser import (
    MAX_PARSED_CHARS,
    infer_task_type_by_suffix,
    parse_file_by_suffix,
)


def test_text_parser_supports_utf8_and_gb18030() -> None:
    assert parse_file_by_suffix("你好".encode(), ".txt") == "你好"
    assert parse_file_by_suffix("中文数据".encode("gb18030"), "txt") == "中文数据"


def test_text_parser_truncates_long_content() -> None:
    result = parse_file_by_suffix(b"x" * (MAX_PARSED_CHARS + 100), "py")

    assert len(result) == MAX_PARSED_CHARS
    assert result.endswith("内容过长，已截断。")


def test_csv_parser_returns_a_compact_summary() -> None:
    result = parse_file_by_suffix(b"name,score\nAlice,90\nBob,85\n", "csv")

    assert "name, score" in result
    assert "2 行，2 列" in result
    assert "Alice" in result


def test_xlsx_parser_lists_sheets() -> None:
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        pd.DataFrame({"score": [90]}).to_excel(
            writer,
            index=False,
            sheet_name="成绩",
        )

    result = parse_file_by_suffix(buffer.getvalue(), "xlsx")

    assert "成绩" in result
    assert "1 行，1 列" in result


def test_notebook_parser_extracts_code_and_plain_text_output() -> None:
    notebook = {
        "cells": [
            {
                "cell_type": "code",
                "source": ["answer = 42"],
                "outputs": [{"data": {"text/plain": ["42"]}}],
            }
        ]
    }

    result = parse_file_by_suffix(json.dumps(notebook).encode(), "ipynb")

    assert "answer = 42" in result
    assert "Output Cell 1" in result


@pytest.mark.parametrize(
    ("suffix", "expected"),
    [
        ("py", "analyze_code"),
        ("CSV", "analyze_data"),
        (".md", "explain_question"),
    ],
)
def test_task_type_inference(suffix: str, expected: str) -> None:
    assert infer_task_type_by_suffix(suffix) == expected


def test_unsupported_file_type_is_rejected() -> None:
    with pytest.raises(ValueError, match="暂不支持"):
        parse_file_by_suffix(b"binary", "exe")
