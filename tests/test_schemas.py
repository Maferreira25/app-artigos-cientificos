import pytest
from pydantic import ValidationError
from src.schemas import (
    GateAvaliadoEnum,
    StatusDecisaoEnum,
    PrecedenteJudicialSchema,
    JurisprudenciaMcpPayloadSchema,
    ScoresPorCriterioSchema,
    DiretrizRefatoracaoSchema,
    ParecerRevisaoGeralSchema,
    DocumentoAcademicoState
)

def test_precedente_schema_valido():
    prec = PrecedenteJudicialSchema(
        tribunal="STJ",
        processo="REsp 1.845.234/SP",
        relator="Min. Paulo de Tarso Sanseverino",
        data_julgamento="2023-03-15",
        ementa="RECURSO ESPECIAL REPETITIVO. TEMA 1015...",
        trecho_fundamentacao="A tese firmada estabelece a imprescritibilidade...",
        link_oficial="https://scon.stj.jus.br"
    )
    assert prec.tribunal == "STJ"
    assert prec.processo == "REsp 1.845.234/SP"

def test_jurisprudencia_payload_schema():
    payload = JurisprudenciaMcpPayloadSchema(
        tool_executada="buscar_precedentes_qualificados",
        parametros_consulta={"tema": "prescrição intercorrente"},
        tese_principal="Incide a prescrição intercorrente no processo de execução...",
        precedentes=[
            PrecedenteJudicialSchema(
                tribunal="STJ",
                processo="REsp 1.604.412/SC",
                relator="Min. Marco Aurélio Bellizze",
                data_julgamento="2018-06-27",
                ementa="INCIDENTE DE ASSUNÇÃO DE COMPETÊNCIA..."
            )
        ],
        pontos_cautela_distincoes="Exige intimação prévia do credor antes da extinção"
    )
    assert len(payload.precedentes) == 1
    assert payload.tool_executada == "buscar_precedentes_qualificados"

def test_parecer_revisao_geral_aprovado():
    parecer = ParecerRevisaoGeralSchema(
        gate_avaliado=GateAvaliadoEnum.GATE_1_EPISTEMICO,
        agente_submetido="epistemic_agent",
        status_decisao=StatusDecisaoEnum.APROVADO,
        score_global=92.5,
        scores_por_criterio=ScoresPorCriterioSchema(
            rigor_conceitual=95.0,
            coerencia_estrutural=90.0,
            ineditismo=90.0,
            fidelidade_metodologica=95.0
        ),
        diagnostico_critico="Problema formulado com precisão e contemporaneidade inconteste.",
        diretrizes_refatoracao=[],
        autorizacao_avanco=True
    )
    assert parecer.autorizacao_avanco is True
    assert parecer.score_global == 92.5

def test_parecer_rejeitado_nao_pode_avancar():
    with pytest.raises(ValidationError):
        ParecerRevisaoGeralSchema(
            gate_avaliado=GateAvaliadoEnum.GATE_1_EPISTEMICO,
            agente_submetido="epistemic_agent",
            status_decisao=StatusDecisaoEnum.REJEITADO_EXIGE_REFATORACAO,
            score_global=65.0,
            scores_por_criterio=ScoresPorCriterioSchema(
                rigor_conceitual=60.0,
                coerencia_estrutural=70.0,
                ineditismo=60.0,
                fidelidade_metodologica=70.0
            ),
            diagnostico_critico="Problema vago e sem hipótese refutável.",
            diretrizes_refatoracao=[
                DiretrizRefatoracaoSchema(
                    topico_ou_paragrafo="Seção 1.2",
                    problema_identificado="Falta de problema empírico delimitado",
                    instrucao_correcao="Formular questão de pesquisa centrada no dissídio do STJ"
                )
            ],
            autorizacao_avanco=True  # Incompatível com REJEITADO_EXIGE_REFATORACAO
        )

def test_documento_academico_state_default():
    state = DocumentoAcademicoState(
        titulo="A Eficácia Vinculante dos Precedentes no Direito Brasileiro",
        tema="Precedentes Vinculantes e Segurança Jurídica"
    )
    assert state.gate_atual == GateAvaliadoEnum.GATE_1_EPISTEMICO
    assert state.status_geral == "EM_ANDAMENTO"
    assert len(state.capitulos) == 0

