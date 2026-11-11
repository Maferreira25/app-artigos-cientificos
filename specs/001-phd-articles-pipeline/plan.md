# Implementation Plan: Pipeline Autônomo Local de Pesquisa, Redação Acadêmica e Projetos de Doutorado com Integração MCP

**Branch**: `001-phd-articles-pipeline` | **Date**: 2026-11-11 | **Spec**: [specs/001-phd-articles-pipeline/spec.md](spec.md)

---

## 1. Summary

Implementar a arquitetura completa do pipeline autônomo local de pesquisa e redação acadêmica (*stricto sensu*) e teses de doutorado, composto por:
1. **Cliente MCP Assíncrono (`src/mcp_client.py`):** Conexão JSON-RPC 2.0 com o servidor `JurisprudênciaIA MCP` (local ou bridge HTTPS) para acesso a 14 ferramentas de pesquisa jurídica com fallback e transformação para Markdown RAG com YAML frontmatter.
2. **Modelos e Schemas Pydantic (`src/schemas.py`):** Definição estrita de `JurisprudenciaMcpPayloadSchema`, `ParecerRevisaoGeralSchema`, `DocumentoAcademicoState` e os Enums de Gates e Decisões.
3. **Agente Revisor Geral (`src/agents/chief_academic_reviewer.py`):** Agente supervisor (LangGraph Supervisor) que opera a matriz de avaliação multidimensional (0 a 100, corte 85) e controla o trânsito pelos Quality Gates 1 a 6.
4. **Agentes Especialistas Acadêmicos (`src/agents/`):**
   - `epistemic_agent.py`: Formulação de problema, hipótese, delimitação e consulta a overruling.
   - `literature_review_agent.py`: RSL (PRISMA), tripé doutrinário e linha do tempo de precedentes.
   - `methodology_agent.py`: Desenho metodológico e jurimetria empírica via MCP.
   - `sectional_writer_agent.py`: Redação modular seccional com citações literais e trechos de ementas.
   - `defense_validator_agent.py`: Auditor anti-alucinação e banca examinadora sintética.
5. **Orquestrador de Grafo de Estados (`src/orchestrator.py`):** Fluxo LangGraph com Supervisor Pattern governando transições e retroalimentação de refatoração.
6. **Camada de Exportação Acadêmica (`src/exporter.py`):** Gerador e integrador Pandoc + LuaLaTeX e DOCX ABNT (NBR 14724, 6023 e 10520).
7. **Suite de Testes Automatizados (`tests/`):** Testes unitários de schemas, cliente MCP com mock/live, quality gates e orquestrador.

---

## 2. Technical Context

- **Linguagem & Runtime:** Python 3.12+ (tipagem estrita com Pydantic v2).
- **Dependências Principais:** `httpx`, `pydantic>=2.0`, `langgraph`, `langchain-core`, `pyyaml`, `rich`, `pytest`, `pytest-asyncio`.
- **Armazenamento:** Sistema de arquivos local em Markdown estruturado (`corpus/`, `drafts/`, `output/`).
- **Protocolo de Integração:** MCP (Model Context Protocol) via JSON-RPC 2.0 (`tools/call`).
- **Plataforma Alvo:** Windows 11 / Linux (Execução local na workstation).
- **Conformidade Normativa:** ABNT NBR 14724, NBR 6023, NBR 10520.

---

## 3. Constitution Check

- **I. Supervisão Acadêmica Contínua:** Verificado. O Supervisor Pattern do LangGraph e o `chief_academic_reviewer` interceptam todas as transições entre etapas com base no score 85.
- **II. Zero Alucinação Jurisprudencial:** Verificado. `JurisprudenciaMcpClient` fornece fontes oficiais; `defense_validator` confronta citações contra metadados YAML.
- **III. Densidade Dialética:** Verificado. Rubrica do Revisor Geral e tools de `comparar_teses_juridicas` e `listar_overruling_tema` garantem profundidade crítica.
- **IV. Modularidade e Execução Local:** Verificado. Estrutura pura Python em `src/`, independente de serviços cloud externos fechados.
- **V. Conformidade ABNT:** Verificado. Módulo de exportação com templates dedicados.

---

## 4. Project Structure and Layout

