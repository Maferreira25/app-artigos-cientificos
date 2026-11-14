import asyncio
import re
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from src.config import config
from src.schemas import GateAvaliadoEnum, TipoDocumentoEnum
from src.orchestrator import AcademicPipelineOrchestrator
from src.improver import AcademicPaperImprover
from src.exporter import AcademicExporter
from src.rag_store import RagStore


app = FastAPI(
    title="StrictoSensu AI — Plataforma de Artigos e Teses de Doutorado",
    version="1.3.0",
    description="Interface Web para Geração Autônoma e Elevação de Papers para Banca de Doutorado (ABNT PDF/DOCX)"
)

STATIC_DIR = Path(__file__).resolve().parent / "static"
STATIC_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Armazenamento em memória do estado de jobs em execução / concluídos
JOBS_STORE: Dict[str, Dict[str, Any]] = {}

GATE_ORDER = [
    GateAvaliadoEnum.GATE_1_EPISTEMICO.value,
    GateAvaliadoEnum.GATE_2_BIBLIOGRAFICO.value,
    GateAvaliadoEnum.GATE_3_METODOLOGICO.value,
    GateAvaliadoEnum.GATE_4_REDACAO_SECCIONAL.value,
    GateAvaliadoEnum.GATE_5_CITACOES_BANCA.value,
    GateAvaliadoEnum.GATE_6_HOMOLOGACAO_FINAL.value,
]

GATE_LABELS = {
    GateAvaliadoEnum.GATE_1_EPISTEMICO.value: {
        "numero": 1,
        "titulo": "Epistemologia & Problematização",
        "modelo": config.model_supervisor,
    },
    GateAvaliadoEnum.GATE_2_BIBLIOGRAFICO.value: {
        "numero": 2,
        "titulo": "Revisão Sistemática PRISMA & MCP",
        "modelo": config.model_literature,
    },
    GateAvaliadoEnum.GATE_3_METODOLOGICO.value: {
        "numero": 3,
        "titulo": "Metodologia & Jurimetria Empírica",
        "modelo": config.model_methodology,
    },
    GateAvaliadoEnum.GATE_4_REDACAO_SECCIONAL.value: {
        "numero": 4,
        "titulo": "Redação Seccional Dialética",
        "modelo": config.model_writer,
    },
    GateAvaliadoEnum.GATE_5_CITACOES_BANCA.value: {
        "numero": 5,
        "titulo": "Auditoria Anti-Alucinação & Banca",
        "modelo": config.model_defense,
    },
    GateAvaliadoEnum.GATE_6_HOMOLOGACAO_FINAL.value: {
        "numero": 6,
        "titulo": "Homologação Final ABNT",
        "modelo": config.model_supervisor,
    },
}


class GeneratePaperRequest(BaseModel):
    titulo: str = Field(..., min_length=5, description="Título da tese ou artigo científico")
    tema: str = Field(..., min_length=5, description="Tema ou questão central de pesquisa")
    tipo_documento: TipoDocumentoEnum = Field(
        TipoDocumentoEnum.ARTIGO_CIENTIFICO,
        description="Formato alvo: ARTIGO_CIENTIFICO (ABNT NBR 6022) ou PROJETO_TESE (ABNT NBR 15287 / 14724)"
    )
    recorte_tematico: Optional[str] = Field(None, description="Problema, hipótese preliminar ou recorte opcional")
    threshold: float = Field(85.0, ge=50.0, le=100.0, description="Nota de corte mínima (padrão 85.0)")
    gerar_pdf: bool = Field(True, description="Compilar saída em PDF ABNT")
    gerar_docx: bool = Field(True, description="Compilar saída em DOCX ABNT")


def _criar_estado_inicial_gates() -> Dict[str, Dict[str, Any]]:
    gates = {}
    for g_key in GATE_ORDER:
        info = GATE_LABELS[g_key]
        gates[g_key] = {
            "gate": g_key,
            "numero": info["numero"],
            "titulo": info["titulo"],
            "modelo": info["modelo"],
            "status": "PENDING",
            "score": None,
            "decisao": None,
            "autorizado": None,
            "diagnostico": "",
        }
    return gates


