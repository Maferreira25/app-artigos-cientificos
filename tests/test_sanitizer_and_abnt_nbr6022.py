import pytest
from pathlib import Path
from src.sanitizer import (
    sanitizar_texto_academico,
    verificar_vazamentos,
    calcular_proporcao_bullets,
    converter_dados_jurimetria_em_prosa
)
from src.schemas import (
    DocumentoAcademicoState,
    TipoDocumentoEnum,
    PrecedenteJudicialSchema,
    GateAvaliadoEnum
)
from src.agents.chief_academic_reviewer import ChiefAcademicReviewer
from src.agents.sectional_writer_agent import SectionalWriterAgent
from src.exporter import AcademicExporter


def test_sanitizador_expurga_logs_mcp_e_comandos_de_prompt():
    texto_poluido = (
        "quando a fonte nao disponibilizar inteiro teor, informe isso explicitamente. Executado em: 2026-11-14T23:36:10.209Z Fonte: https://www.jurisprudenciaia.com.br/\n"
        "# Resultado JurisprudenciaIA\n"
        "## Resposta do JurisprudenciaIA\n"
        "Consulta: Levante um panorama jurimetrico sobre: Lei Maria da Penha.\n"
        "[J1 - STF]\n"
        "• Tribunal: STF\n"
        "• Metadados ausentes: inteiro teor\n"
        "• Link: https://scon.stj.jus.br\n"
        "Confira o inteiro teor dos precedentes antes de usar em peca, parecer ou minuta.\n"
        "A proteção jurídica à integridade psicofísica da mulher configura mandamento constitucional indeclinável.\n"
        "O STJ assentou a autonomia das medidas protetivas de urgência no rito do Tema 1249."
    )

    limpo = sanitizar_texto_academico(texto_poluido)

    assert "quando a fonte nao disponibilizar" not in limpo
    assert "Resultado JurisprudenciaIA" not in limpo
    assert "Consulta: Levante um panorama" not in limpo
    assert "[J1 - STF]" not in limpo
    assert "Metadados ausentes" not in limpo
    assert "Confira o inteiro teor" not in limpo
    assert "A proteção jurídica à integridade psicofísica da mulher" in limpo
    assert "Tema 1249" in limpo


def test_verificador_vazamentos_detecta_anomalias():
    texto_com_vazamento = "Conforme informado em [J1 - STF], valide a fonte no JurisprudenciaIA antes de citar."
    erros = verificar_vazamentos(texto_com_vazamento)
    assert len(erros) >= 1
    assert any("valide a fonte no jurisprudenciaia" in e or "jurisprudenciaia" in e or "j1" in e for e in erros)


def test_gate_4_reprova_vazamento_de_depuracao():
    reviewer = ChiefAcademicReviewer(threshold=85.0)
    state = DocumentoAcademicoState(
        tema="Violência Doméstica",
        capitulos={
            "1. Introdução": "O presente artigo científico analisa as alterações na Lei Maria da Penha sob a ótica dos precedentes das cortes de cúpula e garantias fundamentais.",
            "2. Marco Teórico": "Resultado JurisprudenciaIA: [J1 - STF] Metadados ausentes. O julgado demonstra a cautela judicial.",
        }
    )

    parecer = reviewer.avaliar_gate_4_redacao_seccional(state)
    assert parecer.autorizacao_avanco is False
    assert any("Vazamento detectado" in d.problema_identificado for d in parecer.diretrizes_refatoracao)


def test_gate_4_reprova_excesso_de_bullets():
    reviewer = ChiefAcademicReviewer(threshold=85.0)
    texto_esquematico = "\n".join([
        "Introdução ao problema.",
        "• Ponto 1 de decisão",
        "• Ponto 2 de decisão",
        "• Ponto 3 de decisão",
        "• Ponto 4 de decisão",
        "• Ponto 5 de decisão",
    ])
    state = DocumentoAcademicoState(
        capitulos={
            "1. Introdução": texto_esquematico * 5,
        }
    )

    parecer = reviewer.avaliar_gate_4_redacao_seccional(state)
    assert parecer.autorizacao_avanco is False
    assert any("Excesso de marcadores de lista" in d.problema_identificado for d in parecer.diretrizes_refatoracao)


def test_gate_4_reprova_ordem_invertida_de_secoes():
    reviewer = ChiefAcademicReviewer(threshold=85.0)
    state = DocumentoAcademicoState(
        capitulos={
            "2. Marco Teórico": "Desenvolvimento do tema com fundamentação teórica extensa e análise dialética substancial sobre a eficácia das medidas protetivas no ordenamento jurídico pátrio.",
            "1. Introdução": "Introdução que acabou sendo alocada no final do documento erroneamente."
        }
    )

    parecer = reviewer.avaliar_gate_4_redacao_seccional(state)
    assert parecer.autorizacao_avanco is False
    assert any("ordem das seções subvertida" in d.problema_identificado for d in parecer.diretrizes_refatoracao)


