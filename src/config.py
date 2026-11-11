import os
from pathlib import Path
from dataclasses import dataclass

@dataclass
class PipelineConfig:
    mcp_url: str = os.getenv("MCP_URL", os.getenv("JURISPRUDENCIA_MCP_URL", "http://localhost:8787"))
    mcp_bearer_token: str | None = os.getenv("MCP_BEARER_TOKEN", None)
    mcp_timeout: float = float(os.getenv("MCP_TIMEOUT", "120.0"))
    
    # Limiares acadêmicos
    approval_threshold: float = 85.0
    
    # Diretórios de trabalho locais
    base_dir: Path = Path(__file__).resolve().parent.parent
    corpus_dir: Path = base_dir / "corpus"
    drafts_dir: Path = base_dir / "drafts"
    output_dir: Path = base_dir / "output"
    templates_dir: Path = base_dir / "templates"

    def ensure_directories(self) -> None:
        """Garante a existência de todos os diretórios locais de trabalho."""
        self.corpus_dir.mkdir(parents=True, exist_ok=True)
        self.drafts_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.templates_dir.mkdir(parents=True, exist_ok=True)

config = PipelineConfig()
config.ensure_directories()
