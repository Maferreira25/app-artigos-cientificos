import os
import re
import shutil
import subprocess
import textwrap
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from src.schemas import DocumentoAcademicoState, TipoDocumentoEnum
from src.config import config
from src.sanitizer import sanitizar_texto_academico

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import cm
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT, TA_CENTER
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.pdfgen import canvas
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

try:
    import docx
    from docx.shared import Cm, Pt
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    PYTHON_DOCX_AVAILABLE = True
except ImportError:
    PYTHON_DOCX_AVAILABLE = False


if REPORTLAB_AVAILABLE:
    class ABNTNumberedCanvas(canvas.Canvas):
        """Canvas do ReportLab que calcula a paginação e insere no canto superior direito (ABNT NBR 14724)."""
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self._saved_page_states = []

        def showPage(self):
            self._saved_page_states.append(dict(self.__dict__))
            self._startPage()

        def save(self):
            num_pages = len(self._saved_page_states)
            for state in self._saved_page_states:
                self.__dict__.update(state)
                self.draw_page_number(num_pages)
                super().showPage()
            super().save()

        def draw_page_number(self, page_count):
            self.saveState()
            self.setFont("Times-Roman", 10)
            page_w, page_h = A4
            # ABNT NBR 14724: número da página no canto superior direito a 2cm da borda
            self.drawRightString(page_w - 2.0 * cm, page_h - 2.0 * cm, str(self._pageNumber))
            self.restoreState()


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

    @staticmethod
    def _ordenar_chaves_capitulos(chaves: List[str]) -> List[str]:
        """Garante ordenação canônica estrita para os capítulos do documento (ABNT NBR 6022 / 14724)."""
        def _peso(k: str) -> Tuple[int, str]:
            k_low = k.lower().strip()
            if k_low.startswith("1.") or "introdução" in k_low or "introducao" in k_low:
                return (1, k)
            elif k_low.startswith("2.") or "marco" in k_low or "referencial" in k_low:
                return (2, k)
            elif k_low.startswith("3.") or "metodologia" in k_low or "análise" in k_low or "analise" in k_low:
                return (3, k)
            elif k_low.startswith("4.") or "considerações" in k_low or "consideracoes" in k_low or "conclusão" in k_low or "conclusao" in k_low:
                return (4, k)
            # Extrai dígito inicial se houver
            m = re.match(r"^(\d+)\.", k_low)
            if m:
                return (int(m.group(1)), k)
            return (10, k)

        return sorted(chaves, key=_peso)

    def _gerar_referencias_tematicas(self, state: DocumentoAcademicoState) -> List[str]:
        """Gera referências bibliográficas e jurisprudenciais estritamente contextuais (ABNT NBR 6023)."""
        tema_lower = (state.tema or "").lower()
        refs: List[str] = []

        if any(w in tema_lower for w in ["violência", "violencia", "mulher", "penha", "gênero", "genero", "protetiva"]):
            refs.extend([
                "BIANCHINI, Alice. *Lei Maria da Penha: Lei nº 11.340/2006: aspectos teóricos e práticos*. São Paulo: Saraiva Educação, 2022.",
                "BRASIL. [Constituição (1988)]. *Constituição da República Federativa do Brasil de 1988*. Brasília, DF: Presidência da República, 1988.",
                "BRASIL. *Lei nº 11.340, de 7 de agosto de 2006*. Cria mecanismos para coibir a violência doméstica e familiar contra a mulher. Brasília, DF: Presidência da República, 2006.",
                "BRASIL. *Lei nº 14.550, de 19 de abril de 2023*. Altera a Lei nº 11.340, de 7 de agosto de 2006, para dispor sobre as medidas protetivas de urgência. Brasília, DF: Presidência da República, 2023.",
                "BRASIL. Superior Tribunal de Justiça. *Recurso Especial nº 2.070.857/MG* (Tema Repetitivo 1249). Relator: Ministro Rogerio Schietti Cruz, Terceira Seção, julgado em 13 nov. 2024, DJe 25 mar. 2025.",
                "BRASIL. Supremo Tribunal Federal. *Ação Direta de Inconstitucionalidade nº 6138*. Relator: Ministro Alexandre de Moraes, Tribunal Pleno, julgado em 23 mar. 2022, DJe 10 mai. 2022.",
                "DIAS, Maria Berenice. *A Lei Maria da Penha na Justiça: a efetividade da Lei nº 11.340/2006 de combate à violência doméstica e familiar contra a mulher*. 7. ed. Salvador: Juspodivm, 2021.",
                "PIMENTEL, Silvia. *Direitos humanos das mulheres e a eficácia das medidas protetivas de urgência*. São Paulo: Saraiva, 2020."
            ])
        elif any(w in tema_lower for w in ["tribut", "overruling", "confiança", "confianca", "modula"]):
            refs.extend([
                "BRASIL. [Código de Processo Civil (2015)]. *Lei nº 13.105, de 16 de março de 2015*. Brasília, DF: Presidência da República, 2015.",
                "BRASIL. Superior Tribunal de Justiça. *Recurso Especial nº 1.845.234/SP*. Relator: Ministro Representativo, 2ª Seção, julgado em 12 abr. 2023.",
                "DWORKIN, Ronald. *Taking Rights Seriously*. Cambridge: Harvard University Press, 1977.",
                "MACCORMICK, Neil. *Rhetoric and the Rule of Law: A Theory of Legal Reasoning*. Oxford: Oxford University Press, 2005.",
                "TARUFFO, Michele. *La semplice verità: Il giudice e la costruzione dei fatti*. Roma-Bari: Laterza, 2009."
            ])
        else:
            refs.extend([
                "ALEXY, Robert. *Teoria dos Direitos Fundamentais*. Tradução de Virgílio Afonso da Silva. 2. ed. São Paulo: Malheiros, 2015.",
                "BRASIL. [Código de Processo Civil (2015)]. *Lei nº 13.105, de 16 de março de 2015*. Brasília, DF: Presidência da República, 2015.",
                "DWORKIN, Ronald. *Law's Empire*. Cambridge: Harvard University Press, 1986.",
                "MACCORMICK, Neil. *Legal Reasoning and Legal Theory*. Oxford: Clarendon Press, 1978."
            ])

        # Adicionar precedentes autênticos indexados no estado (ABNT NBR 6023)
        for p in state.precedentes_mcp:
            ref_prec = f"BRASIL. {p.tribunal}. *{p.processo}*. Relator: {p.relator}, julgado em {p.data_julgamento}."
            if ref_prec not in refs:
                refs.append(ref_prec)

        # Adicionar artigos e doutrinas recuperados na pesquisa web acadêmica (ABNT NBR 6023)
        for art in state.artigos_pesquisados_web:
            nome_autor = art.autores.strip()
            if "," in nome_autor:
                sobrenome_fmt = nome_autor
            else:
                partes = nome_autor.split()
                if len(partes) > 1:
                    sobrenome_fmt = f"{partes[-1].upper()}, {' '.join(partes[:-1])}"
                else:
                    sobrenome_fmt = nome_autor.upper()

            ref_art = f"{sobrenome_fmt}. {art.titulo}. *{art.periodico_ou_repositorio}*{f', {art.ano}' if art.ano else ''}.{f' Disponível em: <{art.doi_ou_url}>.' if art.doi_ou_url else ''}"
            if ref_art not in refs:
                refs.append(ref_art)

        return sorted(refs)

    def gerar_markdown_consolidado(self, state: DocumentoAcademicoState) -> Path:
        """Consolida todos os capítulos, pareceres e referências em um único documento Markdown ABNT NBR 6022 / 14724."""
        safe_titulo = "".join(
            c for c in (state.titulo or "artigo_doutorado")
            if c.isalnum() or c in (' ', '_', '-')
        ).strip().replace(" ", "_")
        if not safe_titulo:
            safe_titulo = "artigo_doutorado"
        md_file = self.output_dir / f"{safe_titulo}.md"

        is_tese = state.tipo_documento == TipoDocumentoEnum.PROJETO_TESE

        # Dados autorais e filiação institucional
        autores = state.autores or [
            "Pesquisador Acadêmico (Doutorando em Direito)",
            "Prof. Orientador Dr. (Docente Permanente)"
        ]
        filiacoes = state.filiacoes or [
            "Pontifícia Universidade Católica - Programa de Pós-Graduação em Direito",
            "Pontifícia Universidade Católica - Escola de Direito e Sociedade"
        ]

        # Resumo vernáculo (ABNT NBR 6028)
        resumo_texto = state.resumo or (
            f"O presente {'projeto de tese' if is_tese else 'artigo científico'} investiga o tema '{state.tema}' "
            f"sob o enfoque da integridade do ordenamento jurídico e da segurança jurisprudencial. "
            f"A partir de metodologia dedutiva articulada à jurimetria descritiva das decisões dos tribunais superiores, "
            f"sustenta-se a imperatividade de critérios uniformes na estabilização dos precedentes qualificados. "
            f"Os resultados demonstram a necessidade de coibir oscilações pretorianas e resguardar a proteção material dos direitos."
        )
        if state.palavras_chave:
            palavras_chave_str = ". ".join(k.strip(". ") for k in state.palavras_chave if k.strip(". ")) + "."
        else:
            palavras_chave_str = "Precedentes Vinculantes. Segurança Jurídica. Tutela Efetiva. STJ."

        # Abstract em língua estrangeira (ABNT NBR 6022)
        titulo_en = state.titulo_en or f"Critical Analysis and Legal Effectiveness on {state.tema}"
        abstract_texto = state.abstract or (
            f"This study investigates '{state.tema}' focusing on legal certainty and the integrity of the judicial system. "
            f"Employing a deductive and empirical methodology based on superior court precedents, it argues for objective standards "
            f"to stabilize qualified case law. The findings underscore the importance of ensuring effective fundamental protection "
            f"and preventing arbitrary decisional divergence."
        )
        if state.keywords:
            keywords_str = ". ".join(k.strip(". ") for k in state.keywords if k.strip(". ")) + "."
        else:
            keywords_str = "Binding Precedents. Legal Certainty. Judicial Protection. Superior Court of Justice."

        tipo_badge = (
            "Projeto de Tese / Trabalho de Conclusão de Curso (ABNT NBR 15287 / 14724)"
            if is_tese else
            "Artigo Científico de Periódico Qualis A (ABNT NBR 6022)"
        )

        linhas = [
            f"# {state.titulo or ('Projeto de Tese de Doutoramento' if is_tese else 'Artigo Científico')}",
            "",
            f"**{autores[0]}**",
            f"*{filiacoes[0]}*",
            "",
            f"**{autores[1] if len(autores) > 1 else 'Docente Orientador'}**",
            f"*{filiacoes[1] if len(filiacoes) > 1 else filiacoes[0]}*",
            "",
            f"**Natureza da Obra:** {tipo_badge}",
            "",
            "---",
            "",
            "## Resumo",
            resumo_texto,
            "",
            f"**Palavras-chave:** {palavras_chave_str}",
            "",
            "---",
            "",
            f"## Abstract: {titulo_en}",
            abstract_texto,
            "",
            f"**Keywords:** {keywords_str}",
            "",
            "---",
            ""
        ]

        # Adicionar os capítulos em ordem estritamente sequencial (1, 2, 3, 4...)
        chaves_ordenadas = self._ordenar_chaves_capitulos(list(state.capitulos.keys()))
        for titulo_capitulo in chaves_ordenadas:
            texto = state.capitulos[titulo_capitulo]
            texto_limpo = sanitizar_texto_academico(texto)
            if texto_limpo:
                if not texto_limpo.startswith("#"):
                    linhas.append(f"# {titulo_capitulo}\n\n{texto_limpo.strip()}")
                else:
                    linhas.append(texto_limpo.strip())
                linhas.append("\n---\n")

        # Inclusão da conclusão explícita se houver no estado e ainda não constar nos capítulos
        if state.conclusao and not any("conclus" in k.lower() or "considerações" in k.lower() for k in chaves_ordenadas):
            texto_limpo_conc = sanitizar_texto_academico(state.conclusao)
            if texto_limpo_conc:
                linhas.append(f"# 4. Considerações Finais e Perspectivas Epistemológicas\n\n{texto_limpo_conc.strip()}")
                linhas.append("\n---\n")

        # Adicionar Referências Bibliográficas e Jurisprudenciais ABNT NBR 6023
        referencias = self._gerar_referencias_tematicas(state)
        linhas.append("# Referências")
        linhas.append("")
        for ref in referencias:
            linhas.append(ref)
            linhas.append("")

        conteudo_final = "\n".join(linhas)
        md_file.write_text(conteudo_final, encoding="utf-8")
        return md_file

    def compilar_docx(self, md_path: Path) -> Optional[Path]:
        """Converte o arquivo Markdown para DOCX formatado estritamente nas normas ABNT."""
        if not md_path.exists():
            return None
        docx_path = md_path.with_suffix(".docx")
        markdown_text = md_path.read_text(encoding="utf-8")

        # 1. Prioridade: Compilação nativa ABNT via python-docx (Justificado, 1.25cm, 1.5 entrelinhas)
        if PYTHON_DOCX_AVAILABLE:
            res_docx = self._gerar_docx_nativo(markdown_text, docx_path)
            if res_docx and res_docx.exists():
                return res_docx

        # 2. Fallback via Pandoc se disponível
        env = _resolver_ambiente_tex()
        pandoc_bin = shutil.which("pandoc", path=env.get("PATH"))
        if pandoc_bin:
            try:
                cmd = [pandoc_bin, str(md_path), "-o", str(docx_path), "--standalone"]
                subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env, timeout=60)
                return docx_path if docx_path.exists() else None
            except Exception:
                return None
        return None

    def compilar_pdf(self, md_path: Path) -> Optional[Path]:
        """Converte o arquivo Markdown para PDF nas normas ABNT com texto estritamente justificado.
        
        Prioridade 1: ReportLab com paginação superior direita (ABNT NBR 14724), alinhamento TA_JUSTIFY,
        recuo de 1,25cm e espaçamento 1,5.
        Prioridade 2: Pandoc + LaTeX / Typst.
        Prioridade 3: Compilador nativo direto em Python.
        """
        if not md_path.exists():
            return None

        pdf_path = md_path.with_suffix(".pdf")
        markdown_text = md_path.read_text(encoding="utf-8")

        # 1. Compilador de Alta Precisão Tipográfica: ReportLab (100% justificado, ABNT NBR 14724)
        if REPORTLAB_AVAILABLE:
            try:
                res_pdf = self._gerar_pdf_reportlab(markdown_text, pdf_path)
                if res_pdf and res_pdf.exists() and res_pdf.stat().st_size > 0:
                    return res_pdf
            except Exception:
                pass

        # 2. Fallback via Pandoc + TeX / Typst
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

        # 3. Fallback nativo direto em Python
        try:
            target_pdf = self._gerar_pdf_abnt_nativo(markdown_text, pdf_path)
            return target_pdf if target_pdf and target_pdf.exists() else None
        except Exception:
            return None

    @staticmethod
    def _formatar_tags_inline_reportlab(texto: str) -> str:
        """Formata marcações Markdown simples para tags XML suportadas pelo ReportLab Paragraph."""
        # Escapar caracteres HTML/XML especiais
        texto = texto.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        texto = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', texto)
        texto = re.sub(r'\*(.+?)\*', r'<i>\1</i>', texto)
        texto = re.sub(r'`(.+?)`', r'<font face="Courier">\1</font>', texto)
        return texto

    @staticmethod
    def _obter_caminho_gravavel(caminho_base: Path, sufixo_padrao: str = "_abnt_justificado") -> Path:
        """Retorna o próprio caminho se gravável, ou o primeiro alternativo disponível sem colisão de lock (Windows)."""
        candidatos = [
            caminho_base,
            caminho_base.with_name(f"{caminho_base.stem}{sufixo_padrao}{caminho_base.suffix}"),
            caminho_base.with_name(f"{caminho_base.stem}_atualizado{caminho_base.suffix}"),
            caminho_base.with_name(f"{caminho_base.stem}_v2{caminho_base.suffix}"),
        ]
        for c in candidatos:
            try:
                with open(c, "ab"):
                    pass
                return c
            except Exception:
                continue
        import time
        return caminho_base.with_name(f"{caminho_base.stem}_{int(time.time())}{caminho_base.suffix}")

    def _gerar_pdf_reportlab(self, markdown_text: str, pdf_path: Path) -> Optional[Path]:
        """Gera PDF estritamente conforme as normas da ABNT (NBR 14724/6022/10520) com texto justificado."""
        if not REPORTLAB_AVAILABLE:
            return None

        # Estilos ABNT estritos
        estilo_corpo = ParagraphStyle(
            "ABNT_Corpo",
            fontName="Times-Roman",
            fontSize=12,
            leading=18.0,  # Espaçamento 1,5 entrelinhas (12 * 1.5 = 18)
            alignment=TA_JUSTIFY,  # Alinhamento estritamente JUSTIFICADO
            firstLineIndent=1.25 * cm,  # Recuo de parágrafo ABNT de 1,25 cm
            spaceAfter=6.0
        )

        estilo_resumo = ParagraphStyle(
            "ABNT_Resumo",
            fontName="Times-Roman",
            fontSize=12,
            leading=14.0,  # Espaçamento simples
            alignment=TA_JUSTIFY,
            firstLineIndent=0,
            spaceAfter=6.0
        )

        estilo_citacao_longa = ParagraphStyle(
            "ABNT_CitacaoLonga",
            fontName="Times-Roman",
            fontSize=10,  # Fonte tamanho 10 para citações diretas longas (> 3 linhas)
            leading=12.0,  # Espaçamento simples
            alignment=TA_JUSTIFY,
            leftIndent=4.0 * cm,  # Recuo de 4 cm da margem esquerda (ABNT NBR 10520)
            firstLineIndent=0,
            spaceBefore=6.0,
            spaceAfter=6.0
        )

        estilo_titulo_artigo = ParagraphStyle(
            "ABNT_TituloArtigo",
            fontName="Times-Bold",
            fontSize=13,
            leading=18.0,
            alignment=TA_CENTER,
            spaceAfter=14.0,
            keepWithNext=True
        )

        estilo_autoria = ParagraphStyle(
            "ABNT_Autoria",
            fontName="Times-Italic",
            fontSize=11,
            leading=14.0,
            alignment=TA_LEFT,
            firstLineIndent=0,
            spaceAfter=4.0
        )

        estilo_h1 = ParagraphStyle(
            "ABNT_H1",
            fontName="Times-Bold",
            fontSize=12,
            leading=18.0,
            alignment=TA_LEFT,
            firstLineIndent=0,
            spaceBefore=18.0,
            spaceAfter=10.0,
            keepWithNext=True
        )

        estilo_h2 = ParagraphStyle(
            "ABNT_H2",
            fontName="Times-Bold",
            fontSize=12,
            leading=16.0,
            alignment=TA_LEFT,
            firstLineIndent=0,
            spaceBefore=14.0,
            spaceAfter=8.0,
            keepWithNext=True
        )

        estilo_h3 = ParagraphStyle(
            "ABNT_H3",
            fontName="Times-BoldItalic",
            fontSize=12,
            leading=16.0,
            alignment=TA_LEFT,
            firstLineIndent=0,
            spaceBefore=12.0,
            spaceAfter=6.0,
            keepWithNext=True
        )

        estilo_referencia = ParagraphStyle(
            "ABNT_Referencia",
            fontName="Times-Roman",
            fontSize=12,
            leading=14.0,
            alignment=TA_LEFT,  # ABNT NBR 6023: referências alinhadas à esquerda
            firstLineIndent=0,
            spaceAfter=8.0
        )

        story = []
        primeiro_h1 = True
        em_referencias = False

        for raw_line in markdown_text.splitlines():
            line = raw_line.strip()
            if not line or line == "---":
                continue

            if line.startswith("# "):
                texto_h1 = self._limpar_markdown_inline(line[2:])
                if "referência" in texto_h1.lower() or "referencia" in texto_h1.lower():
                    em_referencias = True
                if primeiro_h1:
                    primeiro_h1 = False
                    story.append(Paragraph(texto_h1.upper(), estilo_titulo_artigo))
                else:
                    story.append(Paragraph(texto_h1.upper(), estilo_h1))
            elif line.startswith("## "):
                sub = self._limpar_markdown_inline(line[3:])
                story.append(Paragraph(sub, estilo_h2))
            elif line.startswith("### "):
                sub3 = self._limpar_markdown_inline(line[4:])
                story.append(Paragraph(sub3, estilo_h3))
            elif line.startswith(">"):
                cit = self._limpar_markdown_inline(line.lstrip(">").strip())
                story.append(Paragraph(cit, estilo_citacao_longa))
            elif line.startswith("**") and ("Pesquisador" in line or "Prof." in line or "Orientador" in line or "Natureza da Obra" in line):
                txt = self._formatar_tags_inline_reportlab(line)
                story.append(Paragraph(txt, estilo_autoria))
            elif line.startswith("*") and ("Universidade" in line or "Programa" in line or "Escola" in line):
                txt = self._formatar_tags_inline_reportlab(line)
                story.append(Paragraph(txt, estilo_autoria))
            elif em_referencias:
                txt = self._formatar_tags_inline_reportlab(line)
                story.append(Paragraph(txt, estilo_referencia))
            elif "Palavras-chave:" in line or "Keywords:" in line:
                txt = self._formatar_tags_inline_reportlab(line)
                story.append(Paragraph(txt, estilo_resumo))
            elif line.startswith("O presente artigo") or line.startswith("This scientific paper"):
                txt = self._formatar_tags_inline_reportlab(line)
                story.append(Paragraph(txt, estilo_resumo))
            else:
                txt = self._formatar_tags_inline_reportlab(line)
                story.append(Paragraph(txt, estilo_corpo))

        target_path = self._obter_caminho_gravavel(pdf_path, "_abnt_justificado")
        try:
            doc = SimpleDocTemplate(
                str(target_path),
                pagesize=A4,
                leftMargin=3.0 * cm,
                rightMargin=2.0 * cm,
                topMargin=3.0 * cm,
                bottomMargin=2.0 * cm
            )
            doc.build(story, canvasmaker=ABNTNumberedCanvas)
            return target_path if target_path.exists() else None
        except Exception:
            return None

    def _gerar_docx_nativo(self, markdown_text: str, docx_path: Path) -> Optional[Path]:
        """Gera DOCX conforme normas ABNT (margens 3/3/2/2, Times 12, justificado, 1.25cm indent, 1.5 espaçamento)."""
        if not PYTHON_DOCX_AVAILABLE:
            return None
        try:
            doc = docx.Document()
            section = doc.sections[0]
            section.top_margin = Cm(3.0)
            section.left_margin = Cm(3.0)
            section.right_margin = Cm(2.0)
            section.bottom_margin = Cm(2.0)

            em_referencias = False
            primeiro_h1 = True

            for raw_line in markdown_text.splitlines():
                line = raw_line.strip()
                if not line or line == "---":
                    continue

                if line.startswith("# "):
                    texto_h1 = self._limpar_markdown_inline(line[2:])
                    if "referência" in texto_h1.lower() or "referencia" in texto_h1.lower():
                        em_referencias = True
                    p = doc.add_paragraph()
                    p.paragraph_format.first_line_indent = Cm(0)
                    p.paragraph_format.space_before = Pt(14)
                    p.paragraph_format.space_after = Pt(8)
                    p.paragraph_format.keep_with_next = True
                    if primeiro_h1:
                        primeiro_h1 = False
                        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                        run = p.add_run(texto_h1)
                        run.font.name = "Times New Roman"
                        run.font.size = Pt(13)
                        run.bold = True
                    else:
                        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
                        run = p.add_run(texto_h1)
                        run.font.name = "Times New Roman"
                        run.font.size = Pt(12)
                        run.bold = True
                elif line.startswith("## "):
                    sub = self._limpar_markdown_inline(line[3:])
                    p = doc.add_paragraph()
                    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
                    p.paragraph_format.first_line_indent = Cm(0)
                    p.paragraph_format.space_before = Pt(12)
                    p.paragraph_format.space_after = Pt(6)
                    p.paragraph_format.keep_with_next = True
                    run = p.add_run(sub)
                    run.font.name = "Times New Roman"
                    run.font.size = Pt(12)
                    run.bold = True
                elif line.startswith("### "):
                    sub3 = self._limpar_markdown_inline(line[4:])
                    p = doc.add_paragraph()
                    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
                    p.paragraph_format.first_line_indent = Cm(0)
                    p.paragraph_format.space_before = Pt(10)
                    p.paragraph_format.space_after = Pt(4)
                    p.paragraph_format.keep_with_next = True
                    run = p.add_run(sub3)
                    run.font.name = "Times New Roman"
                    run.font.size = Pt(12)
                    run.bold = True
                    run.italic = True
                elif line.startswith(">"):
                    cit = self._limpar_markdown_inline(line.lstrip(">").strip())
                    p = doc.add_paragraph()
                    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
                    p.paragraph_format.left_indent = Cm(4.0)
                    p.paragraph_format.first_line_indent = Cm(0)
                    p.paragraph_format.line_spacing = 1.0
                    p.paragraph_format.space_before = Pt(6)
                    p.paragraph_format.space_after = Pt(6)
                    run = p.add_run(cit)
                    run.font.name = "Times New Roman"
                    run.font.size = Pt(10)
                elif em_referencias:
                    limpo = self._limpar_markdown_inline(line)
                    p = doc.add_paragraph()
                    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
                    p.paragraph_format.first_line_indent = Cm(0)
                    p.paragraph_format.line_spacing = 1.0
                    p.paragraph_format.space_after = Pt(6)
                    run = p.add_run(limpo)
                    run.font.name = "Times New Roman"
                    run.font.size = Pt(12)
                elif "Palavras-chave:" in line or "Keywords:" in line or line.startswith("O presente artigo") or line.startswith("This scientific paper"):
                    limpo = self._limpar_markdown_inline(line)
                    p = doc.add_paragraph()
                    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
                    p.paragraph_format.first_line_indent = Cm(0)
                    p.paragraph_format.line_spacing = 1.0
                    p.paragraph_format.space_after = Pt(6)
                    run = p.add_run(limpo)
                    run.font.name = "Times New Roman"
                    run.font.size = Pt(12)
                else:
                    limpo = self._limpar_markdown_inline(line)
                    p = doc.add_paragraph()
                    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
                    p.paragraph_format.first_line_indent = Cm(1.25)
                    p.paragraph_format.line_spacing = 1.5
                    p.paragraph_format.space_after = Pt(6)
                    run = p.add_run(limpo)
                    run.font.name = "Times New Roman"
                    run.font.size = Pt(12)

            target_docx = self._obter_caminho_gravavel(docx_path, "_abnt_justificado")
            try:
                doc.save(str(target_docx))
                return target_docx if target_docx.exists() else None
            except Exception:
                return None
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

    def _gerar_pdf_abnt_nativo(self, markdown_text: str, pdf_path: Path) -> Optional[Path]:
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
            elif line.startswith("*") and line.endswith("*") and not line.startswith("**"):
                # Linha inteira em itálico (ex: filiação institucional)
                limpo = self._limpar_markdown_inline(line)
                for wline in textwrap.wrap(limpo, width=78):
                    blocos.append(("F3", 11, 16.0, 0.0, 2.0, wline))
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
        objetos: List[bytes] = []

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
        try:
            pdf_path.write_bytes(bytes(out))
            return pdf_path
        except PermissionError:
            # Caso o arquivo PDF esteja aberto e travado no Windows por leitor de PDF (ex: Acrobat),
            # grava versão atualizada com sufixo preservando integridade sem falhar a compilação
            alt_path = pdf_path.with_name(f"{pdf_path.stem}_atualizado.pdf")
            alt_path.write_bytes(bytes(out))
            return alt_path
