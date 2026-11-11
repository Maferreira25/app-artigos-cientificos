import os
import re
import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

class RagStore:
    """Gerencia o repositório local de documentos RAG em Markdown com metadados YAML."""

    def __init__(self, storage_dir: Optional[Path] = None):
        if storage_dir is None:
            from src.config import config
            self.storage_dir = config.corpus_dir
        else:
            self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def salvar_documento(
        self,
        doc_id: str,
        metadata: Dict[str, Any],
        content_markdown: str
    ) -> Path:
        """Salva documento estruturado em Markdown com YAML Frontmatter."""
        # Sanitizar nome de arquivo
        safe_id = re.sub(r'[^a-zA-Z0-9_\-\.]', '_', doc_id)
        if not safe_id.endswith(".md"):
            safe_id += ".md"
        
        file_path = self.storage_dir / safe_id
        yaml_header = yaml.dump(metadata, allow_unicode=True, sort_keys=False).strip()
        full_text = f"---\n{yaml_header}\n---\n\n{content_markdown.strip()}\n"
        
        file_path.write_text(full_text, encoding="utf-8")
        return file_path

    def carregar_documento(self, file_path_or_id: str | Path) -> Tuple[Dict[str, Any], str]:
        """Lê arquivo Markdown e extrai o dicionário YAML frontmatter e o corpo em texto."""
        path = Path(file_path_or_id)
        if not path.is_file():
            # Tentar localizar por id no diretório padrão
            candidate = self.storage_dir / (str(file_path_or_id) if str(file_path_or_id).endswith(".md") else f"{file_path_or_id}.md")
            if candidate.is_file():
                path = candidate
            else:
                raise FileNotFoundError(f"Documento não encontrado: {file_path_or_id}")

        text = path.read_text(encoding="utf-8")
        return self.extrair_frontmatter_e_conteudo(text)

    @staticmethod
    def extrair_frontmatter_e_conteudo(text: str) -> Tuple[Dict[str, Any], str]:
        """Separa metadados YAML e conteúdo Markdown de uma string."""
        pattern = r'^---\s*\n(.*?)\n---\s*\n(.*)$'
        match = re.match(pattern, text, re.DOTALL)
        if match:
            yaml_raw = match.group(1)
            body = match.group(2)
            try:
                metadata = yaml.safe_load(yaml_raw) or {}
            except Exception:
                metadata = {}
            return metadata, body.strip()
        return {}, text.strip()

    def listar_documentos(self) -> List[Dict[str, Any]]:
        """Lista todos os documentos indexados no diretório do corpus."""
        documentos = []
        for file in self.storage_dir.glob("*.md"):
            meta, body = self.carregar_documento(file)
            doc_info = {
                "file_name": file.name,
                "file_path": str(file),
                "metadata": meta,
                "preview": body[:200]
            }
            documentos.append(doc_info)
        return documentos

    def verificar_citacao_no_corpus(self, identificador_ou_termo: str) -> bool:
        """Verifica se um número de processo, tema ou termo chave consta no acervo do corpus."""
        termo_limpo = identificador_ou_termo.strip().lower()
        if not termo_limpo:
            return False
            
        for file in self.storage_dir.glob("*.md"):
            conteudo = file.read_text(encoding="utf-8").lower()
            if termo_limpo in conteudo:
                return True
        return False
