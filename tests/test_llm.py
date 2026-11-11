import pytest
import httpx
from src.llm import LlmClient

@pytest.mark.asyncio
async def test_llm_client_mock():
    def handler(request: httpx.Request):
        payload = {
            "choices": [
                {
                    "message": {
                        "content": "Análise acadêmica estruturada com rigor dogmático."
                    }
                }
            ]
        }
        return httpx.Response(200, json=payload)

    transport = httpx.MockTransport(handler)
    client = LlmClient(api_key="sk-mock-key", transport=transport)

    resp = await client.generate(
        model="anthropic/claude-fable-5.2",
        prompt="Escreva a seção teórica."
    )
    assert "Análise acadêmica estruturada" in resp

@pytest.mark.asyncio
async def test_llm_client_offline_fallback():
    # Sem chave de API (string vazia), deve retornar modo offline sem erro
    client = LlmClient(api_key="")
    resp = await client.generate(
        model="openai/gpt-6-astra",
        prompt="Problema de pesquisa"
    )
    assert "[Modo Offline Heurístico]" in resp
