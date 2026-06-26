"""Tests for local Ollama compatibility behavior."""

from unittest import mock

from corecoder.llm import LLM


class _Delta:
    def __init__(self, content=None, tool_calls=None):
        self.content = content
        self.tool_calls = tool_calls


class _Choice:
    def __init__(self, delta):
        self.delta = delta


class _Usage:
    prompt_tokens = 10
    completion_tokens = 5


class _Chunk:
    def __init__(self, content=None, usage=None):
        self.choices = [_Choice(_Delta(content=content))] if content else []
        self.usage = usage


def _make_stream(contents):
    chunks = [_Chunk(content=item) for item in contents]
    chunks.append(_Chunk(usage=_Usage()))
    return iter(chunks)


def _make_llm_with_stream(contents):
    llm = LLM.__new__(LLM)
    llm.model = "qwen2.5-coder:7b"
    llm.extra = {}
    llm.total_prompt_tokens = 0
    llm.total_completion_tokens = 0
    llm._call_with_retry = mock.MagicMock(return_value=_make_stream(contents))
    return llm


def test_plain_json_text_becomes_tool_call():
    llm = _make_llm_with_stream([
        '{"name":"read_file","arguments":{"file_path":"corecoder/config.py"}}'
    ])

    result = llm.chat(messages=[{"role": "user", "content": "read config"}])
    assert result.content == ""
    assert len(result.tool_calls) == 1
    assert result.tool_calls[0].name == "read_file"
    assert result.tool_calls[0].arguments == {
        "file_path": "corecoder/config.py"
    }

def test_markdown_json_text_becomes_tool_call():
    llm = _make_llm_with_stream([
        '```json\n{"name":"read_file","arguments":{"file_path":"corecoder/config.py"}}\n```'
    ])

    result = llm.chat(messages=[{"role": "user", "content": "read config"}])
    assert result.content == ""
    assert len(result.tool_calls) == 1
    assert result.tool_calls[0].name == "read_file"
    assert result.tool_calls[0].arguments == {
        "file_path": "corecoder/config.py"
    }

def test_normal_text_remains_normal_text():
    llm = _make_llm_with_stream(["普通回答，不调用工具。"])
    result = llm.chat(messages=[{"role": "user", "content": "hello"}])
    assert result.content == "普通回答，不调用工具。"
    assert result.tool_calls == []
