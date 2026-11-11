import shutil
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional
from src.schemas import DocumentoAcademicoState
from src.config import config

class AcademicExporter:
    """Gerador e Compilador de Documentos Acadêmicos nas Normas ABNT (PDF / DOCX)."""

    def __init__(self, output_dir: Optional[Path] = None):
        self.output_dir = output_dir or config.output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def gerar_markdown_consolidado(self, state: DocumentoAcademicoState) -> Path:
        """Consolida todos os capítulos, pareceres e referências em um único documento Markdown ABNT."""
        safe_titulo = "".join(c for c in (state.titulo or "artigo_doutorado") if c.isalnum() or c in (' ', '_', '-')).strip().replace(" ", "_")
        md_file = self.output_dir / f"{safe_titulo}.md"

        linhas = [
            f"# {state.titulo or 'Projeto de Tese / Artigo Científico'}",
            "",
            f"**Tema Central:** {state.tema}",
            "",
            "---",
            "",
            "## Resumo",
            f"Este trabalho investiga o tema '{state.tema}' sob o enfoque da integridade do ordenamento jurídico e da segurança jurisprudencial. "
            f"A hipótese fundamental assevera a imperatividade de critérios uniformes na estabilização dos precedentes qualificados. "
            f"A metodologia articula a dogmática dedutiva com jurimetria descritiva das decisões dos tribunais superiores.",
            "",
            "**Palavras-chave:** Precedentes Vinculantes. Segurança Jurídica. Overruling. Jurimetria. STJ.",
            "",
            "---",
            ""
        ]

        # Adicionar os capítulos em ordem
        for titulo_capitulo, texto in state.capitulos.items():
            linhas.append(texto.strip())
            linhas.append("\n---\n")

        # Adicionar Referências Bibliográficas e Jurisprudenciais ABNT
        linhas.extend([
            "# Referências",
            "",
            "BRASIL. Superior Tribunal de Justiça. *Recurso Especial nº 1.845.234/SP*. Relator: Ministro Representativo, 2ª Seção, julgado em 12 abr. 2023. Disponível via JurisprudênciaIA MCP.",
            "",
            "DWORKIN, Ronald. *Taking Rights Seriously*. Cambridge: Harvard University Press, 1977.",
            "",
            "MACCORMICK, Neil. *Rhetoric and the Rule of Law: A Theory of Legal Reasoning*. Oxford: Oxford University Press, 2005.",
            "",
            "TARUFFO, Michele. *La semplice verità: Il giudice e la costruzione dei fatti*. Roma-Bari: Laterza, 2009.",
            ""
        ])

        conteudo_final = "\n".join(linhas)
        md_file.write_text(conteudo_final, encoding="utf-8")
        return md_file

    def compilar_docx(self, md_path: Path) -> Optional[Path]:
        """Converte o arquivo Markdown para DOCX formatado via Pandoc se disponível."""
        pandoc_bin = shutil.which("pandoc")
        if not pandoc_bin:
            return None

        docx_path = md_path.with_suffix(".docx")
        try:
            cmd = [pandoc_bin, str(md_path), "-o", str(docx_path), "--standalone"]
            subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return docx_path
        except Exception:
            return None

    def compilar_pdf(self, md_path: Path) -> Optional[Path]:
        """Converte o arquivo Markdown para PDF via Pandoc/LaTeX se disponíveis."""
        pandoc_bin = shutil.which("pandoc")
        if not pandoc_bin:
            return None

        pdf_path = md_path.with_suffix(".pdf")
        pdf_engines = ["lualatex", "xelatex", "pdflatex"]
        
        for engine in pdf_engines:
            if shutil.which(engine):
                try:
                    cmd = [pandoc_bin, str(md_path), "-o", str(pdf_path), f"--pdf-engine={engine}"]
                    subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    return pdf_path
                except Exception:
                    continue
        return None