```text
App_Artigos_Cientificos/
├── .specify/                         # Configurações do Spec Kit
├── specs/
│   └── 001-phd-articles-pipeline/    # Spec, Plan e Tasks desta feature
├── src/
│   ├── __init__.py
│   ├── config.py                     # Configurações de ambiente (URLs MCP, tokens, caminhos)
│   ├── schemas.py                    # Schemas Pydantic (MCP Payload, Parecer, Estado LangGraph)
│   ├── mcp_client.py                 # Cliente assíncrono MCP JSON-RPC 2.0 com fallbacks
│   ├── rag_store.py                  # Gerenciador de corpus local Markdown com YAML frontmatter
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── chief_academic_reviewer.py # Agente Revisor Geral / Gatekeeper
│   │   ├── epistemic_agent.py         # Gate 1: Problema, Hipótese, Overruling
│   │   ├── literature_review_agent.py # Gate 2: RSL (PRISMA) e Precedentes Históricos
│   │   ├── methodology_agent.py       # Gate 3: Desenho de Pesquisa e Jurimetria
│   │   ├── sectional_writer_agent.py  # Gate 4: Redação Modular e Citações
│   │   └── defense_validator_agent.py # Gate 5: Auditoria Anti-Alucinação e Banca Sintética
│   ├── orchestrator.py               # Máquina de Estados LangGraph (Supervisor Pattern)
│   ├── exporter.py                   # Compilador Pandoc / LuaLaTeX e DOCX ABNT
│   └── cli.py                        # Ponto de entrada CLI para executar o pipeline
├── tests/
│   ├── test_schemas.py               # Validação de schemas Pydantic
│   ├── test_mcp_client.py            # Testes do cliente MCP com mocks e resiliência
│   ├── test_reviewer_gates.py        # Teste dos Quality Gates 1 a 6 e decisões
│   ├── test_rag_store.py             # Testes de ingestão e parsing YAML Frontmatter
│   └── test_orchestrator.py          # Testes de ponta a ponta do fluxo de trabalho
├── templates/
│   ├── abnt_article.latex            # Template LaTeX ABNT
│   └── abnt_reference.docx           # Documento de referência de estilos DOCX ABNT
├── pyproject.toml                    # Configuração de dependências do projeto
└── README.md                         # Documentação e instruções de execução
```

---

## 5. Fases de Implementação (Roadmap)

### Fase 1: Fundação do Ambiente, Dependências e Schemas (`pyproject.toml`, `src/schemas.py`, `src/config.py`)
- Configurar dependências e variáveis de ambiente no projeto.
- Implementar `src/schemas.py` com validação de dados para MCP, pareceres e estado do grafo.

### Fase 2: Cliente MCP Assíncrono e Armazenamento RAG com YAML (`src/mcp_client.py`, `src/rag_store.py`)
- Implementar `JurisprudenciaMcpClient` com JSON-RPC 2.0, métodos de conveniência acadêmica e fallback resiliente.
- Implementar `rag_store.py` para salvar e consultar julgados em Markdown enriquecidos com metadados YAML.

### Fase 3: Agente Revisor Geral e Quality Gates (`src/agents/chief_academic_reviewer.py`)
- Implementar a lógica de auditoria multidimensional (rigor conceitual, coerência estrutural, ineditismo, fidelidade metodológica).
- Criar a emissão do `ParecerRevisaoGeralSchema` e matriz de refatoração para notas < 85.

### Fase 4: Agentes Especialistas de Pesquisa e Redação (`src/agents/`)
- Implementar `epistemic_agent`, `literature_review_agent`, `methodology_agent`, `sectional_writer_agent` e `defense_validator_agent`.

### Fase 5: Orquestrador LangGraph e Camada de Exportação (`src/orchestrator.py`, `src/exporter.py`, `src/cli.py`)
- Montar o grafo com nós de cada agente conectados ao supervisor e roteamento condicional.
- Implementar a exportação para Markdown consolidado, PDF (Pandoc/LaTeX) e DOCX.

### Fase 6: Validação de Testes e Demonstração End-to-End
- Executar suíte de testes unitários e de integração (`pytest`).
- Validar caso piloto simulado gerando artefatos completos.
