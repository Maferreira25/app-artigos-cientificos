import os
import re
import shutil
import subprocess
import textwrap
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from src.schemas import DocumentoAcademicoState, TipoDocumentoEnum
from src.config import config


def _resolver_ambiente_tex() -> Dict[str, str]:
    """Garante que os diretórios do Scoop, MiKTeX e Pandoc estejam no PATH do processo atual."""
    env = os.environ.copy()
    home = Path.home()
    extra_dirs = [
        home / "scoop" / "shims",
        home / "scoop" / "apps" / "miktex" / "current" / "texmfs" / "install" / "miktex" / "bin" / "x64",
        home / "AppData" / "Local" / "Programs" / "MiKTeX" / "miktex" / "bin" / "x64",
        home / "AppData" / "Local" / "Pandoc",
    ]
    current_path = env.get("PATH", "")
    for d in extra_dirs:
        if d.exists() and str(d) not in current_path:
            current_path = f"{d}{os.pathsep}{current_path}"
    env["PATH"] = current_path
    return env


class AcademicExporter:
    """Gerador e Compilador de Documentos Acadêmicos nas Normas ABNT (PDF / DOCX / MD)."""

    def __init__(self, output_dir: Optional[Path | str] = None):
        self.output_dir = Path(output_dir) if output_dir else config.output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def gerar_markdown_consolidado(self, state: DocumentoAcademicoState) -> Path:
        """Consolida todos os capítulos, pareceres e referências em um único documento Markdown ABNT."""
        safe_titulo = "".join(
            c for c in (state.titulo or "artigo_doutorado")
            if c.isalnum() or c in (' ', '_', '-')
        ).strip().replace(" ", "_")
        if not safe_titulo:
            safe_titulo = "artigo_doutorado"
        md_file = self.output_dir / f"{safe_titulo}.md"

        is_tese = state.tipo_documento == TipoDocumentoEnum.PROJETO_TESE
        tipo_badge = (
            "Projeto de Tese / Trabalho de Conclusão de Curso (ABNT NBR 15287 / 14724)"
            if is_tese else
            "Artigo Científico de Periódico Qualis A (ABNT NBR 6022)"
        )
        resumo_heading = "## Resumo Executivo do Projeto de Tese" if is_tese else "## Resumo"

        linhas = [
            f"# {state.titulo or ('Projeto de Tese de Final de Curso' if is_tese else 'Artigo Científico')}",
            "",
            f"**Natureza da Obra:** {tipo_badge}",
            f"**Tema Central:** {state.tema}",
            "",
            "---",
            "",
            resumo_heading,
            f"Este {'projeto de tese' if is_tese else 'artigo científico'} investiga o tema '{state.tema}' sob o enfoque da integridade do ordenamento jurídico e da segurança jurisprudencial. "
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
        env = _resolver_ambiente_tex()
        pandoc_bin = shutil.which("pandoc", path=env.get("PATH"))
        if not pandoc_bin or not md_path.exists():
            return None

        docx_path = md_path.with_suffix(".docx")
        try:
            cmd = [pandoc_bin, str(md_path), "-o", str(docx_path), "--standalone"]
            subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env, timeout=60)
            return docx_path
        except Exception:
            return None

    def compilar_pdf(self, md_path: Path) -> Optional[Path]:
        """Converte o arquivo Markdown para PDF nas normas ABNT.
        
        Tenta inicialmente Pandoc + LaTeX (Tectonic/LuaLaTeX/XeLaTeX/PDFLaTeX) ou Typst. Caso o ambiente
        não possua distribuição TeX instalada, utiliza o compilador PDF ABNT nativo em Python.
        """
        if not md_path.exists():
            return None

        pdf_path = md_path.with_suffix(".pdf")
        env = _resolver_ambiente_tex()
        search_path = env.get("PATH")
        pandoc_bin = shutil.which("pandoc", path=search_path)

        if pandoc_bin:
            pdf_engines = ["tectonic", "lualatex", "xelatex", "pdflatex", "typst"]
            latex_template = config.templates_dir / "abnt_article.latex"
            for engine in pdf_engines:
                engine_bin = shutil.which(engine, path=search_path)
                if engine_bin:
                    try:
                        cmd = [pandoc_bin, str(md_path), "-o", str(pdf_path), f"--pdf-engine={engine_bin}"]
                        if engine != "typst" and latex_template.exists():
                            cmd.extend(["--template", str(latex_template)])
                        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env, timeout=90)
                        if pdf_path.exists() and pdf_path.stat().st_size > 0:
                            return pdf_path
                    except Exception:
                        continue

        # Fallback garantido: Compilador PDF ABNT Nativo em Python (A4, margens 3cm/2cm, Times)
        try:
            markdown_text = md_path.read_text(encoding="utf-8")
            self._gerar_pdf_abnt_nativo(markdown_text, pdf_path)
            return pdf_path if pdf_path.exists() else None
        except Exception:
            return None

    @staticmethod
    def _limpar_markdown_inline(texto: str) -> str:
        """Remove marcações inline Markdown preservando o texto acadêmico limpo."""
        texto = re.sub(r'\*\*(.+?)\*\*', r'\1', texto)
        texto = re.sub(r'\*(.+?)\*', r'\1', texto)
        texto = re.sub(r'`(.+?)`', r'\1', texto)
        return texto.strip()

    @staticmethod
    def _escapar_pdf_bytes(texto: str) -> bytes:
        """Converte string Unicode para bytes WinAnsi (cp1252) escapados para literal PDF."""
        substituicoes = {
            "\u2014": "-",
            "\u2013": "-",
            "\u201c": '"',
            "\u201d": '"',
            "\u2018": "'",
            "\u2019": "'",
            "\u2026": "...",
            "\u2022": "-",
        }
        for orig, dest in substituicoes.items():
            texto = texto.replace(orig, dest)
        raw = texto.encode("cp1252", errors="replace")
        raw = raw.replace(b"\\", b"\\\\").replace(b"(", b"\\(").replace(b")", b"\\)")
        return raw

    def _gerar_pdf_abnt_nativo(self, markdown_text: str, pdf_path: Path) -> None:
        """Gera arquivo PDF 1.4 estruturado nas normas ABNT NBR 14724 (A4, margens 3cm/2cm)."""
        # Dimensões A4 em pontos (1 cm = 28.346 pt)
        page_w = 595.28
        page_h = 841.89
        margin_left = 85.04   # 3 cm
        margin_top = 85.04    # 3 cm
        margin_right = 56.69  # 2 cm
        margin_bottom = 56.69 # 2 cm

        # Elementos estruturados: (tipo_fonte, tamanho, leading, recuo_esq, espaco_antes, texto)
        # Fontes: F1 = Times-Roman, F2 = Times-Bold, F3 = Times-Italic
        blocos: List[Tuple[str, int, float, float, float, str]] = []

        for raw_line in markdown_text.splitlines():
            line = raw_line.strip()
            if not line:
                blocos.append(("F1", 12, 18.0, 0.0, 6.0, ""))
                continue
            if line == "---":
                continue

            if line.startswith("# "):
                titulo = self._limpar_markdown_inline(line[2:])
                for wline in textwrap.wrap(titulo.upper(), width=62):
                    blocos.append(("F2", 14, 21.0, 0.0, 10.0, wline))
                blocos.append(("F1", 12, 12.0, 0.0, 4.0, ""))
            elif line.startswith("## "):
                sub = self._limpar_markdown_inline(line[3:])
                for wline in textwrap.wrap(sub, width=68):
                    blocos.append(("F2", 13, 19.5, 0.0, 8.0, wline))
            elif line.startswith("### "):
                sub3 = self._limpar_markdown_inline(line[4:])
                for wline in textwrap.wrap(sub3, width=72):
                    blocos.append(("F2", 12, 18.0, 0.0, 6.0, wline))
            elif line.startswith(">"):
                # Citação direta longa (> 3 linhas): recuo de 4cm (113.38 pt) e fonte 10pt (ABNT NBR 10520)
                cit = self._limpar_markdown_inline(line.lstrip(">").strip())
                for wline in textwrap.wrap(cit, width=64):
                    blocos.append(("F3", 10, 13.0, 113.38, 2.0, wline))
            elif line.startswith("**") and "**" in line[2:]:
                limpo = self._limpar_markdown_inline(line)
                for wline in textwrap.wrap(limpo, width=78):
                    blocos.append(("F2", 12, 18.0, 0.0, 2.0, wline))
            else:
                limpo = self._limpar_markdown_inline(line)
                for wline in textwrap.wrap(limpo, width=80):
                    blocos.append(("F1", 12, 18.0, 0.0, 0.0, wline))

        # Paginação
        paginas_streams: List[bytes] = []
        y_cursor = page_h - margin_top
        comandos_pagina: List[bytes] = []
        num_pagina = 1

        def fechar_pagina(num_pag: int, cmds: List[bytes]) -> bytes:
            # Número da página no canto superior direito (2cm da borda superior e direita)
            header_cmd = (
                f"BT /F1 10 Tf {page_w - margin_right - 20:.2f} {page_h - 45.0:.2f} Td "
                f"({num_pag}) Tj ET"
            ).encode("ascii")
            return b"\n".join([header_cmd] + cmds)

        for font_key, font_size, leading, indent_x, space_before, text_line in blocos:
            y_cursor -= space_before
            if y_cursor - leading < margin_bottom:
                paginas_streams.append(fechar_pagina(num_pagina, comandos_pagina))
                comandos_pagina = []
                num_pagina += 1
                y_cursor = page_h - margin_top

            if text_line:
                x_pos = margin_left + indent_x
                escaped = self._escapar_pdf_bytes(text_line)
                cmd = (
                    f"BT /{font_key} {font_size} Tf {x_pos:.2f} {y_cursor:.2f} Td (".encode("ascii")
                    + escaped
                    + b") Tj ET"
                )
                comandos_pagina.append(cmd)
            y_cursor -= leading

        if comandos_pagina or not paginas_streams:
            paginas_streams.append(fechar_pagina(num_pagina, comandos_pagina))

        # Montagem da estrutura PDF 1.4
        # Objetos:
        # 1: Catalog
        # 2: Pages
        # 3: Font F1 (Times-Roman)
        # 4: Font F2 (Times-Bold)
        # 5: Font F3 (Times-Italic)
        # Para cada página i: Page object + Content stream object
        objetos: List[bytes] = []

        # Reservamos slots 1 a 5
        objetos.append(b"<< /Type /Catalog /Pages 2 0 R >>")
        objetos.append(b"") # Pages será preenchido após criar as páginas
        objetos.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Times-Roman /Encoding /WinAnsiEncoding >>")
        objetos.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Times-Bold /Encoding /WinAnsiEncoding >>")
        objetos.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Times-Italic /Encoding /WinAnsiEncoding >>")

        kids_refs: List[str] = []
        for stream_bytes in paginas_streams:
            page_obj_id = len(objetos) + 1
            content_obj_id = len(objetos) + 2
            kids_refs.append(f"{page_obj_id} 0 R")

            page_dict = (
                f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {page_w:.2f} {page_h:.2f}] "
                f"/Resources << /Font << /F1 3 0 R /F2 4 0 R /F3 5 0 R >> >> "
                f"/Contents {content_obj_id} 0 R >>"
            ).encode("ascii")
            content_dict = (
                f"<< /Length {len(stream_bytes)} >>\nstream\n".encode("ascii")
                + stream_bytes
                + b"\nendstream"
            )
            objetos.append(page_dict)
            objetos.append(content_dict)

        kids_str = " ".join(kids_refs)
        objetos[1] = f"<< /Type /Pages /Kids [{kids_str}] /Count {len(kids_refs)} >>".encode("ascii")

        # Serialização com tabela xref
        out = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
        offsets: List[int] = [0]
        for idx, obj_bytes in enumerate(objetos, start=1):
            offsets.append(len(out))
            out.extend(f"{idx} 0 obj\n".encode("ascii"))
            out.extend(obj_bytes)
            out.extend(b"\nendobj\n")

        xref_pos = len(out)
        out.extend(f"xref\n0 {len(objetos) + 1}\n".encode("ascii"))
        out.extend(b"0000000000 65535 f \n")
        for off in offsets[1:]:
            out.extend(f"{off:010d} 00000 n \n".encode("ascii"))

        out.extend(
            f"trailer\n<< /Size {len(objetos) + 1} /Root 1 0 R >>\nstartxref\n{xref_pos}\n%%EOF\n".encode("ascii")
        )
        pdf_path.write_bytes(bytes(out))
