import pytest
from src.schemas import (
    GateAvaliadoEnum,
    StatusDecisaoEnum,
    DocumentoAcademicoState,
    PrecedenteJudicialSchema,
    ParecerRevisaoGeralSchema,
    ScoresPorCriterioSchema
)
from src.agents.chief_academic_reviewer import ChiefAcademicReviewer

@pytest.fixture
def reviewer():
    return ChiefAcademicReviewer(threshold=85.0)

def test_gate_1_reprovado_por_problema_curto(reviewer):
    state = DocumentoAcademicoState(
        problema_pesquisa="Qual o problema?",  # Menos de 30 caracteres
        hipotese="A jurisprudência deve ser seguida."
    )
    parecer = reviewer.avaliar_gate_1_epistemico(state)
    assert parecer.status_decisao == StatusDecisaoEnum.REJEITADO_EXIGE_REFATORACAO
    assert parecer.autorizacao_avanco is False
    assert parecer.score_global < 85.0
    assert len(parecer.diretrizes_refatoracao) > 0

def test_gate_1_aprovado(reviewer):
    state = DocumentoAcademicoState(
        problema_pesquisa="Em que medida a modulação temporal de efeitos em overruling tributário pelo STF viola a legítima confiança e a segurança jurídica do contribuinte?",
        hipotese="A modulação prospectiva sem critérios objetivos de transição instaura insegurança sistêmica, exigindo um estatuto dogmático uniforme de proteção à confiança."
    )
    parecer = reviewer.avaliar_gate_1_epistemico(state)
    assert parecer.status_decisao == StatusDecisaoEnum.APROVADO
    assert parecer.autorizacao_avanco is True
    assert parecer.score_global >= 85.0

def test_gate_2_reprovado_sem_precedentes_mcp(reviewer):
    state = DocumentoAcademicoState(
        marco_teorico="A teoria dos precedentes de Michele Taruffo e Neil MacCormick sustenta que a coerência integrativa do ordenamento depende do respeito às razões de decidir consolidadas pelos tribunais de cúpula.",
        precedentes_mcp=[] # Vazio
    )
    parecer = reviewer.avaliar_gate_2_bibliografico(state)
    assert parecer.status_decisao == StatusDecisaoEnum.REJEITADO_EXIGE_REFATORACAO
    assert parecer.autorizacao_avanco is False

def test_gate_2_aprovado(reviewer):
    state = DocumentoAcademicoState(
        marco_teorico="A teoria dos precedentes de Michele Taruffo e Neil MacCormick sustenta que a coerência integrativa do ordenamento depende do respeito às razões de decidir consolidadas pelos tribunais de cúpula.",
        precedentes_mcp=[
            PrecedenteJudicialSchema(
                tribunal="STJ",
                processo="REsp 1.845.234/SP",
                relator="Min. Paulo Sanseverino",
                data_julgamento="2023-03-15",
                ementa="RECURSO ESPECIAL..."
            )
        ]
    )
    parecer = reviewer.avaliar_gate_2_bibliografico(state)
    assert parecer.status_decisao == StatusDecisaoEnum.APROVADO
    assert parecer.autorizacao_avanco is True

def test_gate_5_reprovado_por_citacao_alucinada(reviewer):
    state = DocumentoAcademicoState()
    erros = ["Acórdão STJ REsp 9.999.999/DF citado na página 12 não consta no corpus indexado nem na base oficial."]
    parecer = reviewer.avaliar_gate_5_citacoes_banca(state, audit_erros=erros)
    assert parecer.status_decisao == StatusDecisaoEnum.REJEITADO_EXIGE_REFATORACAO
    assert parecer.autorizacao_avanco is False
    assert "Alucinação" in parecer.diretrizes_refatoracao[0].problema_identificado

