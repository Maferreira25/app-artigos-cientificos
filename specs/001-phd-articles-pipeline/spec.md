# Feature Specification: Pipeline Autônomo Local de Pesquisa, Redação Acadêmica e Projetos de Doutorado com Integração MCP

**Feature Branch**: `001-phd-articles-pipeline`  
**Created**: 2026-11-11  
**Status**: Approved for Implementation  
**Input Reference**: `C:\Users\miche\Downloads\Temporários\especificacoes_tecnicas_pipeline_artigos_doutorado (1).md`  
**Target Domain**: Legal Tech / Inteligência Artificial Aplicada à Pesquisa Acadêmica (*Stricto Sensu*)

---

## 1. Visão Geral e Problema de Engenharia

A produção de projetos de tese de doutorado e artigos acadêmicos de alto impacto (Qualis A / Scopus) requer rigor epistemológico, exaustividade bibliográfica, coerência metodológica e precisão absoluta em citações jurisprudenciais e doutrinárias.

Este pipeline resolve as três principais falhas de LLMs genéricos no meio acadêmico:
1. **Alucinação Jurisprudencial e Normativa:** Eliminada através da integração nativa com o **Servidor MCP de Jurisprudência Brasileira (`JurisprudênciaIA MCP`)** e persistência em Markdown com YAML Frontmatter.
2. **Superficialidade Argumentativa:** Eliminada através da orquestração modular com agentes especializados em epistemologia, RSL (PRISMA), jurimetria e confronto dialético.
3. **Desarticulação Estrutural e Falta de Governança:** Eliminada através do **Agente Revisor Geral (Supervisor / Chief Academic Auditor)** governando o avanço através de 6 Quality Gates eliminatórios.

---

## 2. Histórias de Usuário e Cenários de Teste (Priorizados)

### User Story 1 - Conexão Resiliente ao Servidor MCP de Jurisprudência (Priority: P1)
**Descrição:** Como pesquisador acadêmico, quero que o pipeline consulte precedentes vinculantes (STF/STJ), linhas do tempo de jurisprudência e jurimetria real diretamente do servidor MCP, com fallback automático em caso de indisponibilidade de ferramentas secundárias.
- **Por que esta prioridade:** Base de dados indispensável para garantir "Zero Alucinação".
- **Teste Independente:** O cliente assíncrono `JurisprudenciaMcpClient` executa chamadas JSON-RPC 2.0 para `buscar_precedentes_qualificados` e `pesquisar_jurisprudencia`, validando a saída em Markdown com metadados estruturados.
- **Cenários de Aceite:**
  1. **Given** o servidor MCP ativo em `http://localhost:8787/mcp` ou bridge HTTPS, **When** o cliente invocar `buscar_teses_vinculantes("prescrição intercorrente")`, **Then** o retorno deve conter precedentes qualificados reais com tribunal, processo, relator e ementa.
  2. **Given** uma requisição a uma tool inexistente ou com erro `-32602`, **When** o fallback for acionado, **Then** a requisição deve ser redirecionada com sucesso para `pesquisar_jurisprudencia` usando o argumento textual.

### User Story 2 - Agente Revisor Geral e Governança de Quality Gates 1 a 6 (Priority: P1)
**Descrição:** Como pesquisador e orientador acadêmico, quero que um Agente Revisor Geral audite rigorosamente cada fase da tese com uma matriz multidimensional (0 a 100, limiar 85), impedindo o avanço de textos superficiais ou metodologicamente incoerentes.
- **Por que esta prioridade:** Garante a governança global e impede que problemas na introdução se propaguem até a conclusão.
- **Teste Independente:** Submeter artefatos parciais ao `chief_academic_reviewer_agent` e verificar a geração válida do `ParecerRevisaoGeralSchema` com scores por critério e diretrizes de refatoração quando score < 85.
- **Cenários de Aceite:**
  1. **Given** uma formulação de problema rasa ou sem ineditismo submetida ao Gate 1, **When** o Revisor Geral avaliar o artefato, **Then** o status deve ser `REJEITADO_EXIGE_REFATORACAO`, com `autorizacao_avanco = False` e lista de diretrizes corretivas.
  2. **Given** um capítulo analítico rigoroso com confrontação dialética e fontes MCP validadas, **When** avaliado no Gate 4, **Then** o status deve ser `APROVADO` (score >= 85) e `autorizacao_avanco = True`.