def _registrar_evento_job(job_id: str, evento: Dict[str, Any]) -> None:
    job = JOBS_STORE.get(job_id)
    if not job:
        return
    gate_key = evento.get("gate")
    status = evento.get("status", "RUNNING")
    msg = evento.get("message", "")
    timestamp = datetime.now().strftime("%H:%M:%S")

    if msg:
        job["logs"].append(f"[{timestamp}] {msg}")

    if gate_key and gate_key in job["gates"]:
        g_entry = job["gates"][gate_key]
        g_entry["status"] = status
        if "score" in evento and evento["score"] is not None:
            g_entry["score"] = evento["score"]
        if "decisao" in evento and evento["decisao"] is not None:
            g_entry["decisao"] = evento["decisao"]
        if "autorizado" in evento and evento["autorizado"] is not None:
            g_entry["autorizado"] = evento["autorizado"]
        if "diagnostico" in evento and evento["diagnostico"]:
            g_entry["diagnostico"] = evento["diagnostico"]

    job["updated_at"] = datetime.now().isoformat()


async def _executar_job_geracao(job_id: str, req: GeneratePaperRequest) -> None:
    job = JOBS_STORE[job_id]
    job["status"] = "RUNNING"
    exporter = AcademicExporter()

    try:
        tema_efetivo = req.tema
        if req.recorte_tematico and req.recorte_tematico.strip():
            tema_efetivo = f"{req.tema} (Recorte: {req.recorte_tematico.strip()})"

        orchestrator = AcademicPipelineOrchestrator(threshold=req.threshold)
        state = await orchestrator.executar_pipeline_completo(
            titulo=req.titulo,
            tema=tema_efetivo,
            progress_callback=lambda ev: _registrar_evento_job(job_id, ev),
            tipo_documento=req.tipo_documento,
        )

        # Mesmo que algum gate exija ajustes, geramos os arquivos para inspeção e download
        md_path = exporter.gerar_markdown_consolidado(state)
        docx_path = exporter.compilar_docx(md_path) if req.gerar_docx else None
        pdf_path = exporter.compilar_pdf(md_path) if req.gerar_pdf else None

        scores = [p.score_global for p in state.pareceres_gates.values()]
        score_medio = round(sum(scores) / len(scores), 2) if scores else 0.0

        job["result"] = {
            "titulo": state.titulo,
            "tema": state.tema,
            "status_geral": state.status_geral,
            "score_medio": score_medio,
            "homologado": state.status_geral == "HOMOLOGADO_SUCESSO",
            "files": {
                "md": md_path.name if md_path and md_path.exists() else None,
                "docx": docx_path.name if docx_path and docx_path.exists() else None,
                "pdf": pdf_path.name if pdf_path and pdf_path.exists() else None,
                "dossie_md": None,
                "dossie_pdf": None,
                "dossie_docx": None,
            },
        }
        job["status"] = "COMPLETED"
        job["logs"].append(f"[{datetime.now().strftime('%H:%M:%S')}] Pipeline concluído com status: {state.status_geral}")
    except Exception as e:
        job["status"] = "FAILED"
        job["error"] = str(e)
        job["logs"].append(f"[{datetime.now().strftime('%H:%M:%S')}] Erro fatal: {e}")


