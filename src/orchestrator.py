import asyncio
from typing import Dict, Any, Optional, Callable
from src.schemas import (
    DocumentoAcademicoState,
    GateAvaliadoEnum,
    StatusDecisaoEnum,
    ParecerRevisaoGeralSchema,
    TipoDocumentoEnum
)
from src.mcp_client import JurisprudenciaMcpClient
from src.rag_store import RagStore
from src.llm import LlmClient
from src.agents.chief_academic_reviewer import ChiefAcademicReviewer
from src.agents.epistemic_agent import EpistemicAgent
from src.agents.literature_review_agent import LiteratureReviewAgent
from src.agents.methodology_agent import MethodologyAgent
from src.agents.sectional_writer_agent import SectionalWriterAgent
from src.agents.defense_validator_agent import DefenseValidatorAgent

class AcademicPipelineOrchestrator:
    """Orquestrador do Pipeline de Agentes com Supervisão e Quality Gates Eliminatórios."""

    def __init__(
        self,
        mcp_client: Optional[JurisprudenciaMcpClient] = None,
        rag_store: Optional[RagStore] = None,
        llm_client: Optional[LlmClient] = None,
        threshold: float = 85.0
    ):
        self.mcp_client = mcp_client or JurisprudenciaMcpClient()
        self.rag_store = rag_store or RagStore()
        self.llm_client = llm_client or LlmClient()
        self.reviewer = ChiefAcademicReviewer(threshold=threshold)
        
        self.epistemic_agent = EpistemicAgent(self.mcp_client, self.llm_client)
        self.lit_review_agent = LiteratureReviewAgent(self.mcp_client, self.rag_store, self.llm_client)
        self.methodology_agent = MethodologyAgent(self.mcp_client, self.llm_client)
        self.writer_agent = SectionalWriterAgent(self.mcp_client, self.llm_client)
        self.defense_agent = DefenseValidatorAgent(self.mcp_client, self.rag_store, self.llm_client)

    async def executar_pipeline_completo(
        self,
        titulo: str,
        tema: str,
        progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
        tipo_documento: TipoDocumentoEnum = TipoDocumentoEnum.ARTIGO_CIENTIFICO
    ) -> DocumentoAcademicoState:
        """Executa a máquina de estados completa com supervisão passo a passo."""
        state = DocumentoAcademicoState(titulo=titulo, tema=tema, tipo_documento=tipo_documento)

        def _notify(gate: str, status: str, message: str, parecer: Optional[ParecerRevisaoGeralSchema] = None):
            if progress_callback:
                payload: Dict[str, Any] = {
                    "gate": gate,
                    "status": status,
                    "message": message,
                }
                if parecer:
                    payload["score"] = parecer.score_global
                    payload["decisao"] = parecer.status_decisao.value
                    payload["autorizado"] = parecer.autorizacao_avanco
                    payload["diagnostico"] = parecer.diagnostico_critico
                progress_callback(payload)

        # -------------------------------------------------------------
        # Gate 1: Epistemologia e Problematização (GPT-6 Astra)
        # -------------------------------------------------------------
        msg_g1 = f"[Gate 1] Epistemologia e Problematizacao ({self.llm_client.api_key and 'GPT-6 Astra' or 'Offline'})..."
        print(msg_g1)
        _notify(GateAvaliadoEnum.GATE_1_EPISTEMICO.value, "RUNNING", msg_g1)
        state.gate_atual = GateAvaliadoEnum.GATE_1_EPISTEMICO
        state = await self.epistemic_agent.formular_problema_e_hipotese(state, tema)
        parecer_g1 = self.reviewer.avaliar_gate_1_epistemico(state)
        state.pareceres_gates[GateAvaliadoEnum.GATE_1_EPISTEMICO.value] = parecer_g1
        _notify(GateAvaliadoEnum.GATE_1_EPISTEMICO.value, "DONE" if parecer_g1.autorizacao_avanco else "FAILED", parecer_g1.diagnostico_critico, parecer_g1)
        if not parecer_g1.autorizacao_avanco:
            state.status_geral = "REPROVADO_GATE_1"
            state.refatoracao_pendente = True
            return state

        # -------------------------------------------------------------
        # Gate 2: Revisão Bibliográfica e Precedentes MCP (Gemini 4 Argon)
        # -------------------------------------------------------------
        msg_g2 = f"[Gate 2] Revisao Bibliografica RSL e Precedentes MCP ({self.llm_client.api_key and 'Gemini 4 Argon' or 'Offline'})..."
        print(msg_g2)
        _notify(GateAvaliadoEnum.GATE_2_BIBLIOGRAFICO.value, "RUNNING", msg_g2)
        state.gate_atual = GateAvaliadoEnum.GATE_2_BIBLIOGRAFICO
        state = await self.lit_review_agent.conduzir_revisao_bibliografica(state)
        parecer_g2 = self.reviewer.avaliar_gate_2_bibliografico(state)
        state.pareceres_gates[GateAvaliadoEnum.GATE_2_BIBLIOGRAFICO.value] = parecer_g2
        _notify(GateAvaliadoEnum.GATE_2_BIBLIOGRAFICO.value, "DONE" if parecer_g2.autorizacao_avanco else "FAILED", parecer_g2.diagnostico_critico, parecer_g2)
        if not parecer_g2.autorizacao_avanco:
            state.status_geral = "REPROVADO_GATE_2"
            state.refatoracao_pendente = True
            return state

        # -------------------------------------------------------------
        # Gate 3: Metodologia e Jurimetria Empírica (GPT-6.1 Sol)
        # -------------------------------------------------------------
        msg_g3 = f"[Gate 3] Metodologia e Jurimetria Empirica ({self.llm_client.api_key and 'GPT-6.1 Sol' or 'Offline'})..."
        print(msg_g3)
        _notify(GateAvaliadoEnum.GATE_3_METODOLOGICO.value, "RUNNING", msg_g3)
        state.gate_atual = GateAvaliadoEnum.GATE_3_METODOLOGICO
        state = await self.methodology_agent.definir_metodologia(state)
        parecer_g3 = self.reviewer.avaliar_gate_3_metodologico(state)
        state.pareceres_gates[GateAvaliadoEnum.GATE_3_METODOLOGICO.value] = parecer_g3
        _notify(GateAvaliadoEnum.GATE_3_METODOLOGICO.value, "DONE" if parecer_g3.autorizacao_avanco else "FAILED", parecer_g3.diagnostico_critico, parecer_g3)
        if not parecer_g3.autorizacao_avanco:
            state.status_geral = "REPROVADO_GATE_3"
            state.refatoracao_pendente = True
            return state

        # -------------------------------------------------------------
        # Gate 4: Redação Seccional Modular (Claude Fable 5.2)
        # -------------------------------------------------------------
        msg_g4 = f"[Gate 4] Redacao Seccional Modular ({self.llm_client.api_key and 'Claude Fable 5.2' or 'Offline'})..."
        print(msg_g4)
        _notify(GateAvaliadoEnum.GATE_4_REDACAO_SECCIONAL.value, "RUNNING", msg_g4)
        state.gate_atual = GateAvaliadoEnum.GATE_4_REDACAO_SECCIONAL
        state = await self.writer_agent.redigir_secoes(state)
        parecer_g4 = self.reviewer.avaliar_gate_4_redacao_seccional(state)
        state.pareceres_gates[GateAvaliadoEnum.GATE_4_REDACAO_SECCIONAL.value] = parecer_g4
        _notify(GateAvaliadoEnum.GATE_4_REDACAO_SECCIONAL.value, "DONE" if parecer_g4.autorizacao_avanco else "FAILED", parecer_g4.diagnostico_critico, parecer_g4)
        if not parecer_g4.autorizacao_avanco:
            state.status_geral = "REPROVADO_GATE_4"
            state.refatoracao_pendente = True
            return state

        # -------------------------------------------------------------
        # Gate 5: Auditoria Anti-Alucinação e Banca Sintética (DeepSeek)
        # -------------------------------------------------------------
        msg_g5 = f"[Gate 5] Auditoria Anti-Alucinacao e Banca Sintetica ({self.llm_client.api_key and 'DeepSeek' or 'Offline'})..."
        print(msg_g5)
        _notify(GateAvaliadoEnum.GATE_5_CITACOES_BANCA.value, "RUNNING", msg_g5)
        state.gate_atual = GateAvaliadoEnum.GATE_5_CITACOES_BANCA
        erros_citacao, parecer_banca = await self.defense_agent.submeter_a_banca_sintetica(state)
        parecer_g5 = self.reviewer.avaliar_gate_5_citacoes_banca(state, audit_erros=erros_citacao)
        state.pareceres_gates[GateAvaliadoEnum.GATE_5_CITACOES_BANCA.value] = parecer_g5
        _notify(GateAvaliadoEnum.GATE_5_CITACOES_BANCA.value, "DONE" if parecer_g5.autorizacao_avanco else "FAILED", parecer_g5.diagnostico_critico, parecer_g5)
        if not parecer_g5.autorizacao_avanco:
            state.status_geral = "REPROVADO_GATE_5"
            state.refatoracao_pendente = True
            return state

        # -------------------------------------------------------------
        # Gate 6: Homologação Final para Compilação (Supervisor GPT-6 Astra)
        # -------------------------------------------------------------
        msg_g6 = "[Gate 6] Homologacao Final do Revisor Geral..."
        print(msg_g6)
        _notify(GateAvaliadoEnum.GATE_6_HOMOLOGACAO_FINAL.value, "RUNNING", msg_g6)
        parecer_g6 = self.reviewer.avaliar_gate_6_homologacao_final(state)
        state.pareceres_gates[GateAvaliadoEnum.GATE_6_HOMOLOGACAO_FINAL.value] = parecer_g6
        _notify(GateAvaliadoEnum.GATE_6_HOMOLOGACAO_FINAL.value, "DONE" if parecer_g6.autorizacao_avanco else "FAILED", parecer_g6.diagnostico_critico, parecer_g6)
        if not parecer_g6.autorizacao_avanco:
            state.status_geral = "REPROVADO_GATE_6"
            state.refatoracao_pendente = True
            return state

        state.status_geral = "HOMOLOGADO_SUCESSO"
        state.refatoracao_pendente = False
        return state
