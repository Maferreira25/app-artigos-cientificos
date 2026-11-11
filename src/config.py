import os
from pathlib import Path
from dataclasses import dataclass
from dotenv import load_dotenv

# Carrega variáveis de ambiente do arquivo .env no diretório raiz
_base_dir = Path(__file__).resolve().parent.parent
load_dotenv(_base_dir / ".env", override=False)

@dataclass
class PipelineConfig:
    # Servidor MCP de Jurisprudência (Padrão: Bridge Cloudflare Workers HTTPS)
    mcp_url: str = os.getenv("MCP_URL", os.getenv("MCP_SERVER_URL", os.getenv("JURISPRUDENCIA_MCP_URL", "https://jurisprudenciaia-mcp.michel-aires2012.workers.dev")))
    mcp_bearer_token: str | None = os.getenv("MCP_BEARER_TOKEN", None)
    mcp_timeout: float = float(os.getenv("MCP_TIMEOUT", "120.0"))
    
    # Limiar acadêmico eliminatório
    approval_threshold: float = float(os.getenv("APPROVAL_THRESHOLD", "85.0"))
    
    # Diretórios de trabalho locais configuráveis
    base_dir: Path = _base_dir
    corpus_dir: Path = _base_dir / os.getenv("CORPUS_DIR", "corpus")
    drafts_dir: Path = _base_dir / os.getenv("DRAFTS_DIR", "drafts")
    output_dir: Path = _base_dir / os.getenv("OUTPUT_DIR", "output")
    templates_dir: Path = _base_dir / os.getenv("TEMPLATES_DIR", "templates")

    # Provedor e Chaves de API
    llm_provider: str = os.getenv("LLM_PROVIDER", "openrouter").lower()
    openrouter_api_key: str | None = os.getenv("OPENROUTER_API_KEY", None)

    # Modelos por Papel Acadêmico (Quadro 2)
    model_supervisor: str = os.getenv("MODEL_SUPERVISOR", "openai/gpt-6-astra")
    model_writer: str = os.getenv("MODEL_WRITER", "anthropic/claude-fable-5.2")
    model_literature: str = os.getenv("MODEL_LITERATURE", "google/gemini-4-argon")
    model_methodology: str = os.getenv("MODEL_METHODOLOGY", "openai/gpt-6.1-sol-pro")
    model_defense: str = os.getenv("MODEL_DEFENSE", "deepseek/deepseek-chat")

    def ensure_directories(self) -> None:
        """Garante a existência de todos os diretórios locais de trabalho."""
        self.corpus_dir.mkdir(parents=True, exist_ok=True)
        self.drafts_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.templates_dir.mkdir(parents=True, exist_ok=True)

config = PipelineConfig()
config.ensure_directories()
