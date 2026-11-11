from typing import Optional
from src.schemas import DocumentoAcademicoState
from src.mcp_client import JurisprudenciaMcpClient

class EpistemicAgent:
    """Agente Epistemológico: responsável por problematização, hipótese e delimitação do marco teórico.
    
    Integra-se ao MCP para checar teses consolidadas e overruling jurisprudencial.
    """

    def __init__(self, mcp_client: Optional[JurisprudenciaMcpClient] = None):
        self.mcp_client = mcp_client or JurisprudenciaMcpClient()

    async def formular_problema_e_hipotese(
        self,
        state: DocumentoAcademicoState,
        tema: str,
        recorte_tematico: Optional[str] = None
    ) -> DocumentoAcademicoState:
        """Formula o problema e a hipótese e pesquisa viragens jurisprudenciais no MCP."""
        state.tema = tema
        
        # Consulta de viragem / precedentes no MCP para fundamentar a novidade
        overruling_info = ""
        try:
            overruling_info = await self.mcp_client.mapear_overruling(tema)
        except Exception:
            overruling_info = "Análise doutrinária de mutação hermenêutica sem registro de overruling formal indexado."

        if not state.problema_pesquisa:
            state.problema_pesquisa = (
                f"Em que medida a interpretação jurisprudencial contemporânea acerca de '{tema}' "
                f"afeta a segurança jurídica e a estabilidade das relações materiais no direito brasileiro, "
                f"considerando a necessidade de critérios objetivos para a contenção de divergências entre cortes de vértice?"
            )
            
        if not state.hipotese:
            state.hipotese = (
                f"Hipótese: A ausência de parâmetros dogmáticos estritos na aplicação de precedentes sobre '{tema}' "
                f"gera dispersão decisória e imprevisibilidade, impondo a formulação de um critério hermenêutico uniforme "
                f"vinculado à integridade do ordenamento e aos precedentes qualificados."
            )

        if not state.marco_teorico:
            state.marco_teorico = (
                f"Marco Teórico Preliminar: Fundamentado na teoria dos precedentes judiciais (Michele Taruffo, Neil MacCormick), "
                f"na integridade e coerência de Ronald Dworkin e na dogmática constitucional da segurança jurídica.\n\n"
                f"Registro de Overruling / Mutação Jurisprudencial mapeado:\n{overruling_info}"
            )

        return state
