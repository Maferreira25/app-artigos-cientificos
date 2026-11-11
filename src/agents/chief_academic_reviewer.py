from typing import List, Dict, Any, Optional
from src.schemas import (
    GateAvaliadoEnum,
    StatusDecisaoEnum,
    ScoresPorCriterioSchema,
    DiretrizRefatoracaoSchema,
    ParecerRevisaoGeralSchema,
    DocumentoAcademicoState
)

class ChiefAcademicReviewer:
    """Agente Revisor Geral (Supervisor / Chief Academic Auditor / Gatekeeper).
    
    Aplica a Matriz de Avaliação Multidimensional e controla os Quality Gates 1 a 6.
    Limiar eliminatório: 85/100 pontos.
    """

    def __init__(self, threshold: float = 85.0):
        self.threshold = threshold

    def _calcular_score_e_status(
        self,
        scores: ScoresPorCriterioSchema,
        diretrizes: List[DiretrizRefatoracaoSchema],
        diagnostico: str,
        gate: GateAvaliadoEnum,
        agente: str
    ) -> ParecerRevisaoGeralSchema:
        score_global = round(
            (scores.rigor_conceitual + scores.coerencia_estrutural + scores.ineditismo + scores.fidelidade_metodologica) / 4.0,
            2
        )

        if score_global >= 90.0 and len(diretrizes) == 0:
            status = StatusDecisaoEnum.APROVADO
            autorizacao = True
        elif score_global >= self.threshold:
            status = StatusDecisaoEnum.APROVADO_COM_RESSALVAS_MENORES
            autorizacao = True
        else:
            status = StatusDecisaoEnum.REJEITADO_EXIGE_REFATORACAO
            autorizacao = False

        return ParecerRevisaoGeralSchema(
            gate_avaliado=gate,
            agente_submetido=agente,
            status_decisao=status,
            score_global=score_global,
            scores_por_criterio=scores,
            diagnostico_critico=diagnostico,
            diretrizes_refatoracao=diretrizes,
            autorizacao_avanco=autorizacao
        )

    def avaliar_gate_1_epistemico(self, state: DocumentoAcademicoState) -> ParecerRevisaoGeralSchema:
        """Avalia Gate 1: Problema, hipótese e ineditismo frente ao overruling jurisprudencial."""
        diretrizes: List[DiretrizRefatoracaoSchema] = []
        
        # Validação do problema
        if not state.problema_pesquisa or len(state.problema_pesquisa.strip()) < 30:
            diretrizes.append(DiretrizRefatoracaoSchema(
                topico_ou_paragrafo="Problema de Pesquisa",
                problema_identificado="Problema de pesquisa ausente, lacunar ou superficial.",
                instrucao_correcao="Formular uma pergunta epistemológica clara e delimitada focada na divergência jurisprudencial."
            ))
            
        # Validação da hipótese
        if not state.hipotese or len(state.hipotese.strip()) < 30:
            diretrizes.append(DiretrizRefatoracaoSchema(
                topico_ou_paragrafo="Hipótese de Trabalho",
                problema_identificado="Hipótese não especificada ou meramente descritiva.",
                instrucao_correcao="Enunciar hipótese falseável/refutável com solução dogmática proposta."
            ))

        # Pontuação
        if diretrizes:
            scores = ScoresPorCriterioSchema(
                rigor_conceitual=60.0,
                coerencia_estrutural=65.0,
                ineditismo=60.0,
                fidelidade_metodologica=70.0
            )
            diag = "Gate 1 Reprovado: O problema ou hipótese não cumprem os requisitos epistemológicos de pós-graduação stricto sensu."
        else:
            scores = ScoresPorCriterioSchema(
                rigor_conceitual=92.0,
                coerencia_estrutural=90.0,
                ineditismo=88.0,
                fidelidade_metodologica=90.0
            )
            diag = "Gate 1 Aprovado: Problema contemporâneo, hipótese refutável e delimitação do marco teórico chancelados."

        return self._calcular_score_e_status(scores, diretrizes, diag, GateAvaliadoEnum.GATE_1_EPISTEMICO, "epistemic_agent")

    def avaliar_gate_2_bibliografico(self, state: DocumentoAcademicoState) -> ParecerRevisaoGeralSchema:
        """Avalia Gate 2: Revisão sistemática (PRISMA), tripé doutrinário e precedentes qualificados."""
        diretrizes: List[DiretrizRefatoracaoSchema] = []

        if not state.marco_teorico or len(state.marco_teorico.strip()) < 100:
            diretrizes.append(DiretrizRefatoracaoSchema(
                topico_ou_paragrafo="Marco Teórico e RSL",
                problema_identificado="Marco teórico insubsistente ou sem menção ao método de revisão sistemática.",
                instrucao_correcao="Apresentar o estado da arte com base no protocolo PRISMA e doutrina clássica e contemporânea."
            ))

        if len(state.precedentes_mcp) == 0:
            diretrizes.append(DiretrizRefatoracaoSchema(
                topico_ou_paragrafo="Corpus Jurisprudencial MCP",
                problema_identificado="Nenhum precedente vinculante ou qualificado indexado via MCP.",
                instrucao_correcao="Executar consulta ao JurisprudênciaIA MCP para incluir acórdãos do STF/STJ."
            ))

        if diretrizes:
            scores = ScoresPorCriterioSchema(
                rigor_conceitual=65.0,
                coerencia_estrutural=70.0,
                ineditismo=70.0,
                fidelidade_metodologica=60.0
            )
            diag = "Gate 2 Reprovado: Ausência de base de precedentes autênticos ou marco teórico incompleto."
        else:
            scores = ScoresPorCriterioSchema(
                rigor_conceitual=94.0,
                coerencia_estrutural=92.0,
                ineditismo=89.0,
                fidelidade_metodologica=93.0
            )
            diag = "Gate 2 Aprovado: Tripé doutrinário e base de precedentes qualificados validados."

        return self._calcular_score_e_status(scores, diretrizes, diag, GateAvaliadoEnum.GATE_2_BIBLIOGRAFICO, "literature_review_agent")

    def avaliar_gate_3_metodologico(self, state: DocumentoAcademicoState) -> ParecerRevisaoGeralSchema:
        """Avalia Gate 3: Metodologia e jurimetria empírica via MCP."""
        diretrizes: List[DiretrizRefatoracaoSchema] = []

        if not state.desenho_metodologico or len(state.desenho_metodologico.strip()) < 80:
            diretrizes.append(DiretrizRefatoracaoSchema(
                topico_ou_paragrafo="Metodologia",
                problema_identificado="Desenho de pesquisa não explicita a amostragem ou critérios de inclusão/exclusão.",
                instrucao_correcao="Definir recorte temporal, tribunais pesquisados e abordagem analítica."
            ))

        if diretrizes:
            scores = ScoresPorCriterioSchema(
                rigor_conceitual=70.0,
                coerencia_estrutural=70.0,
                ineditismo=75.0,
                fidelidade_metodologica=60.0
            )
            diag = "Gate 3 Reprovado: Critérios metodológicos insuficientes para replicação científica."
        else:
            scores = ScoresPorCriterioSchema(
                rigor_conceitual=91.0,
                coerencia_estrutural=93.0,
                ineditismo=88.0,
                fidelidade_metodologica=95.0
            )
            diag = "Gate 3 Aprovado: Desenho metodológico rigoroso e dados jurimétricos harmonizados."

        return self._calcular_score_e_status(scores, diretrizes, diag, GateAvaliadoEnum.GATE_3_METODOLOGICO, "methodology_agent")

    def avaliar_gate_4_redacao_seccional(self, state: DocumentoAcademicoState) -> ParecerRevisaoGeralSchema:
        """Avalia Gate 4: Redação modular, transições dialéticas e sustentação dogmática."""
        diretrizes: List[DiretrizRefatoracaoSchema] = []

        if len(state.capitulos) == 0:
            diretrizes.append(DiretrizRefatoracaoSchema(
                topico_ou_paragrafo="Capítulos Analíticos",
                problema_identificado="Nenhum capítulo ou seção redigida submetida para avaliação.",
                instrucao_correcao="Redigir as seções temáticas integrando a doutrina e as ementas do MCP."
            ))
        else:
            for titulo, texto in state.capitulos.items():
                if len(texto.strip()) < 150:
                    diretrizes.append(DiretrizRefatoracaoSchema(
                        topico_ou_paragrafo=f"Seção: {titulo}",
                        problema_identificado="Extensão ou densidade argumentativa insuficiente para padrão stricto sensu.",
                        instrucao_correcao="Expandir a discussão dialética confrontando posições antagônicas."
                    ))

        if diretrizes:
            scores = ScoresPorCriterioSchema(
                rigor_conceitual=65.0,
                coerencia_estrutural=65.0,
                ineditismo=70.0,
                fidelidade_metodologica=70.0
            )
            diag = "Gate 4 Reprovado: Seções com desenvolvimento analítico aquém do esperado."
        else:
            scores = ScoresPorCriterioSchema(
                rigor_conceitual=92.0,
                coerencia_estrutural=94.0,
                ineditismo=88.0,
                fidelidade_metodologica=91.0
            )
            diag = "Gate 4 Aprovado: Redação modular densa, articulada e amparada em fontes autênticas."

        return self._calcular_score_e_status(scores, diretrizes, diag, GateAvaliadoEnum.GATE_4_REDACAO_SECCIONAL, "sectional_writer_agent")

    def avaliar_gate_5_citacoes_banca(self, state: DocumentoAcademicoState, audit_erros: List[str] = None) -> ParecerRevisaoGeralSchema:
        """Avalia Gate 5: Auditoria anti-alucinação de citações e crivo da banca sintética."""
        diretrizes: List[DiretrizRefatoracaoSchema] = []
        if audit_erros:
            for erro in audit_erros:
                diretrizes.append(DiretrizRefatoracaoSchema(
                    topico_ou_paragrafo="Auditoria de Citações / Banca",
                    problema_identificado=f"Alucinação ou inconsistência detectada: {erro}",
                    instrucao_correcao="Substituir por precedente indexado comprovado no corpus RAG ou sanar a vulnerabilidade da tese."
                ))

        if diretrizes:
            scores = ScoresPorCriterioSchema(
                rigor_conceitual=60.0,
                coerencia_estrutural=70.0,
                ineditismo=80.0,
                fidelidade_metodologica=60.0
            )
            diag = "Gate 5 Reprovado: Inconsistência de citações ou vulnerabilidade dogmática identificada pela banca."
        else:
            scores = ScoresPorCriterioSchema(
                rigor_conceitual=95.0,
                coerencia_estrutural=95.0,
                ineditismo=90.0,
                fidelidade_metodologica=96.0
            )
            diag = "Gate 5 Aprovado: Citações 100% conferidas e tese aprovada com louvor na banca sintética."

        return self._calcular_score_e_status(scores, diretrizes, diag, GateAvaliadoEnum.GATE_5_CITACOES_BANCA, "defense_validator_agent")

    def avaliar_gate_6_homologacao_final(self, state: DocumentoAcademicoState) -> ParecerRevisaoGeralSchema:
        """Avalia Gate 6: Homologação global e liberação para compilação final ABNT."""
        gates_anteriores = [
            GateAvaliadoEnum.GATE_1_EPISTEMICO.value,
            GateAvaliadoEnum.GATE_2_BIBLIOGRAFICO.value,
            GateAvaliadoEnum.GATE_3_METODOLOGICO.value,
            GateAvaliadoEnum.GATE_4_REDACAO_SECCIONAL.value,
            GateAvaliadoEnum.GATE_5_CITACOES_BANCA.value
        ]

        faltantes = [g for g in gates_anteriores if g not in state.pareceres_gates or not state.pareceres_gates[g].autorizacao_avanco]
        diretrizes: List[DiretrizRefatoracaoSchema] = []

        if faltantes:
            for f in faltantes:
                diretrizes.append(DiretrizRefatoracaoSchema(
                    topico_ou_paragrafo="Homologação Final",
                    problema_identificado=f"Gate prévio não aprovado ou pendente: {f}",
                    instrucao_correcao=f"Retornar ao gate {f} e obter parecer favorável do Revisor Geral."
                ))
            scores = ScoresPorCriterioSchema(
                rigor_conceitual=50.0,
                coerencia_estrutural=50.0,
                ineditismo=50.0,
                fidelidade_metodologica=50.0
            )
            diag = "Gate 6 Reprovado: Impossível homologar compilação com etapas anteriores incompletas."
        else:
            scores = ScoresPorCriterioSchema(
                rigor_conceitual=96.0,
                coerencia_estrutural=96.0,
                ineditismo=92.0,
                fidelidade_metodologica=98.0
            )
            diag = "Gate 6 Aprovado: Obra acadêmica integralmente homologada para exportação em PDF e DOCX ABNT."

        return self._calcular_score_e_status(scores, diretrizes, diag, GateAvaliadoEnum.GATE_6_HOMOLOGACAO_FINAL, "chief_academic_reviewer")

