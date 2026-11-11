import pytest
import httpx
from src.orchestrator import AcademicPipelineOrchestrator
from src.rag_store import RagStore
from src.mcp_client import JurisprudenciaMcpClient
from src.exporter import AcademicExporter

@pytest.mark.asyncio
async def test_orchestrator_end_to_end_flow(tmp_path):
    # Mock do servidor MCP respondendo as tools chamadas pelos agentes
    def mcp_handler(request: httpx.Request):
        import json
        body = json.loads(request.content.decode("utf-8"))
        tool_name = body.get("params", {}).get("name", "")
        
        text_map = {
            "listar_overruling_tema": "Mutação jurisprudencial registrada no Tema 1015 do STJ.",
            "linha_do_tempo_precedentes": "1998: Início da controvérsia. 2015: CPC institui rito dos repetitivos. 2023: Fixação da tese.",
            "buscar_precedentes_qualificados": "STJ fixou tese vinculante com eficácia geral sobre a matéria.",
            "analisar_jurimetria": "STJ analisou 4.520 recursos com 82% de aderência à tese vinculante.",
            "pesquisar_jurisprudencia": "Ementa oficial: RECURSO ESPECIAL. AÇÃO COLETIVA. PRESCRIÇÃO INTERCORRENTE.",
            "analisar_tese_juridica": "Pontos de cautela da tese: confrontar com o entendimento da Corte Especial quanto à retroatividade."
        }
        
        resp_text = text_map.get(tool_name, "Resposta genérica de ferramenta MCP")
        return httpx.Response(200, json={
            "jsonrpc": "2.0",
            "id": 1,
            "result": {
                "content": [{"type": "text", "text": resp_text}]
            }
        })

    transport = httpx.MockTransport(mcp_handler)
    mcp_client = JurisprudenciaMcpClient(mcp_url="http://mock-mcp:8787", transport=transport)
    rag_store = RagStore(storage_dir=tmp_path / "corpus")
    
    orchestrator = AcademicPipelineOrchestrator(
        mcp_client=mcp_client,
        rag_store=rag_store,
        threshold=85.0
    )

    state = await orchestrator.executar_pipeline_completo(
        titulo="A Eficácia Vinculante dos Precedentes Judiciais",
        tema="Precedentes Vinculantes e Segurança Jurídica"
    )

    # Verificação de status geral
    assert state.status_geral == "HOMOLOGADO_SUCESSO"
    assert state.refatoracao_pendente is False

    # Verificação dos 6 gates
    assert len(state.pareceres_gates) == 6
    for gate_name, parecer in state.pareceres_gates.items():
        assert parecer.autorizacao_avanco is True
        assert parecer.score_global >= 85.0

    # Verificação do corpus indexado
    docs = rag_store.listar_documentos()
    assert len(docs) > 0
    assert rag_store.verificar_citacao_no_corpus("1.845.234") is True

    # Verificação da exportação consolidada
    exporter = AcademicExporter(output_dir=tmp_path / "output")
    md_file = exporter.gerar_markdown_consolidado(state)
    assert md_file.exists()
    conteudo_exportado = md_file.read_text(encoding="utf-8")
    assert "A Eficácia Vinculante dos Precedentes Judiciais" in conteudo_exportado
    assert "Referências" in conteudo_exportado
    assert "DWORKIN, Ronald" in conteudo_exportado