def test_exporter_ordena_capitulos_e_inclui_elementos_abnt(tmp_path):
    exporter = AcademicExporter(output_dir=tmp_path)
    state = DocumentoAcademicoState(
        titulo="A Efetividade da Proteção à Mulher",
        tema="Lei Maria da Penha e Medidas Protetivas",
        tipo_documento=TipoDocumentoEnum.ARTIGO_CIENTIFICO,
        capitulos={
            "2. Marco Teórico e Confrontação Dialética": "Desenvolvimento do marco teórico em prosa contínua densa sobre a Lei 14.550/2023.",
            "1. Introdução e Problematização Epistemológica": "Introdução formal delimitando a problemática e a hipótese do estudo.",
            "4. Considerações Finais": "Síntese conclusiva reafirmando a confirmação da hipótese investigada.",
            "3. Análise Empírico-Jurisprudencial": "Análise dos repetitivos e do Tema 1249 do STJ."
        }
    )

    md_path = exporter.gerar_markdown_consolidado(state)
    conteudo = md_path.read_text(encoding="utf-8")

    # Verifica presença dos elementos pré-textuais da ABNT NBR 6022
    assert "# A Efetividade da Proteção à Mulher" in conteudo
    assert "Pesquisador Acadêmico (Doutorando em Direito)" in conteudo
    assert "## Resumo" in conteudo
    assert "Palavras-chave:" in conteudo
    assert "## Abstract:" in conteudo
    assert "Keywords:" in conteudo

    # Verifica ordenação estrita: Seção 1 deve aparecer ANTES de Seção 2
    idx_sec1 = conteudo.find("1. Introdução")
    idx_sec2 = conteudo.find("2. Marco Teórico")
    idx_sec3 = conteudo.find("3. Análise Empírico")
    idx_sec4 = conteudo.find("4. Considerações Finais")

    assert idx_sec1 != -1 and idx_sec2 != -1 and idx_sec3 != -1 and idx_sec4 != -1
    assert idx_sec1 < idx_sec2 < idx_sec3 < idx_sec4

    # Verifica referências contextuais da Lei Maria da Penha
    assert "Lei nº 11.340" in conteudo
    assert "Lei nº 14.550" in conteudo
    assert "Tema Repetitivo 1249" in conteudo

    # Verifica ausência de vazamentos
    assert "Resultado JurisprudenciaIA" not in conteudo
    assert "quando a fonte nao disponibilizar" not in conteudo


def test_calcular_proporcao_bullets_ignora_titulos_de_secoes():
    # Texto com títulos numerados de seção e parágrafos normais (sem bullets reais)
    texto = (
        "1. Introdução e Problematização Epistemológica\n"
        "O presente estudo investiga as nuances hermenêuticas do sistema protetivo pátrio.\n"
        "2. Marco Teórico e Hermenêutica Aplicada\n"
        "A base dogmática ampara-se nas garantias fundamentais da dignidade da pessoa humana.\n"
        "3. Análise Empírico-Jurisprudencial e Hermenêutica Decisória\n"
        "Os acórdãos paradigmáticos do STJ convergem para a consolidação de teses repetitivas.\n"
        "4. Considerações Finais e Perspectivas Epistemológicas\n"
        "Conclui-se pela imperatividade de estabilidade decisória e segurança jurídica."
    )
    # A proporção de bullets DEVE ser 0.0 (nenhum item é bullet)
    prop = calcular_proporcao_bullets(texto)
    assert prop == 0.0


def test_exporter_higieniza_pontuacao_de_palavras_chave(tmp_path):
    exporter = AcademicExporter(output_dir=tmp_path)
    state = DocumentoAcademicoState(
        titulo="Estudo Sobre Garantias Fundamentais",
        tema="Garantias Fundamentais",
        palavras_chave=["Precedentes Judiciais.", " Segurança Jurídica. ", "STJ."],
        keywords=["Judicial Precedents.", " Legal Certainty. ", "Superior Court."],
        capitulos={
            "1. Introdução": "Texto introdutório com fundamentação densa e acadêmica para validação de formato.",
        },
        conclusao="Síntese conclusiva alocada no campo conclusao do estado para validação de fallback."
    )

    md_path = exporter.gerar_markdown_consolidado(state)
    conteudo = md_path.read_text(encoding="utf-8")

    # Verifica que não há duplicação de pontos ".. "
    assert "Precedentes Judiciais. Segurança Jurídica. STJ." in conteudo
    assert ".." not in conteudo
    # Verifica que a conclusão explícita foi incluída mesmo sem estar previamente em capitulos
    assert "# 4. Considerações Finais" in conteudo
    assert "Síntese conclusiva alocada no campo conclusao" in conteudo


def test_converter_dados_jurimetria_em_prosa_com_dados_variados():
    # Caso 1: entrada vazia ou mínima
    resultado_fallback = converter_dados_jurimetria_em_prosa("", "Proteção à Mulher")
    assert "A análise empírico-jurimétrica sobre Proteção à Mulher" in resultado_fallback

    # Caso 2: entrada com dados numéricos e metadados
    dados_mcp = (
        "# Resultado JurisprudenciaIA\n"
        "• Tribunal: STJ\n"
        "• Total de Acórdãos Analisados: 120\n"
        "• Índice de Provimento: 78.5%\n"
        "A Terceira Seção uniformizou a jurisprudência por meio do Tema 1249.\n"
        "Fixou-se a autonomia das medidas protetivas de urgência."
    )
    prosa = converter_dados_jurimetria_em_prosa(dados_mcp, "Tema 1249")
    assert "Resultado JurisprudenciaIA" not in prosa
    assert "• Tribunal:" not in prosa
    assert "Tema 1249" in prosa
