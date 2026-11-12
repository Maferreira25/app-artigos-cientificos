import re
import shutil
import subprocess
from pathlib import Path
from typing import Dict, Any, Tuple, Optional
from src.schemas import DocumentoAcademicoState
from src.exporter import _resolver_ambiente_tex

class AcademicPaperImporter:
    """Importador e Parser de Documentos Acadêmicos Existentes (.md, .txt, .docx, .pdf)."""

    def __init__(self):
        self.env = _resolver_ambiente_tex()
        self.pandoc_bin = shutil.which("pandoc", path=self.env.get("PATH"))

    def converter_docx_para_markdown(self, docx_path: Path) -> str:
        """Converte documento DOCX para string Markdown via Pandoc ou python-docx."""
        if self.pandoc_bin:
            try:
                cmd = [self.pandoc_bin, str(docx_path), "-f", "docx", "-t", "markdown", "--wrap=none"]
                res = subprocess.run(cmd, capture_output=True, text=True, check=True, encoding="utf-8", timeout=30, env=self.env)
                if res.stdout.strip():
                    return res.stdout
            except Exception:
                pass

        try:
            import docx
            doc = docx.Document(str(docx_path))
            blocos = [p.text for p in doc.paragraphs if p.text.strip()]
            return "\n\n".join(blocos)
        except Exception as e:
            raise RuntimeError(f"Não foi possível extrair texto do arquivo .docx: {e}")

    def converter_pdf_para_markdown(self, pdf_path: Path) -> str:
        """Extrai texto de um documento PDF via PyMuPDF (fitz) ou pypdf."""
        try:
            import fitz  # PyMuPDF
            doc = fitz.open(str(pdf_path))
            paginas = [page.get_text("text") for page in doc]
            doc.close()
            texto = "\n\n".join(p.strip() for p in paginas if p.strip())
            if texto:
                return texto
        except Exception:
            pass

        try:
            from pypdf import PdfReader
            reader = PdfReader(str(pdf_path))
            paginas = [p.extract_text() or "" for p in reader.pages]
            texto = "\n\n".join(p.strip() for p in paginas if p.strip())
            if texto:
                return texto
        except Exception as e:
            raise RuntimeError(f"Não foi possível extrair texto do arquivo .pdf: {e}")

        raise RuntimeError("O arquivo PDF não contém texto extraível.")

    def carregar_arquivo(self, arquivo_path: Path | str) -> str:
        """Carrega o texto em Markdown a partir de arquivo .md, .txt, .docx ou .pdf."""
        path = Path(arquivo_path)
        if not path.exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {path}")

        ext = path.suffix.lower()
        if ext == ".docx":
            return self.converter_docx_para_markdown(path)
        elif ext == ".pdf":
            return self.converter_pdf_para_markdown(path)
        elif ext in (".md", ".txt", ".markdown"):
            return path.read_text(encoding="utf-8")
        else:
            raise ValueError(f"Extensão não suportada: '{ext}'. Use .md, .txt, .docx ou .pdf.")

    def parsear_para_estado(self, texto_markdown: str, titulo_fallback: Optional[str] = None) -> DocumentoAcademicoState:
        """Analisa o texto do paper existente e decompõe em seções acadêmicas estruturadas."""
        linhas = [l.strip() for l in texto_markdown.splitlines()]
        
        # 1. Extração do Título
        titulo = titulo_fallback or ""
        for linha in linhas:
            if linha.startswith("# "):
                titulo = linha.replace("#", "").strip()
                break
        if not titulo and linhas:
            titulo = linhas[0][:100]

        # 2. Decomposição das Seções (por cabeçalhos Markdown ## ou # numéricos)
        secoes: Dict[str, str] = {}
        secao_atual: Optional[str] = None
        buffer_secao: list[str] = []

        header_pattern = re.compile(r'^(#{1,3})\s+(.+)$')

        for linha in texto_markdown.splitlines():
            match = header_pattern.match(linha.strip())
            if match:
                header_level = len(match.group(1))
                header_text = match.group(2).strip()
                
                # Se for o título principal de nível 1 (# Titulo), não adiciona como capítulo
                if header_level == 1 and header_text.lower() == titulo.lower():
                    continue

                # Salva a seção anterior se tiver conteúdo e um nome válido
                if secao_atual and buffer_secao:
                    texto_secao = "\n".join(buffer_secao).strip()
                    if texto_secao:
                        secoes[secao_atual] = texto_secao
                    buffer_secao = []
                
                secao_atual = header_text
            
            if secao_atual:
                buffer_secao.append(linha)

        if secao_atual and buffer_secao:
            texto_secao = "\n".join(buffer_secao).strip()
            if texto_secao:
                secoes[secao_atual] = texto_secao

        # Se nenhuma seção com cabeçalho foi detectada, agrupa o texto em uma seção padrão
        if not secoes and texto_markdown.strip():
            secoes["1. Introdução e Desenvolvimento"] = texto_markdown.strip()

        # 3. Inferência de Problema, Hipótese e Tema sobre o documento completo
        problema = ""
        hipotese = ""
        tema = ""

        p_match = re.search(r'(?:problema(?:\s+de\s+pesquisa)?|questão(?:\s+central)?):\s*([^\n\.\?]+[\.\?])', texto_markdown, re.IGNORECASE)
        if p_match:
            problema = p_match.group(1).strip()
        h_match = re.search(r'hipótese(?:\s+central)?:\s*([^\n\.\?]+[\.\?])', texto_markdown, re.IGNORECASE)
        if h_match:
            hipotese = h_match.group(1).strip()
        t_match = re.search(r'(?:tema(?:\s+central)?):\s*([^\n\.]+)', texto_markdown, re.IGNORECASE)
        if t_match:
            tema = t_match.group(1).strip()

        if not tema:
            tema = titulo
        if not problema:
            problema = f"Em que medida a controvérsia sobre '{tema}' impõe critérios uniformes de segurança jurídica e estabilidade das relações materiais?"
        if not hipotese:
            hipotese = f"Hipótese: A indefinição jurisprudencial sobre '{tema}' demanda parâmetros dogmáticos estritos e respeito à integridade dos precedentes qualificados."

        state = DocumentoAcademicoState(
            titulo=titulo,
            tema=tema,
            problema_pesquisa=problema,
            hipotese=hipotese,
            capitulos=secoes
        )

        return state