async def _executar_job_melhoria(
    job_id: str,
    arquivo_path: Path,
    titulo_customizado: Optional[str],
    threshold: float,
    gerar_pdf: bool,
    gerar_docx: bool,
    tipo_documento: TipoDocumentoEnum = TipoDocumentoEnum.ARTIGO_CIENTIFICO,
) -> None:
    job = JOBS_STORE[job_id]
    job["status"] = "RUNNING"
    exporter = AcademicExporter()

    try:
        improver = AcademicPaperImprover(threshold=threshold)
        state, relatorio = await improver.aprimorar_paper(
            caminho_arquivo=arquivo_path,
            titulo_customizado=titulo_customizado,
            progress_callback=lambda ev: _registrar_evento_job(job_id, ev),
            gerar_pdf=gerar_pdf,
            gerar_docx=gerar_docx,
            tipo_documento=tipo_documento,
        )

        md_path = Path(relatorio["artigo_md_path"])
        docx_path = Path(relatorio["artigo_docx_path"]) if relatorio.get("artigo_docx_path") else None
        pdf_path = Path(relatorio["artigo_pdf_path"]) if relatorio.get("artigo_pdf_path") else None

        if gerar_pdf and (not pdf_path or not pdf_path.exists()):
            pdf_path = exporter.compilar_pdf(md_path)
        if gerar_docx and (not docx_path or not docx_path.exists()):
            docx_path = exporter.compilar_docx(md_path)

        dossie_md = Path(relatorio["dossie_path"]) if relatorio.get("dossie_path") else None
        dossie_pdf = Path(relatorio["dossie_pdf_path"]) if relatorio.get("dossie_pdf_path") else None
        dossie_docx = Path(relatorio["dossie_docx_path"]) if relatorio.get("dossie_docx_path") else None

        diag_init = relatorio.get("diagnostico_inicial", {})
        res_final = relatorio.get("resultado_final", {})

        job["result"] = {
            "titulo": state.titulo,
            "tema": state.tema,
            "status_geral": state.status_geral,
            "score_inicial": diag_init.get("score_medio", 0.0),
            "score_medio": res_final.get("score_medio_final", 0.0),
            "inconsistencias_antes": diag_init.get("inconsistencias_citacao", 0),
            "inconsistencias_depois": res_final.get("inconsistencias_citacao_finais", 0),
            "parecer_banca": res_final.get("parecer_banca_final", ""),
            "homologado": res_final.get("homologado", False),
            "intervencoes": relatorio.get("intervencoes_realizadas", []),
            "files": {
                "md": md_path.name if md_path and md_path.exists() else None,
                "docx": docx_path.name if docx_path and docx_path.exists() else None,
                "pdf": pdf_path.name if pdf_path and pdf_path.exists() else None,
                "dossie_md": dossie_md.name if dossie_md and dossie_md.exists() else None,
                "dossie_pdf": dossie_pdf.name if dossie_pdf and dossie_pdf.exists() else None,
                "dossie_docx": dossie_docx.name if dossie_docx and dossie_docx.exists() else None,
            },
        }
        job["status"] = "COMPLETED"
        job["logs"].append(f"[{datetime.now().strftime('%H:%M:%S')}] Elevação de paper concluída! Score final: {res_final.get('score_medio_final', 0.0):.2f}/100")
    except Exception as e:
        job["status"] = "FAILED"
        job["error"] = str(e)
        job["logs"].append(f"[{datetime.now().strftime('%H:%M:%S')}] Erro fatal: {e}")


@app.get("/", response_class=HTMLResponse)
async def index_page():
    """Serve a interface web principal."""
    html_file = STATIC_DIR / "index.html"
    if not html_file.exists():
        raise HTTPException(status_code=404, detail="Interface index.html não encontrada.")
    return HTMLResponse(content=html_file.read_text(encoding="utf-8"))


@app.get("/api/config")
async def get_system_config():
    """Retorna informações de configuração dos modelos e servidor MCP para exibição no painel."""
    store = RagStore()
    docs = store.listar_documentos()
    return {
        "mcp_url": config.mcp_url,
        "approval_threshold": config.approval_threshold,
        "corpus_count": len(docs),
        "models": {
            "supervisor": config.model_supervisor,
            "literature": config.model_literature,
            "methodology": config.model_methodology,
            "writer": config.model_writer,
            "defense": config.model_defense,
        },
        "gates": [GATE_LABELS[k] for k in GATE_ORDER],
    }


@app.post("/api/generate")
async def start_generate_paper(req: GeneratePaperRequest, background_tasks: BackgroundTasks):
    """Inicia um job assíncrono para gerar um novo paper/tese do zero."""
    job_id = str(uuid.uuid4())
    JOBS_STORE[job_id] = {
        "job_id": job_id,
        "mode": "GENERATE",
        "titulo": req.titulo,
        "tema": req.tema,
        "threshold": req.threshold,
        "status": "QUEUED",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "gates": _criar_estado_inicial_gates(),
        "logs": [f"[{datetime.now().strftime('%H:%M:%S')}] Iniciando pipeline para '{req.titulo}'..."],
        "result": None,
        "error": None,
    }
    background_tasks.add_task(_executar_job_geracao, job_id, req)
    return {"job_id": job_id, "status": "QUEUED"}


