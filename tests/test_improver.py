import pytest
from pathlib import Path
from src.importer import AcademicPaperImporter
from src.improver import AcademicPaperImprover
from src.schemas import DocumentoAcademicoState
from src.llm import LlmClient
from src.mcp_client import JurisprudenciaMcpClient

def test_importer_parser_markdown():
    importer = AcademicPaperImporter()
    texto = (
        "# A Modulação de Efeitos no Direito Tributário\n\n"
        "Tema Central: Confiança Legítima e Precedentes\n\n"
        "Problema de pesquisa: Em que medida o overruling tributário sem modulação fere a segurança jurídica?\n\n"
        "Hipótese central: A proteção da confiança exige critérios objetivos vinculantes para a eficácia temporal das decisões.\n\n"
        "## 1. Introdução\n"
        "O presente artigo discute a segurança jurídica nas viragens jurisprudenciais.\n\n"
        "## 2. Marco Teórico\n"
        "A teoria dos precedentes de Neil MacCormick e Ronald Dworkin..."
    )
    
    state = importer.parsear_para_estado(texto)
    assert state.titulo == "A Modulação de Efeitos no Direito Tributário"
    assert "Confiança Legítima" in state.tema
    assert "overruling tributário" in state.problema_pesquisa
    assert "proteção da confiança" in state.hipotese
    assert "1. Introdução" in state.capitulos
    assert "2. Marco Teórico" in state.capitulos

@pytest.mark.asyncio
async def test_improver_fluxo_completo(tmp_path):
    # Criar um arquivo markdown de artigo inicial com texto curto que exige intervenção
    artigo_teste = tmp_path / "paper_teste_doutorado.md"
    artigo_teste.write_text(
        "# O Princípio da Confiança Legítima\n\n"
        "Tema: Confiança Legítima e Modulação de Efeitos\n\n"
        "## 1. Introdução\n"
        "Este artigo aborda o princípio da confiança legítima no direito brasileiro com foco na jurisprudência das cortes superiores.\n\n"
        "## 2. Desenvolvimento Dialético\n"
        "A doutrina diverge sobre os efeitos do overruling e a incidência do art. 927 do CPC.",
        encoding="utf-8"
    )

    improver = AcademicPaperImprover(
        llm_client=LlmClient(api_key=""), # modo offline determinístico
        mcp_client=JurisprudenciaMcpClient(mcp_url="http://mock-mcp:8787"),
        threshold=85.0
    )

    state, relatorio = await improver.aprimorar_paper(caminho_arquivo=artigo_teste)

    assert state.status_geral == "HOMOLOGADO_SUCESSO"
    assert "diagnostico_inicial" in relatorio
    assert "resultado_final" in relatorio
    assert relatorio["resultado_final"]["homologado"] is True
    assert Path(relatorio["dossie_path"]).exists()
    assert Path(relatorio["artigo_md_path"]).exists()

