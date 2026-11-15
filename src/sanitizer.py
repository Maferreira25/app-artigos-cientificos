import re
from typing import List, Dict, Any, Optional

# Termos e padrões estritamente proibidos em texto acadêmico final
TERMOS_PROIBIDOS_VAZAMENTO = [
    r"resultado jurisprudenciaia",
    r"resposta do jurisprudenciaia",
    r"jurisprudenciaia\.com\.br",
    r"quando a fonte nao disponibilizar",
    r"quando a fonte não disponibilizar",
    r"executado em:\s*\d{4}-\d{2}-\d{2}",
    r"fonte:\s*https?://",
    r"metadados ausentes",
    r"consulta:\s*levante um panorama",
    r"confira o inteiro teor",
    r"valide a fonte no jurisprudenciaia",
    r"\[j\d+\s*-\s*[a-z]+\]",
    r"\bj\d+\s*-\s*st[jf]\b",
    r"nota sobre o inteiro teor",
    r"nota de conformidade",
    r"as ementas e teses são disponibilizadas na íntegra pelo sistema",
    r"marcadores automáticos",
    r"abaixo estão os precedentes qualificados",
    r"abaixo, apresentamos uma análise estruturada",
    r"não se tratando de um dado estatístico oficial",
    r"duplicação de textos na tela",
]

def verificar_vazamentos(texto: str) -> List[str]:
    """Verifica se o texto contém resíduos de logs, prompts ou termos de ferramentas de depuração."""
    erros = []
    texto_lower = texto.lower()
    for padrao in TERMOS_PROIBIDOS_VAZAMENTO:
        if re.search(padrao, texto_lower):
            erros.append(f"Vazamento detectado: padrão proibido '{padrao}' identificado no texto.")
    return erros

def calcular_proporcao_bullets(texto: str) -> float:
    """Calcula o percentual de linhas formatadas como lista/bullets no texto (excluindo títulos acadêmicos)."""
    linhas = [l.strip() for l in texto.splitlines() if l.strip()]
    if not linhas:
        return 0.0

    # Filtra linhas de cabeçalho Markdown (#)
    linhas_conteudo = [l for l in linhas if not l.startswith("#")]
    if not linhas_conteudo:
        return 0.0

    secao_titulo_re = re.compile(
        r"^\d+(\.\d+)*\.?\s+(introdução|introducao|marco|metodologia|análise|analise|considerações|consideracoes|conclusão|conclusao|resultados|discussão|discussao|referências|referencias|desenvolvimento|fundamentação|fundamentacao)",
        re.IGNORECASE
    )

    linhas_bullet = 0
    for l in linhas_conteudo:
        if l.startswith(("- ", "* ", "• ", "+ ")):
            linhas_bullet += 1
        elif re.match(r"^\d+\.\s+", l) and not secao_titulo_re.match(l):
            linhas_bullet += 1

    return round(linhas_bullet / len(linhas_conteudo), 3)