### User Story 3 - Ciclo de Pesquisa Epistemológica, RSL e Metodologia (Priority: P2)
**Descrição:** Como doutorando, quero gerar a formulação do problema, hipótese, marco teórico, revisão sistemática (RSL/PRISMA) e metodologia empírica com jurimetria descritiva via MCP.
- **Por que esta prioridade:** Fornece o alicerce científico e a sustentação do projeto antes da redação dos capítulos.
- **Teste Independente:** Execução sequencial de `epistemic_agent`, `literature_review_agent` e `methodology_agent` gerando artefatos Markdown estruturados em `corpus/` e `drafts/`.
- **Cenários de Aceite:**
  1. **Given** o tema da pesquisa, **When** o `epistemic_agent` consultar `listar_overruling_tema`, **Then** deve mapear a viragem jurisprudencial que justifica a novidade da tese.
  2. **Given** o corpus doutrinário e jurisprudencial, **When** o `literature_review_agent` estruturar os dados, **Then** deve gerar arquivos Markdown locais enriquecidos com YAML Frontmatter.

### User Story 4 - Redação Seccional Modular e Banca Examinadora Sintética (Priority: P2)
**Descrição:** Como autor, quero que cada subcapítulo seja redigido com citações literais autênticas, e que uma banca sintética submeta a tese a fogo cruzado identificando vulnerabilidades antes da homologação.
- **Por que esta prioridade:** Transforma a pesquisa em texto dissertativo denso com validação antecipada contra contra-argumentos da jurisprudência dominante.
- **Teste Independente:** O `defense_validator_agent` executa `analisar_tese_juridica` no MCP e gera o relatório da banca sintética.
- **Cenários de Aceite:**
  1. **Given** uma seção com citação doutrinária ou de acórdão, **When** o auditor de citações inspecionar o texto, **Then** deve confrontar a citação contra o corpus RAG indexado, bloqueando menções a julgados inexistentes.
  2. **Given** a tese proposta, **When** submetida à banca sintética no Gate 5, **Then** os pontos de cautela e distinções devem ser emitidos e sanados.

### User Story 5 - Homologação e Compilação Final ABNT (Priority: P3)
**Descrição:** Como pesquisador, quero exportar o projeto ou artigo completo em formato PDF tipográfico (via Pandoc + LuaLaTeX ou motor nativo Python) e DOCX estritamente formatados nas normas ABNT.
- **Por que esta prioridade:** Entrega final pronta para protocolo acadêmico ou submissão a periódicos.
- **Teste Independente:** Geração de arquivos `.pdf` e `.docx` a partir dos rascunhos consolidados aprovados no Gate 6.
- **Cenários de Aceite:**
  1. **Given** o parecer final aprovado pelo Revisor Geral, **When** o compilador for invocado, **Then** os documentos finais devem ser gerados no diretório `output/` com sumário, referências e citações conformes à ABNT.

