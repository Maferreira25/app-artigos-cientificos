import pytest
import httpx
from src.mcp_client import JurisprudenciaMcpClient
from src.rag_store import RagStore

@pytest.mark.asyncio
async def test_mcp_client_success():
    def handler(request: httpx.Request):
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "result": {
                "content": [
                    {"type": "text", "text": "## Precedente STJ REsp 1.845.234\nEmenta oficial..."}
                ]
            }
        }
        return httpx.Response(200, json=payload)

    transport = httpx.MockTransport(handler)
    client = JurisprudenciaMcpClient(mcp_url="http://mock-mcp:8787", transport=transport)
    
    res = await client.buscar_teses_vinculantes("Tema 1015")
    assert "REsp 1.845.234" in res
    assert "Ementa oficial" in res

@pytest.mark.asyncio
async def test_mcp_client_fallback_on_unknown_tool():
    calls = []
    def handler(request: httpx.Request):
        import json
        body = json.loads(request.content.decode("utf-8"))
        calls.append(body["params"]["name"])
        if body["params"]["name"] == "ferramenta_inexistente":
            return httpx.Response(200, json={
                "jsonrpc": "2.0",
                "id": 1,
                "error": {
                    "code": -32602,
                    "message": "Unknown tool: ferramenta_inexistente"
                }
            })
        else:
            return httpx.Response(200, json={
                "jsonrpc": "2.0",
                "id": 1,
                "result": {
                    "content": [{"type": "text", "text": "Resultado do fallback de pesquisa"}]
                }
            })

    transport = httpx.MockTransport(handler)
    client = JurisprudenciaMcpClient(mcp_url="http://mock-mcp:8787", transport=transport)
    
    res = await client.call_tool("ferramenta_inexistente", {"query": "prescrição"})
    assert "Resultado do fallback de pesquisa" in res
    assert calls == ["ferramenta_inexistente", "pesquisar_jurisprudencia"]

def test_rag_store_save_and_load(tmp_path):
    store = RagStore(storage_dir=tmp_path)
    meta = {
        "id": "stj-resp-1845234-sp",
        "tipo": "acordao_precedente",
        "tribunal": "STJ",
        "tema_repetitivo": 1015
    }
    content = "# Precedente STJ > REsp 1.845.234/SP\n\n## Tese Fixada\nTexto da tese..."
    
    saved_path = store.salvar_documento("stj-resp-1845234-sp", meta, content)
    assert saved_path.exists()
    
    loaded_meta, loaded_body = store.carregar_documento("stj-resp-1845234-sp")
    assert loaded_meta["tribunal"] == "STJ"
    assert loaded_meta["tema_repetitivo"] == 1015
    assert "Texto da tese..." in loaded_body

    # Teste de verificação no corpus
    assert store.verificar_citacao_no_corpus("1.845.234") is True
    assert store.verificar_citacao_no_corpus("REsp Inexistente 9999999") is False

@pytest.mark.asyncio
async def test_mcp_client_placeholder_url_immediate_error():
    client = JurisprudenciaMcpClient(mcp_url="https://jurisprudencia.seu-dominio.workers.dev")
    with pytest.raises(RuntimeError, match="URL placeholder"):
        await client.call_tool("pesquisar_jurisprudencia", {"query": "teste"})

def test_rag_store_path_traversal_prevention(tmp_path):
    store = RagStore(storage_dir=tmp_path)
    # Tentar escapar do diretório usando ../../
    path_salvo = store.salvar_documento("../../documento_malicioso", {"tipo": "teste"}, "Corpo do texto")
    assert path_salvo.exists()
    # Deve estar estritamente contido dentro de tmp_path
    assert path_salvo.parent == tmp_path
    assert path_salvo.name == "documento_malicioso.md"