@app.post("/api/improve")
async def start_improve_paper(
    background_tasks: BackgroundTasks,
    arquivo: Optional[UploadFile] = File(None),
    texto_colado: Optional[str] = Form(None),
    titulo: Optional[str] = Form(None),
    tipo_documento: TipoDocumentoEnum = Form(TipoDocumentoEnum.ARTIGO_CIENTIFICO),
    threshold: float = Form(85.0),
    gerar_pdf: bool = Form(True),
    gerar_docx: bool = Form(True),
):
    """Inicia um job assíncrono para revisar e aprimorar um paper existente (upload ou texto)."""
    config.ensure_directories()

    if arquivo and arquivo.filename:
        ext = Path(arquivo.filename).suffix.lower()
        if ext not in (".md", ".txt", ".markdown", ".docx", ".pdf"):
            raise HTTPException(
                status_code=400,
                detail=f"Extensão '{ext}' não suportada. Envie um arquivo .pdf, .docx, .md ou .txt."
            )
        safe_name = re.sub(r"[^a-zA-Z0-9._\-]", "_", Path(arquivo.filename).name)
        saved_draft = config.drafts_dir / f"upload_{uuid.uuid4().hex[:8]}_{safe_name}"
        content_bytes = await arquivo.read()
        if not content_bytes:
            raise HTTPException(status_code=400, detail="O arquivo enviado está vazio.")
        if len(content_bytes) > 25 * 1024 * 1024:
            raise HTTPException(status_code=413, detail="O arquivo excede o limite máximo de 25 MB.")
        saved_draft.write_bytes(content_bytes)
    elif texto_colado and len(texto_colado.strip()) >= 30:
        saved_draft = config.drafts_dir / f"colado_{uuid.uuid4().hex[:8]}.md"
        saved_draft.write_text(texto_colado.strip(), encoding="utf-8")
    else:
        raise HTTPException(
            status_code=400,
            detail="Envie um arquivo (.md, .txt, .docx) ou cole o texto do paper (mínimo 30 caracteres)."
        )

    job_id = str(uuid.uuid4())
    titulo_display = (titulo.strip() if titulo and titulo.strip() else saved_draft.stem)
    JOBS_STORE[job_id] = {
        "job_id": job_id,
        "mode": "IMPROVE",
        "titulo": titulo_display,
        "tema": "Auditoria e Elevação para Banca de Doutorado",
        "threshold": threshold,
        "status": "QUEUED",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "gates": _criar_estado_inicial_gates(),
        "logs": [f"[{datetime.now().strftime('%H:%M:%S')}] Arquivo recebido ({saved_draft.name}). Iniciando auditoria da Banca..."],
        "result": None,
        "error": None,
    }
    background_tasks.add_task(
        _executar_job_melhoria,
        job_id,
        saved_draft,
        titulo.strip() if titulo and titulo.strip() else None,
        threshold,
        gerar_pdf,
        gerar_docx,
        tipo_documento,
    )
    return {"job_id": job_id, "status": "QUEUED"}


@app.get("/api/jobs/{job_id}")
async def get_job_status(job_id: str):
    """Consulta o andamento em tempo real dos 6 Quality Gates e resultado de um job."""
    job = JOBS_STORE.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job não encontrado.")
    return job


