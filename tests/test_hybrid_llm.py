"""Tests for cloud-to-local hybrid LLM fallback."""

from unittest import mock

import pytest
from openai import APIConnectionError, BadRequestError

from corecoder.llm import HybridLLM, LLMResponse


def _fake_llm(model, response=None, error=None):
    llm = mock.MagicMock()
    llm.model = model
    llm.total_prompt_tokens = 0
    llm.total_completion_tokens = 0
    llm.estimated_cost = None

    if error:
        llm.chat.side_effect = error
    else:
        llm.chat.return_value = response or LLMResponse(content="ok")

    return llm


def test_hybrid_uses_primary_when_cloud_succeeds():
    cloud = _fake_llm("cloud-model", LLMResponse(content="cloud answer"))
    local = _fake_llm("local-model", LLMResponse(content="local answer"))

    llm = HybridLLM(cloud, local)
    result = llm.chat([{"role": "user", "content": "hi"}])

    assert result.content == "cloud answer"
    assert llm.last_provider == "cloud"
    local.chat.assert_not_called()


def test_hybrid_falls_back_on_connection_error():
    cloud = _fake_llm(

        "cloud-model",

        error=APIConnectionError(request=mock.MagicMock()),

    )

    local = _fake_llm("local-model", LLMResponse(content="local answer"))

    llm = HybridLLM(cloud, local)

    result = llm.chat([{"role": "user", "content": "hi"}])

    assert result.content == "local answer"

    assert llm.last_provider == "local"

    local.chat.assert_called_once()

def test_hybrid_does_not_fallback_on_bad_request():

    cloud = _fake_llm(

        "cloud-model",

        error=BadRequestError(

            message="bad request",

            response=mock.MagicMock(status_code=400),

            body={},

        ),

    )

    local = _fake_llm("local-model", LLMResponse(content="local answer"))

    llm = HybridLLM(cloud, local)

    with pytest.raises(BadRequestError):

        llm.chat([{"role": "user", "content": "hi"}])

    local.chat.assert_not_called()