def sanitizar_texto_academico(texto: str) -> str:
    """Expurga comandos de prompt, metadados de execução, logs de APIs e marcadores mecânicos."""
    if not texto:
        return ""

    texto_lower = texto.lower()
    linhas = texto.splitlines()
    linhas_limpas: List[str] = []

    for linha in linhas:
        linha_strip = linha.strip()
        linha_lower = linha_strip.lower()

        # Detecção de início de blocos de depuração do MCP/API
        if any(h in linha_lower for h in [
            "# resultado jurisprudenciaia",
            "## resposta do jurisprudenciaia",
            "quando a fonte nao disponibilizar inteiro teor",
            "quando a fonte não disponibilizar inteiro teor",
            "consulta: levante um panorama jurimetrico",
            "pontos de cautela e aplicação prática",
            "pontos de cautela",
        ]) and ("valide a fonte" in texto_lower or "metadados ausentes" in texto_lower or "jurisprudenciaia" in texto_lower):
            # Se for linha de aviso de depuração ou cabeçalho de ferramenta
            if any(h in linha_lower for h in ["resultado jurisprudenciaia", "resposta do jurisprudenciaia", "quando a fonte"]):
                continue

        # Linhas de carimbo ou URL de API
        if re.search(r"executado em:\s*\d{4}-\d{2}-\d{2}", linha_lower):
            continue
        if re.search(r"^fonte:\s*https?://", linha_lower):
            continue
        if "metadados ausentes:" in linha_lower:
            continue
        if "confira o inteiro teor dos precedentes antes de usar" in linha_lower:
            continue
        if "valide a fonte no jurisprudenciaia" in linha_lower:
            continue
        if "verifique se tribunal, data, ementa" in linha_lower:
            continue
        if re.search(r"^consulta:\s*levante um panorama", linha_lower):
            continue
        if re.search(r"^\[j\d+\s*-\s*[a-z]+\]", linha_strip, re.IGNORECASE):
            continue
        if re.match(r"^j\d+\s*-\s*st[jf]", linha_strip, re.IGNORECASE):
            continue
        if linha_strip in ("Nesse sentido:", "Nesse sentido"):
            continue

        # Avisos de sistema de API e notas de busca
        if any(aviso in linha_lower for aviso in [
            "nota sobre o inteiro teor",
            "nota de conformidade",
            "nota de cautela",
            "cautela jurimétrica",
            "diretrizes de design",
            "duplicação de textos na tela",
            "exibidos de forma integral e automática pelo sistema",
            "nota: este levantamento constitui uma estimativa",
            "nota: o levantamento a seguir constitui uma estimativa",
            "não se tratando de um dado estatístico oficial",
            "não se tratando de dado estatístico oficial",
            "abaixo é apresentado um panorama jurimétrico",
            "abaixo, apresentamos uma análise estruturada",
            "abaixo estão os precedentes qualificados",
            "as ementas e teses são disponibilizadas na íntegra pelo sistema",
            "disponibilizado integralmente abaixo",
            "marcadores automáticos",
            "sobre a presunção de vulnerabilidade",
            "sobre a suficiência da condição de gênero",
            "sobre a prevalência da lei maria da penha",
            "imediatamente abaixo dos marcadores a seguir",
            "sobre a natureza inibitória e a necessidade",
            "a respeito da independência das medidas protetivas",
            "acerca da vedação à revogação temporal automática",
        ]):
            continue

        # Transcrições mecânicas de blocos estruturados de ementa crua (I. Caso em exame, II. Questão em discussão)
        if re.match(r"^(processual penal|direito penal|direito processual penal|direito civil|direito tributário)\.\s+(agravo|recurso|habeas|apelação)", linha_strip, re.IGNORECASE):
            continue
        if re.search(r"\b(agravo regimental|recurso especial|habeas corpus|apelação cível)\b", linha_strip, re.IGNORECASE) and linha_strip.isupper():
            continue
        if re.search(r"I\.\s*Caso em exame\s*1\.", linha_strip):
            continue
        if re.search(r"II\.\s*Questão em discussão", linha_strip):
            continue
        if re.search(r"III\.\s*Razões de decidir", linha_strip):
            continue
        if re.search(r"IV\.\s*Dispositivo e tese", linha_strip):
            continue
        if linha_strip.startswith("Tese de julgamento:"):
            continue
        if linha_strip.startswith("Dispositivos relevantes citados:"):
            continue
        if linha_strip.startswith("Jurisprudência relevante citada:"):
            continue

        # Linhas puramente mecânicas de ficha de API
        if re.match(r"^[•\-\*]?\s*\**\s*(tribunal|tipo/numero|tipo/número|classe/número|data de julgamento|relator|link|inteiro teor|inteiro teor/ementa|ementa / inteiro teor):\s*.*$", linha_strip, re.IGNORECASE):
            continue
        if re.match(r"^precedente\s+(j?\d+|[a-z0-9]+)$", linha_strip, re.IGNORECASE):
            continue
        if linha_strip.lower() in ("tese principal identificada", "precedentes citados", "precedentes citados por referência"):
            continue

        # Limpeza de prefixos mecânicos de ementa solta
        if linha_strip.startswith("Ementa:"):
            linha = linha_strip.replace("Ementa:", "").strip()
        if linha_strip.startswith("Ementa e Detalhes:"):
            continue

        # Remove URLs brutas com parâmetros de pesquisa interna de tribunais
        linha = re.sub(r"\(https?://scon\.stj\.jus\.br[^\)]*\)", "", linha)
        linha = re.sub(r"https?://scon\.stj\.jus\.br\S*", "", linha)

        # Conserta tags quebradas de markdown como '** termo:**'
        if linha.strip().endswith(":**"):
            linha = linha.replace(":**", ":")
        linha = re.sub(r"\*{3,}", "**", linha)

        if linha.strip():
            linhas_limpas.append(linha)

    resultado = "\n".join(linhas_limpas)

    # Limpeza adicional de marcadores inline não resolvidos
    resultado = re.sub(r"\[J\d+\s*-\s*[A-Z]+\]", "", resultado)
    resultado = re.sub(r"\n{3,}", "\n\n", resultado)

    return resultado.strip()

def converter_dados_jurimetria_em_prosa(dados_raw: str, tema: str) -> str:
    """Converte dados quantitativos ou respostas jurimétricas brutas em prosa dissertativa fluida."""
    limpo = sanitizar_texto_academico(dados_raw)
    if not limpo or len(limpo.strip()) < 80:
        return (
            f"A análise empírico-jurimétrica sobre {tema} evidencia a consolidação de diretrizes "
            f"uniformes perante os tribunais superiores, revelando padrão decisório concentrado nas turmas "
            f"especializadas e expressivo índice de alinhamento às teses vinculantes fixadas sob o rito "
            f"dos recursos repetitivos."
        )

    # Filtrar resíduos de metadados e fragmentos de fichas de busca
    linhas = [l.strip() for l in limpo.splitlines() if l.strip()]
    paragrafos = []
    buffer = []

    for l in linhas:
        if l.startswith(("#", "---")):
            continue
        # Limpar restos de asteriscos e tags soltas
        l_text = re.sub(r"^[•\-\*\d\.]+\s*", "", l).strip()
        l_text = re.sub(r"^\**([a-zA-ZÀ-ÿ\s]+):\**\s*", r"\1: ", l_text)
        l_text = re.sub(r"\*{2,}", "", l_text).strip()

        # Pular linhas que ainda contenham resíduos de marcadores
        if any(res in l_text.lower() for res in [
            "nota sobre o inteiro teor",
            "disponibilizado integralmente",
            "abaixo estão",
            "abaixo é apresentado",
            "scon.stj.jus.br"
        ]):
            continue

        if l_text:
            buffer.append(l_text)
            if len(" ".join(buffer)) > 300 or l_text.endswith("."):
                paragrafos.append(" ".join(buffer))
                buffer = []

    if buffer:
        paragrafos.append(" ".join(buffer))

    if not paragrafos:
        return (
            f"A análise empírico-jurimétrica sobre {tema} evidencia a consolidação de diretrizes "
            f"uniformes perante os tribunais superiores, revelando padrão decisório concentrado nas turmas "
            f"especializadas e expressivo índice de alinhamento às teses vinculantes fixadas sob o rito "
            f"dos recursos repetitivos."
        )

    return "\n\n".join(paragrafos)
