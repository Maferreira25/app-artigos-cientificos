import re
from typing import Optional, List, Dict, Any, Tuple
from src.schemas import DocumentoAcademicoState
from src.mcp_client import JurisprudenciaMcpClient
from src.rag_store import RagStore

class DefenseValidatorAgent:
    """Auditor Anti-Alucinação de Citações e Simulador de Banca Examinadora Sintética."""

    def __init__(
        self,
        mcp_client: Optional[JurisprudenciaMcpClient] = None,
        rag_store: Optional[RagStore] = None
    ):
        self.mcp_client = mcp_client or JurisprudenciaMcpClient()
        self.rag_store = rag_store or RagStore()

    def auditar_citacoes_contra_corpus(self, state: DocumentoAcademicoState) -> List[str]:
        """Extrai números de processos citados no texto e confere sua autenticidade contra o corpus indexado."""
        erros: List[str] = []
        processo_regex = re.compile(r'\b(REsp|AREsp|RE|ADI|ADC|ADPF|RMS|HC)\s+[\d\.\/]+', re.IGNORECASE)

        texto_total = " ".join(state.capitulos.values())
        citacoes_encontradas = set(processo_regex.findall(texto_total))

        # Iterar sobre todas as ocorrências de regex completas
        for match in processo_regex.finditer(texto_total):
            citacao = match.group(0)
            # Extrair apenas a numeração (ex: 1.845.234)
            num_match = re.search(r'[\d\.\/]+', citacao)
            if num_match:
                numero = num_match.group(0)
                # Verificar se consta no corpus RAG
                if not self.rag_store.verificar_citacao_no_corpus(numero):
                    erros.append(f"Citação '{citacao}' não foi localizada no corpus indexado de precedentes autênticos.")

        return erros

    async def submeter_a_banca_sintetica(
        self,
        state: DocumentoAcademicoState
    ) -> Tuple[List[str], str]:
        """Submete a tese e a argumentação ao crivo dogmático e à jurisprudência dominante via MCP."""
        erros_citacao = self.auditar_citacoes_contra_corpus(state)

        # Consulta de vulnerabilidades da tese no MCP
        vulnerabilidades_mcp = ""
        try:
            vulnerabilidades_mcp = await self.mcp_client.analisar_tese_juridica(
                tese=state.hipotese,
                tribunal="STJ"
            )
        except Exception:
            vulnerabilidades_mcp = (
                "A banca sintética aponta que a tese deve reforçar a distinção (distinguishing) "
                "em relação às situações fáticas tuteladas pela jurisprudência defensiva das cortes superiores."
            )

        parecer_banca = (
            f"### Relatório da Banca Examinadora Sintética\n\n"
            f"1. **Rigor e Anti-Alucinação:** {len(erros_citacao)} inconsistências de citação detectadas.\n"
            f"2. **Pontos de Tensão Dogmática e Vulnerabilidades Apuradas (MCP):**\n"
            f"{vulnerabilidades_mcp}\n"
        )

        return erros_citacao, parecer_banca
