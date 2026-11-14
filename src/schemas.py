from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, field_validator

class GateAvaliadoEnum(str, Enum):
    GATE_1_EPISTEMICO = "GATE_1_EPISTEMICO"
    GATE_2_BIBLIOGRAFICO = "GATE_2_BIBLIOGRAFICO"
    GATE_3_METODOLOGICO = "GATE_3_METODOLOGICO"
    GATE_4_REDACAO_SECCIONAL = "GATE_4_REDACAO_SECCIONAL"
    GATE_5_CITACOES_BANCA = "GATE_5_CITACOES_BANCA"
    GATE_6_HOMOLOGACAO_FINAL = "GATE_6_HOMOLOGACAO_FINAL"

class StatusDecisaoEnum(str, Enum):
    APROVADO = "APROVADO"
    APROVADO_COM_RESSALVAS_MENORES = "APROVADO_COM_RESSALVAS_MENORES"
    REJEITADO_EXIGE_REFATORACAO = "REJEITADO_EXIGE_REFATORACAO"
    BLOQUEIO_HUMAN_IN_THE_LOOP = "BLOQUEIO_HUMAN_IN_THE_LOOP"

class PrecedenteJudicialSchema(BaseModel):
    tribunal: str = Field(..., description="Tribunal de origem (ex: STF, STJ, TJSP)")
    processo: str = Field(..., description="Classe e número processual (ex: REsp 1.845.234/SP)")
    relator: str = Field(..., description="Nome do Ministro ou Desembargador Relator")
    data_julgamento: str = Field(..., description="Data do julgamento (AAAA-MM-DD)")
    ementa: str = Field(..., description="Texto oficial da ementa do julgado")
    trecho_fundamentacao: Optional[str] = Field(None, description="Trecho literal de fundamentação do voto")
    link_oficial: Optional[str] = Field(None, description="URL pública oficial do acórdão")

class JurisprudenciaMcpPayloadSchema(BaseModel):
    tool_executada: str = Field(..., description="Nome da ferramenta MCP executada")
    parametros_consulta: Dict[str, Any] = Field(default_factory=dict, description="Parâmetros enviados à tool")
    tese_principal: str = Field(..., description="Síntese dogmática ou tese vinculante fixada")
    precedentes: List[PrecedenteJudicialSchema] = Field(default_factory=list, description="Lista de precedentes autênticos")
    pontos_cautela_distincoes: str = Field("", description="Pontos de cautela, divergências ou distinguishing")

class ScoresPorCriterioSchema(BaseModel):
    rigor_conceitual: float = Field(..., ge=0, le=100)
    coerencia_estrutural: float = Field(..., ge=0, le=100)
    ineditismo: float = Field(..., ge=0, le=100)
    fidelidade_metodologica: float = Field(..., ge=0, le=100)

class DiretrizRefatoracaoSchema(BaseModel):
    topico_ou_paragrafo: str = Field(..., description="Localização do problema no texto ou planejamento")
    problema_identificado: str = Field(..., description="Diagnóstico da falha técnica ou metodológica")
    instrucao_correcao: str = Field(..., description="Orientações detalhadas para correção pelo agente")

class ParecerRevisaoGeralSchema(BaseModel):
    gate_avaliado: GateAvaliadoEnum
    agente_submetido: str
    status_decisao: StatusDecisaoEnum
    score_global: float = Field(..., ge=0, le=100)
    scores_por_criterio: ScoresPorCriterioSchema
    diagnostico_critico: str
    diretrizes_refatoracao: List[DiretrizRefatoracaoSchema] = Field(default_factory=list)
    autorizacao_avanco: bool

    @field_validator("autorizacao_avanco")
    @classmethod
    def validar_autorizacao(cls, v: bool, info) -> bool:
        status = info.data.get("status_decisao")
        score = info.data.get("score_global")
        if status == StatusDecisaoEnum.REJEITADO_EXIGE_REFATORACAO and v:
            raise ValueError("Não é permitido autorizar avanço quando status é REJEITADO_EXIGE_REFATORACAO")
        if score is not None and score < 85.0 and v and status not in (StatusDecisaoEnum.APROVADO_COM_RESSALVAS_MENORES, StatusDecisaoEnum.APROVADO):
            raise ValueError(f"Score {score} inferior a 85 não pode autorizar avanço sem aprovação formal")
        return v

class TipoDocumentoEnum(str, Enum):
    ARTIGO_CIENTIFICO = "ARTIGO_CIENTIFICO"
    PROJETO_TESE = "PROJETO_TESE"

class DocumentoAcademicoState(BaseModel):
    """Estado global compartilhado entre os nós de agentes do pipeline."""
    titulo: str = ""
    tema: str = ""
    tipo_documento: TipoDocumentoEnum = TipoDocumentoEnum.ARTIGO_CIENTIFICO
    problema_pesquisa: str = ""
    hipotese: str = ""
    marco_teorico: str = ""
    desenho_metodologico: str = ""
    dados_jurimetria: Dict[str, Any] = Field(default_factory=dict)
    precedentes_mcp: List[PrecedenteJudicialSchema] = Field(default_factory=list)
    capitulos: Dict[str, str] = Field(default_factory=dict) # chave: titulo do capitulo/secao, valor: texto markdown
    pareceres_gates: Dict[str, ParecerRevisaoGeralSchema] = Field(default_factory=dict)
    gate_atual: GateAvaliadoEnum = GateAvaliadoEnum.GATE_1_EPISTEMICO
    status_geral: str = "EM_ANDAMENTO"
    refatoracao_pendente: bool = False

