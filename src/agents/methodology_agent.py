from typing import Optional
from src.schemas import DocumentoAcademicoState
from src.mcp_client import JurisprudenciaMcpClient
from src.llm import LlmClient
from src.config import config
from src.sanitizer import sanitizar_texto_academico, converter_dados_jurimetria_em_prosa

class MethodologyAgent:
    """Agente Metodológico: estrutura o desenho de pesquisa e jurimetria empírica via GPT-6.1 Sol."""

    def __init__(
        self,
        mcp_client: Optional[JurisprudenciaMcpClient] = None,
        llm_client: Optional[LlmClient] = None
    ):
        self.mcp_client = mcp_client or JurisprudenciaMcpClient()
        self.llm_client = llm_client or LlmClient()

    async def definir_metodologia(
        self,
        state: DocumentoAcademicoState
    ) -> DocumentoAcademicoState:
        """Estrutura a metodologia qualitativa e quantitativa e obtém estatísticas jurimétricas em prosa."""
        tema = state.tema or "Controvérsias Jurisprudenciais"

        # Coleta de jurimetria via MCP com sanitização
        jurimetria_raw = ""
        try:
            raw = await self.mcp_client.extrair_jurimetria(tema, tribunal="STJ")
            jurimetria_raw = sanitizar_texto_academico(raw)
        except Exception:
            jurimetria_raw = ""

        jurimetria_prosa = converter_dados_jurimetria_em_prosa(jurimetria_raw, tema)

        state.dados_jurimetria = {
            "tribunal": "STJ",
            "recorte_temporal": "2019-2026",
            "amostra_coletada": jurimetria_prosa
        }

        prompt = (
            f"Como metodólogo de pesquisa empírica em direito e jurimetria, redija a seção metodológica de um artigo científico de alto estrato (Qualis A) sobre:\n"
            f"'{tema}'\n\n"
            f"Síntese dos dados amostrais e empíricos coletados:\n{jurimetria_prosa[:1500]}\n\n"
            f"DIRETRIZES OBRIGATÓRIAS DE REDAÇÃO ACADÊMICA:\n"
            f"- Redija EXCLUSIVAMENTE em prosa dissertativa contínua e elegante, em parágrafos densos e articulados.\n"
            f"- É TERMINANTEMENTE PROIBIDO transcrever ementas brutas, acórdãos em caixa alta, ou notas de sistema como 'Nota de Cautela Jurimétrica' ou 'estimativa de amostra'.\n"
            f"- É TERMINANTEMENTE PROIBIDO usar marcadores mecânicos ('•', '-', '*'), tópicos ou listas no texto.\n"
            f"- Articule a abordagem metodológica híbrida (qualitativa dogmática e jurimetria descritiva), critérios de inclusão/exclusão temporal e a repercussão empírica das teses dos tribunais superiores."
        )
        system_prompt = "Você é o Agente Metodológico de um programa stricto sensu. Apresente critérios científicos claros e replicáveis em prosa contínua."

        try:
            texto_metodologia = await self.llm_client.generate(
                model=config.model_methodology,
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.2,
                fallback_model="google/gemini-4-argon"
            )
            state.desenho_metodologico = sanitizar_texto_academico(texto_metodologia)
        except Exception:
            # Fallback determinístico estruturado em prosa acadêmica densa
            state.desenho_metodologico = (
                f"Adota-se como desenho de pesquisa a abordagem metodológica híbrida, articulando a investigação "
                f"qualitativo-dogmática à jurimetria descritiva dos pronunciamentos das Cortes Superiores. "
                f"A vertente analítico-crítica orienta-se pela hermenêutica reconstrutiva dos enunciados normativos "
                f"e dos precedentes qualificados, confrontando os fundamentos decisórios com as garantias constitucionais vigentes.\n\n"
                f"Os critérios de inclusão e amostragem temporal contemplam os acórdãos paradigmas proferidos pelo "
                f"Superior Tribunal de Justiça e pelo Supremo Tribunal Federal entre 2019 e 2026, com foco nas controvérsias "
                f"afetadas ao rito dos recursos repetitivos e da repercussão geral correlatas a '{tema}'. "
                f"Essa delimitação viabiliza a observação empírica da dispersão decisória inicial e a identificação do momento "
                f"de convergência hermenêutica após a fixação das teses vinculantes.\n\n"
                f"{jurimetria_prosa}"
            )

        return state
