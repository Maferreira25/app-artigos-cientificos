import re
from typing import Optional, List, Dict, Any, Tuple
from src.schemas import DocumentoAcademicoState
from src.mcp_client import JurisprudenciaMcpClient
from src.rag_store import RagStore
from src.llm import LlmClient
from src.config import config

class DefenseValidatorAgent:
    """Auditor Anti-Alucinação de Citações e Simulador de Banca Examinadora Sintética via DeepSeek R1."""

    def __init__(
        self,
        mcp_client: Optional[JurisprudenciaMcpClient] = None,
        rag_store: Optional[RagStore] = None,
        llm_client: Optional[LlmClient] = None
    ):
        self.mcp_client = mcp_client or JurisprudenciaMcpClient()
        self.rag_store = rag_store or RagStore()
        self.llm_client = llm_client or LlmClient()

    def auditar_citacoes_contra_corpus(self, state: DocumentoAcademicoState) -> List[str]:
        """Extrai números de processos citados no texto e confere sua autenticidade contra o corpus indexado."""
        erros: List[str] = []
        processo_regex = re.compile(r'\b(REsp|AREsp|RE|ADI|ADC|ADPF|RMS|HC)\s+[\d\.\/]+', re.IGNORECASE)

        texto_total = " ".join(state.capitulos.values())

        for match in processo_regex.finditer(texto_total):
            citacao = match.group(0)
            num_match = re.search(r'[\d\.\/]+', citacao)
            if num_match:
                numero = num_match.group(0)
                if not self.rag_store.verificar_citacao_no_corpus(numero):
                    erros.append(f"Citação '{citacao}' não foi localizada no corpus indexado de precedentes autênticos.")

        return erros

    async def submeter_a_banca_sintetica(
        self,
        state: DocumentoAcademicoState
    ) -> Tuple[List[str], str]:
        """Submete a tese ao teste de fogo adversarial da banca examinadora sintética com DeepSeek R1."""
        erros_citacao = self.auditar_citacoes_contra_corpus(state)

        # 1. Consulta de vulnerabilidades da tese no MCP
        vulnerabilidades_mcp = ""
        try:
            vulnerabilidades_mcp = await self.mcp_client.analisar_tese_juridica(
                tese=state.hipotese,
                tribunal="STJ"
            )
        except Exception:
            vulnerabilidades_mcp = "Pontos de cautela da jurisprudência defensiva das cortes superiores."

        # 2. Análise crítica adversarial com DeepSeek R1
        prompt = (
            f"Você é uma Banca Examinadora de Doutorado extremamente rigorosa e adversarial.\n"
            f"Avalie a tese de doutorado proposta:\n"
            f"Tema: {state.tema}\n"
            f"Problema: {state.problema_pesquisa}\n"
            f"Hipótese: {state.hipotese}\n\n"
            f"Alertas de Precedentes e Jurisprudência do Servidor MCP:\n{vulnerabilidades_mcp}\n\n"
            f"Emita seu parecer crítico apontando:\n"
            f"1. As 3 maiores fragilidades ou contra-argumentos dogmáticos que o autor precisará defender.\n"
            f"2. Eventuais riscos de distinguishing forçado ou má aplicação de precedentes vinculantes.\n"
            f"3. Veredito sintético da banca examinadora."
        )
        system_prompt = "Você é um membro catedrático e adversarial de banca examinadora de pós-graduação stricto sensu. Não poupe críticas técnicas construtivas."

        parecer_banca_texto = ""
        try:
            parecer_banca_texto = await self.llm_client.generate(
                model=config.model_defense,
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.3,
                max_tokens=2500,
                fallback_model="deepseek/deepseek-chat"
            )
        except Exception:
            parecer_banca_texto = (
                "A banca examinadora sintética aponta a necessidade de delimitação precisa "
                "entre a hipótese fática do precedente e as particularidades do caso concreto (distinguishing)."
            )

        parecer_banca = (
            f"### Relatório da Banca Examinadora Sintética (DeepSeek R1 / MCP)\n\n"
            f"1. **Rigor e Anti-Alucinação:** {len(erros_citacao)} inconsistências de citação detectadas.\n\n"
            f"2. **Avaliação Crítica Adversarial da Banca:**\n"
            f"{parecer_banca_texto}\n"
        )

        return erros_citacao, parecer_banca
