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
**Descrição:** Como pesquisador, quero exportar o projeto ou artigo completo em formato PDF tipográfico (via Pandoc + LuaLaTeX) e DOCX estritamente formatados nas normas ABNT.
- **Por que esta prioridade:** Entrega final pronta para protocolo acadêmico ou submissão a periódicos.
- **Teste Independente:** Geração de arquivos `.pdf` e `.docx` a partir dos rascunhos consolidados aprovados no Gate 6.
- **Cenários de Aceite:**
  1. **Given** o parecer final aprovado pelo Revisor Geral, **When** o compilador for invocado, **Then** os documentos finais devem ser gerados no diretório `output/` com sumário, referências e citações conformes à ABNT.

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

3. **`DocumentoAcademicoState` (LangGraph State):**
   - Estado compartilhado contendo: tema, problema, hipótese, corpus RAG de precedentes e doutrinas, capítulos redigidos, histórico de pareceres dos gates, notas e status de avanço.

---

## 4. Requisitos Não Funcionais e Restrições Técnicas

- **Execução Local:** O código opera integralmente no ambiente local (`c:\App_Artigos_Cientificos`), conectando-se a endpoints MCP via HTTP/HTTPS JSON-RPC 2.0.
- **Resiliência a Falhas de Conexão:** Timeout configurável, tratamento de retries e fallbacks de tools de busca.
- **Armazenamento Transparente:** Textos e referências gravados em Markdown legível e auditável pelo usuário.
