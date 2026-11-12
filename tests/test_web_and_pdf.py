import pytest
from pathlib import Path
from httpx import AsyncClient, ASGITransport
from src.exporter import AcademicExporter
from src.importer import AcademicPaperImporter
from src.web import app, _resolver_caminho_seguro_output
from src.config import config
from fastapi import HTTPException


def test_exporter_pdf_latex_e_importer_pdf_docx(tmp_path):
    """Testa compilação real PDF (Pandoc+LaTeX), DOCX e a reimportação de ambos pelo AcademicPaperImporter."""
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

    docx_path = exporter.compilar_docx(md_file)
    assert docx_path is not None
    assert Path(docx_path).exists()

    # Testa a extração de PDF e DOCX pelo AcademicPaperImporter
    importer = AcademicPaperImporter()
    extracted_pdf = importer.carregar_arquivo(pdf_path)
    assert "Precedentes" in extracted_pdf or "Introdução" in extracted_pdf

    extracted_docx = importer.carregar_arquivo(docx_path)
    assert "Precedentes" in extracted_docx and "Introdução" in extracted_docx


def test_exporter_pdf_fallback_nativo_direto(tmp_path, monkeypatch):
    """Garante que o gerador PDF ABNT nativo funciona como fallback mesmo quando Pandoc/LaTeX estão ausentes."""
    monkeypatch.setattr("shutil.which", lambda *args, **kwargs: None)
    exporter = AcademicExporter(output_dir=tmp_path)
    md_file = tmp_path / "Fallback_Nativo.md"
    md_file.write_text(
        "# Título Principal em Caixa Alta\n\n"
        "## Subseção Secundária\n\n"
        "### Subseção Terciária\n\n"
        "> Bloco de citação longa com acentuação: ç, ã, õ, é, ú — e caracteres especiais (parênteses) e \\barra\\.\n\n"
        "**Parágrafo em destaque negrito** com texto complementar.\n\n"
        "Parágrafo regular de desenvolvimento.\n",
        encoding="utf-8",
    )

    pdf_path = exporter.compilar_pdf(md_file)
    assert pdf_path is not None
    assert pdf_path.exists()
    raw = pdf_path.read_bytes()
    assert raw.startswith(b"%PDF-1.4")
    assert b"/BaseFont /Times-Roman" in raw
    assert b"%%EOF" in raw


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
        assert "escapeHtml" in res_index.text

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

        # 4. Proteção contra Path Traversal / extensão inválida / arquivo inexistente
        res_bad = await client.get("/api/download/secret.env")
        assert res_bad.status_code == 400

        res_not_found = await client.get("/api/download/Nao_Existe.pdf")
        assert res_not_found.status_code == 404

        with pytest.raises(HTTPException) as exc_info:
            _resolver_caminho_seguro_output("..")
        assert exc_info.value.status_code == 400


@pytest.mark.asyncio
async def test_web_improve_validation_and_negative_cases():
    """Verifica validações negativas de upload, arquivo vazio, extensão inválida e job inexistente."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Sem arquivo nem texto
        res = await client.post("/api/improve", data={"threshold": "85.0"})
        assert res.status_code == 400
        assert "Envie um arquivo" in res.json()["detail"]

        # Extensão inválida (.exe)
        res_ext = await client.post(
            "/api/improve",
            data={"threshold": "85.0"},
            files={"arquivo": ("malware.exe", b"MZ...", "application/octet-stream")},
        )
        assert res_ext.status_code == 400
        assert "não suportada" in res_ext.json()["detail"]

        # Arquivo vazio
        res_empty = await client.post(
            "/api/improve",
            data={"threshold": "85.0"},
            files={"arquivo": ("vazio.md", b"", "text/markdown")},
        )
        assert res_empty.status_code == 400
        assert "vazio" in res_empty.json()["detail"]

        # Job inexistente
        res_job = await client.get("/api/jobs/job-id-inexistente")
        assert res_job.status_code == 404