@app.get("/api/history")
async def list_generated_history():
    """Lista o histórico de todos os papers e dossiês gerados na pasta output/."""
    config.ensure_directories()
    items: List[Dict[str, Any]] = []

    md_files = sorted(
        config.output_dir.glob("*.md"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )

    for md_file in md_files:
        stem = md_file.stem
        is_dossie = stem.startswith("Dossie_Banca_Doutorado_")
        docx_file = md_file.with_suffix(".docx")
        pdf_file = md_file.with_suffix(".pdf")
        dossie_candidate = config.output_dir / f"Dossie_Banca_Doutorado_{stem}.md"

        try:
            text_content = md_file.read_text(encoding="utf-8")
        except Exception:
            text_content = ""

        # Extrair título legível da primeira linha
        first_line = next((l.strip() for l in text_content.splitlines() if l.strip()), stem)
        titulo_legivel = first_line.lstrip("#").strip() if first_line.startswith("#") else stem.replace("_", " ")

        stat = md_file.stat()
        if is_dossie:
            tipo_badge_hist = "DOSSIÊ DA BANCA"
        elif "**Natureza da Obra:** Projeto de Tese" in text_content:
            tipo_badge_hist = "PROJETO DE TESE"
        elif "**Natureza da Obra:** Artigo Científico" in text_content:
            tipo_badge_hist = "ARTIGO CIENTÍFICO"
        else:
            tipo_badge_hist = "ARTIGO / TESE"

        items.append({
            "id": stem,
            "titulo": titulo_legivel,
            "tipo": tipo_badge_hist,
            "is_dossie": is_dossie,
            "created_at": datetime.fromtimestamp(stat.st_mtime).strftime("%d/%m/%Y %H:%M"),
            "size_kb": round(stat.st_size / 1024.0, 1),
            "preview": text_content[:360].strip(),
            "files": {
                "md": md_file.name,
                "docx": docx_file.name,  # Gerado sob demanda se não existir ainda
                "pdf": pdf_file.name,    # Gerado sob demanda se não existir ainda
                "has_docx": docx_file.exists(),
                "has_pdf": pdf_file.exists(),
                "dossie_md": dossie_candidate.name if (not is_dossie and dossie_candidate.exists()) else None,
            },
        })

    return {"items": items}


def _resolver_caminho_seguro_output(filename: str) -> Path:
    """Garante confinamento estrito dentro de config.output_dir contra path traversal."""
    safe_name = Path(filename).name
    if not safe_name or safe_name in (".", ".."):
        raise HTTPException(status_code=400, detail="Caminho de arquivo inválido.")
    out_root = config.output_dir.resolve()
    target = (out_root / safe_name).resolve()
    try:
        target.relative_to(out_root)
    except ValueError:
        raise HTTPException(status_code=400, detail="Caminho de arquivo inválido.")
    return target


@app.get("/api/preview/{filename}")
async def preview_markdown_file(filename: str):
    """Retorna o conteúdo integral de um arquivo Markdown de output/ para leitura na interface."""
    target = _resolver_caminho_seguro_output(filename)
    if not target.exists() or target.suffix.lower() != ".md":
        raise HTTPException(status_code=404, detail="Documento Markdown não encontrado.")
    return {
        "filename": target.name,
        "content": target.read_text(encoding="utf-8"),
    }


@app.get("/api/download/{filename}")
async def download_output_file(filename: str):
    """Faz o download de arquivo .pdf, .docx ou .md, compilando sob demanda caso necessário."""
    target = _resolver_caminho_seguro_output(filename)
    ext = target.suffix.lower()

    if ext not in (".md", ".docx", ".pdf"):
        raise HTTPException(status_code=400, detail="Formato de download não suportado.")

    # Compilação sob demanda caso o usuário solicite .pdf ou .docx de um .md já existente
    if not target.exists() and ext in (".pdf", ".docx"):
        md_source = target.with_suffix(".md")
        if md_source.exists():
            exporter = AcademicExporter(output_dir=str(config.output_dir))
            if ext == ".pdf":
                exporter.compilar_pdf(md_source)
            elif ext == ".docx":
                exporter.compilar_docx(md_source)

    if not target.exists():
        raise HTTPException(status_code=404, detail=f"Arquivo '{target.name}' não encontrado.")

    media_types = {
        ".pdf": "application/pdf",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".md": "text/markdown; charset=utf-8",
    }
    return FileResponse(
        path=target,
        filename=target.name,
        media_type=media_types.get(ext, "application/octet-stream"),
    )
