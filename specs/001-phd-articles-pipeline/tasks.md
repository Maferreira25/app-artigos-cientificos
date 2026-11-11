# Tasks: Pipeline Autônomo Local de Pesquisa, Redação Acadêmica e Projetos de Doutorado com Integração MCP

**Input**: Design documents from `specs/001-phd-articles-pipeline/` (spec.md, plan.md)  
**Status**: Completed & Verified  

---

## Phase 1: Setup & Foundational Infrastructure

- [x] T001 Inicializar repositório Git e estrutura de diretórios do Spec Kit (`.specify/`, `specs/`).
- [x] T002 Criar `pyproject.toml` com dependências (`httpx`, `pydantic>=2.0`, `pyyaml`, `rich`, `typer`, `pytest`, `pytest-asyncio`).
- [x] T003 [P] Criar `src/config.py` com configurações de ambiente (endpoint MCP `http://localhost:8787`, tokens, diretórios de trabalho).
- [x] T004 Criar `src/schemas.py` com os schemas Pydantic: `JurisprudenciaMcpPayloadSchema`, `ParecerRevisaoGeralSchema`, `StatusDecisaoEnum`, `GateAvaliadoEnum`, `ScoresPorCriterioSchema` e `DocumentoAcademicoState`.
- [x] T005 [P] Criar suite de testes em `tests/test_schemas.py` para validar conformidade dos schemas Pydantic.

---

## Phase 2: User Story 1 - Conexão Resiliente ao Servidor MCP (Priority: P1)

- [x] T006 Implementar `src/mcp_client.py`: classe `JurisprudenciaMcpClient` com conexão JSON-RPC 2.0 assíncrona, autenticação Bearer opcional, timeout configurável e tratamento de erro com fallback automático para `pesquisar_jurisprudencia`.
- [x] T007 Adicionar métodos acadêmicos em `src/mcp_client.py`: `buscar_teses_vinculantes`, `obter_linha_do_tempo`, `mapear_overruling`, `extrair_jurimetria`, `pesquisar_ementas`, `buscar_citacoes_dispositivo`, `analisar_tese_juridica`, `comparar_teses`.
- [x] T008 Implementar `src/rag_store.py`: módulo gerenciador de Markdown local com suporte a extração e escrita de YAML Frontmatter para indexação de precedentes.
- [x] T009 Criar testes automatizados em `tests/test_mcp_client.py` simulando chamadas JSON-RPC 2.0 reais/mockadas e testando o fallback.

---

## Phase 3: User Story 2 - Agente Revisor Geral e Governança de Quality Gates 1 a 6 (Priority: P1)

- [x] T010 Implementar `src/agents/chief_academic_reviewer.py`: lógica do Revisor Geral / Auditor Chefe com matriz de avaliação multidimensional (0 a 100, limiar 85).
- [x] T011 Implementar avaliadores específicos para cada gate no Revisor Geral:
  - Gate 1: Problema, hipótese e contemporaneidade
  - Gate 2: RSL (PRISMA) e tripé doutrinário
  - Gate 3: Metodologia e amostra jurimétrica
  - Gate 4: Redação modular e densidade dialética
  - Gate 5: Citações anti-alucinação e banca sintética
  - Gate 6: Homologação final para compilação
- [x] T012 Criar testes em `tests/test_reviewer_gates.py` testando aprovações, ressalvas e rejeições com emissão de diretrizes de refatoração.

---

## Phase 4: User Story 3 - Ciclo de Pesquisa Epistemológica, RSL e Metodologia (Priority: P2)

- [x] T013 Implementar `src/agents/epistemic_agent.py`: geração de problema de pesquisa, hipóteses refutáveis, marco teórico e consulta a viragens jurisprudenciais (`listar_overruling_tema`).
- [x] T014 Implementar `src/agents/literature_review_agent.py`: revisão sistemática de literatura (RSL/PRISMA), tripé doutrinário e linha do tempo de precedentes via MCP (`linha_do_tempo_precedentes`).
- [x] T015 Implementar `src/agents/methodology_agent.py`: desenho de pesquisa (qualitativa/quantitativa) e integração com `analisar_jurimetria` do MCP.

---

## Phase 5: User Story 4 - Redação Seccional Modular e Banca Examinadora Sintética (Priority: P2)

- [x] T016 Implementar `src/agents/sectional_writer_agent.py`: redação modular de subcapítulos injetando acórdãos autênticos e citações doutrinárias do corpus.
- [x] T017 Implementar `src/agents/defense_validator_agent.py`: auditor anti-alucinação confrontando citações contra metadados YAML e simulando a banca examinadora com `analisar_tese_juridica`.

---

## Phase 6: User Story 5 - Orquestrador LangGraph, Compilação ABNT e CLI (Priority: P3)

- [x] T018 Implementar `src/orchestrator.py`: Grafo de estados com Supervisor Pattern ligando os 5 agentes especialistas ao `chief_academic_reviewer` com loops de refatoração.
- [x] T019 Implementar `src/exporter.py`: gerador de Markdown consolidado e exportador para Pandoc (PDF via LaTeX e DOCX formatado nas normas ABNT NBR 14724, 6023 e 10520).
- [x] T020 Implementar `src/cli.py`: interface de linha de comando com Rich para inicializar projetos de tese, executar gates interativamente ou em lote e visualizar relatórios do revisor.
- [x] T021 Criar teste end-to-end em `tests/test_orchestrator.py` validando o fluxo completo com simulação de tese piloto.