def test_gate_6_homologacao_com_etapas_anteriores_aprovadas(reviewer):
    state = DocumentoAcademicoState()
    # Mock dos 5 gates aprovados
    for g in [
        GateAvaliadoEnum.GATE_1_EPISTEMICO,
        GateAvaliadoEnum.GATE_2_BIBLIOGRAFICO,
        GateAvaliadoEnum.GATE_3_METODOLOGICO,
        GateAvaliadoEnum.GATE_4_REDACAO_SECCIONAL,
        GateAvaliadoEnum.GATE_5_CITACOES_BANCA
    ]:
        state.pareceres_gates[g.value] = ParecerRevisaoGeralSchema(
            gate_avaliado=g,
            agente_submetido="agent",
            status_decisao=StatusDecisaoEnum.APROVADO,
            score_global=92.0,
            scores_por_criterio=ScoresPorCriterioSchema(
                rigor_conceitual=92.0,
                coerencia_estrutural=92.0,
                ineditismo=92.0,
                fidelidade_metodologica=92.0
            ),
            diagnostico_critico="Aprovado",
            diretrizes_refatoracao=[],
            autorizacao_avanco=True
        )
    
    parecer = reviewer.avaliar_gate_6_homologacao_final(state)
    assert parecer.status_decisao == StatusDecisaoEnum.APROVADO
    assert parecer.autorizacao_avanco is True
    assert parecer.score_global >= 90.0

def test_gate_3_reprovado_por_metodologia_insuficiente(reviewer):
    state = DocumentoAcademicoState(
        desenho_metodologico="Pesquisa teórica simples."  # Menos de 80 caracteres
    )
    parecer = reviewer.avaliar_gate_3_metodologico(state)
    assert parecer.status_decisao == StatusDecisaoEnum.REJEITADO_EXIGE_REFATORACAO
    assert parecer.autorizacao_avanco is False
    assert len(parecer.diretrizes_refatoracao) > 0

def test_gate_4_reprovado_por_ausencia_de_capitulos(reviewer):
    state = DocumentoAcademicoState(
        capitulos={}  # Sem capítulos
    )
    parecer = reviewer.avaliar_gate_4_redacao_seccional(state)
    assert parecer.status_decisao == StatusDecisaoEnum.REJEITADO_EXIGE_REFATORACAO
    assert parecer.autorizacao_avanco is False

def test_gate_4_reprovado_por_capitulo_curto(reviewer):
    state = DocumentoAcademicoState(
        capitulos={"Capítulo 1": "Texto extremamente curto sem profundidade."}  # < 150 caracteres
    )
    parecer = reviewer.avaliar_gate_4_redacao_seccional(state)
    assert parecer.status_decisao == StatusDecisaoEnum.REJEITADO_EXIGE_REFATORACAO
    assert parecer.autorizacao_avanco is False

def test_gate_6_reprovado_com_gate_anterior_pendente(reviewer):
    state = DocumentoAcademicoState()
    # Apenas o Gate 1 configurado
    state.pareceres_gates[GateAvaliadoEnum.GATE_1_EPISTEMICO.value] = ParecerRevisaoGeralSchema(
        gate_avaliado=GateAvaliadoEnum.GATE_1_EPISTEMICO,
        agente_submetido="agent",
        status_decisao=StatusDecisaoEnum.APROVADO,
        score_global=90.0,
        scores_por_criterio=ScoresPorCriterioSchema(
            rigor_conceitual=90.0,
            coerencia_estrutural=90.0,
            ineditismo=90.0,
            fidelidade_metodologica=90.0
        ),
        diagnostico_critico="Aprovado",
        diretrizes_refatoracao=[],
        autorizacao_avanco=True
    )
    parecer = reviewer.avaliar_gate_6_homologacao_final(state)
    assert parecer.status_decisao == StatusDecisaoEnum.REJEITADO_EXIGE_REFATORACAO
    assert parecer.autorizacao_avanco is False
    assert len(parecer.diretrizes_refatoracao) == 4  # Gates 2, 3, 4 e 5 faltantes