### User Story 6 - Higiene Acadêmica, Ordem Canônica ABNT NBR 6022 e Zero Vazamento RAG (Priority: P1)
**Descrição:** Como editor-chefe de periódico acadêmico Qualis A, exijo que o artigo científico respeite a ordem estrutural canônica (Introdução precedendo obrigatoriamente o desenvolvimento), apresente elementos pré-textuais normatizados (autoria qualificada, resumo vernáculo NBR 6028, abstract e keywords) e esteja 100% livre de comandos de depuração, metadados de API ou transcrições mecânicas de ementas.
- **Por que esta prioridade:** O vazamento de logs de ferramentas ou a desordem estrutural quebra o decoro acadêmico e inviabiliza a submissão para periódicos de estrato superior.
- **Teste Independente:** Execução de `sanitizar_texto_academico`, `verificar_vazamentos` e `calcular_proporcao_bullets` sobre o texto final gerado, avaliando reprovação imediata nos Gates 4 e 6 perante qualquer anomalia detectada.
- **Cenários de Aceite:**
  1. **Given** um texto gerado com comandos residuais como `# Resultado JurisprudenciaIA` ou `[J1 - STF]`, **When** submetido à auditoria do Revisor Geral, **Then** o Gate 4 ou Gate 6 deve reprovar a etapa com diretriz expressa de sanitização.
  2. **Given** um documento em que a Seção 2 anteceda a Seção 1, **When** processado pelo `AcademicExporter`, **Then** o algoritmo de ordenação canônica deve corrigir a sequência garantindo a Seção 1 (Introdução) como primeiro capítulo.
  3. **Given** capítulos com proporção de bullets superior a 15%, **When** avaliados no Gate 4, **Then** o sistema deve rejeitar o texto por estilo esquemático incompatível com o padrão *stricto sensu*.

---

## 3. Entidades e Modelos de Dados Chave

1. **`JurisprudenciaMcpPayloadSchema`:**
   - `tool_executada` (str)
   - `parametros_consulta` (dict)
   - `tese_principal` (str)
   - `precedentes` (list de objetos com tribunal, processo, relator, data_julgamento, ementa, trecho_fundamentacao, link_oficial)
   - `pontos_cautela_distincoes` (str)

2. **`ParecerRevisaoGeralSchema`:**
   - `gate_avaliado` (enum: `GATE_1_EPISTEMICO` .. `GATE_6_HOMOLOGACAO_FINAL`)
   - `agente_submetido` (str)
   - `status_decisao` (enum: `APROVADO`, `APROVADO_COM_RESSALVAS_MENORES`, `REJEITADO_EXIGE_REFATORACAO`, `BLOQUEIO_HUMAN_IN_THE_LOOP`)
   - `score_global` (float 0 a 100)
   - `scores_por_criterio` (`rigor_conceitual`, `coerencia_estrutural`, `ineditismo`, `fidelidade_metodologica`)
   - `diagnostico_critico` (str)
   - `diretrizes_refatoracao` (list de objetos com topico_ou_paragrafo, problema_identificado, instrucao_correcao)
   - `autorizacao_avanco` (bool)

3. **`DocumentoAcademicoState` (LangGraph / State Central):**
   - `tema` (str), `titulo` (str), `tipo_documento` (TipoDocumentoEnum)
   - `autores` (List[str]), `filiacoes` (List[str])
   - `resumo` (str - NBR 6028), `palavras_chave` (List[str])
   - `titulo_en` (str), `abstract` (str), `keywords` (List[str])
   - `problema_pesquisa` (str), `hipotese` (str), `marco_teorico` (str)
   - `desenho_metodologico` (str), `capitulos` (Dict[str, str]), `conclusao` (str)
   - `precedentes_mcp` (List[PrecedenteJudicialSchema]), `teses_concorrentes` (List[str])
   - `pareceres_gates` (Dict[str, ParecerRevisaoGeralSchema]), `scores_acumulados` (Dict[str, float])
   - `status_geral` (str)

---

## 4. Requisitos Não Funcionais e Restrições Técnicas

- **Execução Local:** O código opera integralmente no ambiente local (`c:\App_Artigos_Cientificos`), conectando-se a endpoints MCP via HTTP/HTTPS JSON-RPC 2.0.
- **Resiliência a Falhas de Conexão:** Timeout configurável, tratamento de retries e fallbacks de tools de busca.
- **Armazenamento Transparente:** Textos e referências gravados em Markdown legível e auditável pelo usuário.
- **Zero Tool Leakage:** Nenhuma cadeia de depuração, parâmetro de busca bruto ou log de chamada de API pode estar presente nos arquivos finais (.md, .pdf, .docx).
- **Prosa Dissertativa Contínua:** Decoro acadêmico de nível *stricto sensu*, limitando estruturas de tópicos/bullets a no máximo 15% das linhas do texto analítico.
