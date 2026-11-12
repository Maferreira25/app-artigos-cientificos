import pytest
from pathlib import Path
from httpx import AsyncClient, ASGITransport
from src.exporter import AcademicExporter
from src.web import app
from src.config import config


def test_exporter_pdf_abnt_nativo(tmp_path):
    """Garante que o gerador PDF ABNT nativo cria um arquivo PDF 1.4 válido com acentuação PT-BR."""
    exporter = AcademicExporter(output_dir=str(tmp_path))
    md_file = tmp_path / "Artigo_Teste_ABNT.md"
    md_file.write_text(
        "# A Eficácia Vinculante dos Precedentes Judiciais\n\n"
        "**Data de Homologação:** 11/11/2026\n\n"
        "## 1. Introdução\n\n"
        "A jurisdição constitucional contemporânea exige observância estrita à segurança jurídica e à isonomia.\n\n"
        "> Citação longa com recuo de 4cm segundo as diretrizes da ABNT NBR 10520, preservando acentuação gráfica: ç, ã, õ, é, ê, á, í, ó, ú.\n\n"
        "- Item de lista com **negrito** e *itálico*\n"
        "---\n"
        "## Referências Bibliográficas\n\n"
        "- BRASIL. Supremo Tribunal Federal. Tema 987. Brasília, DF, 2024.\n",
        encoding="utf-8",
    )

    pdf_path = exporter.compilar_pdf(md_file)
    assert pdf_path is not None
    pdf_path = Path(pdf_path)
    assert pdf_path.exists()
    content_bytes = pdf_path.read_bytes()
    assert content_bytes.startswith(b"%PDF-1.")
    assert b"%%EOF" in content_bytes
    assert len(content_bytes) > 500

    # Também testa a extração de PDF pelo AcademicPaperImporter
    from src.importer import AcademicPaperImporter
    importer = AcademicPaperImporter()
    extracted_md = importer.carregar_arquivo(pdf_path)
    assert "Precedentes" in extracted_md or "Introdução" in extracted_md


@pytest.mark.asyncio
async def test_web_index_and_config():
    """Testa se a interface HTML principal e o endpoint de configuração carregam corretamente."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res_index = await client.get("/")
        assert res_index.status_code == 200
        assert "Stricto" in res_index.text
        assert "Gerar Novo Paper" in res_index.text
        assert "Revisar & Elevar Paper Existente" in res_index.text

        res_cfg = await client.get("/api/config")
        assert res_cfg.status_code == 200
        data = res_cfg.json()
        assert "models" in data
        assert "mcp_url" in data
        assert "corpus_count" in data
        assert len(data["gates"]) == 6


@pytest.mark.asyncio
async def test_web_history_preview_and_on_demand_pdf(tmp_path, monkeypatch):
    """Testa a listagem do acervo, visualização de Markdown, compilação PDF sob demanda e proteção contra Path Traversal."""
    monkeypatch.setattr(config, "output_dir", tmp_path)
    sample_md = tmp_path / "Paper_Doutorado_Teste.md"
    sample_md.write_text("# Tese de Doutorado em Direito Constitucional\n\nConteúdo acadêmico rigoroso.", encoding="utf-8")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Histórico lista o arquivo
        res_hist = await client.get("/api/history")
        assert res_hist.status_code == 200
        items = res_hist.json()["items"]
        assert len(items) == 1
        assert items[0]["id"] == "Paper_Doutorado_Teste"
        assert items[0]["files"]["pdf"] == "Paper_Doutorado_Teste.pdf"

        # 2. Preview retorna o texto Markdown
        res_prev = await client.get("/api/preview/Paper_Doutorado_Teste.md")
        assert res_prev.status_code == 200
        assert "Tese de Doutorado em Direito Constitucional" in res_prev.json()["content"]

        # 3. Download do PDF gera automaticamente o arquivo PDF sob demanda a partir do .md
        res_pdf = await client.get("/api/download/Paper_Doutorado_Teste.pdf")
        assert res_pdf.status_code == 200
        assert res_pdf.content.startswith(b"%PDF-1.")
        assert (tmp_path / "Paper_Doutorado_Teste.pdf").exists()

        # 4. Proteção contra Path Traversal / extensão inválida
        res_bad = await client.get("/api/download/secret.env")
        assert res_bad.status_code == 400


@pytest.mark.asyncio
async def test_web_improve_validation():
    """Verifica validação de entrada quando nem arquivo nem texto colado são enviados."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post("/api/improve", data={"threshold": "85.0"})
        assert res.status_code == 400
        assert "Envie um arquivo" in res.json()["detail"]
