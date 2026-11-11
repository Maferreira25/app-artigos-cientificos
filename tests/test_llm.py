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

@pytest.mark.asyncio
async def test_llm_client_null_content_and_refusal():
    def handler(request: httpx.Request):
        payload = {
            "choices": [
                {
                    "message": {
                        "content": None,
                        "refusal": "Solicitação acadêmica com conteúdo sensível recusada pelo filtro do modelo."
                    }
                }
            ]
        }
        return httpx.Response(200, json=payload)

    transport = httpx.MockTransport(handler)
    client = LlmClient(api_key="sk-mock-key", transport=transport)

    resp = await client.generate(
        model="deepseek/deepseek-chat",
        prompt="Auditoria adversarial"
    )
    assert "recusada pelo filtro" in resp

@pytest.mark.asyncio
async def test_llm_client_strip_thinking_tags():
    def handler(request: httpx.Request):
        payload = {
            "choices": [
                {
                    "message": {
                        "content": "<think>\nPlanejamento do texto aqui...\n</think>\nTexto acadêmico finalizado sem tags internas."
                    }
                }
            ]
        }
        return httpx.Response(200, json=payload)

    transport = httpx.MockTransport(handler)
    client = LlmClient(api_key="sk-mock-key", transport=transport)

    resp = await client.generate(
        model="deepseek/deepseek-r1-0528",
        prompt="Raciocínio com CoT"
    )
    assert "<think>" not in resp
    assert "</think>" not in resp
    assert resp == "Texto acadêmico finalizado sem tags internas."

@pytest.mark.asyncio
async def test_llm_client_fallback_model_retry():
    tentativas = []
    def handler(request: httpx.Request):
        import json
        body = json.loads(request.content.decode("utf-8"))
        modelo_chamado = body["model"]
        tentativas.append(modelo_chamado)
        
        if modelo_chamado == "openai/gpt-6-astra":
            # Primeira tentativa falha com erro 503
            return httpx.Response(503, json={"error": "Model overloaded"})
        else:
            # Segunda tentativa com modelo fallback tem sucesso
            return httpx.Response(200, json={
                "choices": [{"message": {"content": "Resposta bem-sucedida do modelo fallback."}}]
            })

    transport = httpx.MockTransport(handler)
    client = LlmClient(api_key="sk-mock-key", transport=transport)

    resp = await client.generate(
        model="openai/gpt-6-astra",
        prompt="Pergunta epistemológica",
        fallback_model="google/gemini-4-argon"
    )
    assert "Resposta bem-sucedida do modelo fallback." in resp
    assert tentativas == ["openai/gpt-6-astra", "google/gemini-4-argon"]
