# Pipeline Autônomo Local de Pesquisa, Redação Acadêmica e Projetos de Doutorado com Integração MCP

Sistema multiagente em ambiente local (*on-premises*) para produção de artigos científicos e teses de doutorado (*stricto sensu*), governado por um **Agente Revisor Geral** com 6 Quality Gates eliminatórios e integrado nativamente ao **JurisprudênciaIA MCP** para garantia de **Zero Alucinação**.

Desenvolvido segundo a metodologia **Spec-Driven Development (SDD)** do **GitHub Spec Kit** (`specify`).

---

## 🏛️ Princípios Arquiteturais e Governança

1. **Supervisão Contínua (Supervisor Pattern):** O `chief_academic_reviewer` avalia cada avanço através de 6 Quality Gates eliminatórios com nota de corte mínima de **85.0/100**, incluindo travas estritas contra inversão de capítulos, proporção de bullets (>15%) e vazamentos de depuração.
2. **Zero Alucinação & Zero Tool Leakage:** Conexão direta com ferramentas MCP via JSON-RPC 2.0, indexação no corpus local com metadados em **YAML Frontmatter** e sanitização determinística para expurgo de logs de APIs, comandos de prompt e ementas brutas coladas.
3. **Densidade Dialética em Prosa Contínua:** Confrontação de correntes doutrinárias, *overruling*, *distinguishing* e síntese orgânica de precedentes vinculantes (ex.: Tema 1249/STJ) sem formatação esquemática.
4. **Conformidade ABNT NBR 6022, 6028, 6023 e 14724:** Ordenação canônica inalterável (Seção 1 Introdução $\rightarrow$ Seção 2 Marco Teórico $\rightarrow$ Seção 3 Desenvolvimento $\rightarrow$ Seção 4 Considerações Finais), elementos pré-textuais completos (autoria, filiações, resumo vernáculo, abstract e keywords) e referências contextuais, com exportação automática em Markdown, DOCX e PDF nativo.

---

## 🚀 Como Executar

### 1. Testes Automatizados (43 Testes · 100% Aprovados)
```bash
python -m pytest tests/ -v
```

### 2. Executar o Pipeline Acadêmico
```bash
python -m src.cli run --titulo "A Modulação de Efeitos no Overruling Tributário" --tema "Modulação de Efeitos e Segurança Jurídica"
```

### 3. Inspecionar o Corpus RAG Indexado
```bash
python -m src.cli corpus
```

### 4. Testar Conexão com o Servidor MCP
```bash
python -m src.cli test-mcp --url http://localhost:8787
```

---

## 📂 Estrutura do Projeto

- `.specify/`: Framework GitHub Spec Kit (Constituição, templates e workflows)
- `specs/001-phd-articles-pipeline/`: Especificação formal, plano de implementação e lista de tarefas
- `docs/`:
  - `especificacao_tecnica_strictosensu.md`: Arquitetura completa, diagramas e matriz de modelos
  - `memoria.md`: Rastreabilidade de engenharia e decisões técnicas
- `src/`:
  - `mcp_client.py`: Cliente JSON-RPC 2.0 assíncrono com fallback resiliente
  - `rag_store.py`: Armazenamento e conferência de citações em Markdown com YAML
  - `sanitizer.py`: Sanitizador universal de logs, bullets e vazamentos de ferramentas
  - `schemas.py`: Modelos de dados e validação Pydantic v2 com suporte ABNT
  - `agents/`: Agente Revisor Geral e os 5 agentes especialistas
  - `orchestrator.py`: Grafo de estados e supervisor com Quality Gates
  - `exporter.py`: Compilador acadêmico ABNT com ordenação canônica e PDF nativo
  - `improver.py`: Módulo de elevação e refatoração de papers externos
  - `importer.py`: Extrator de textos multi-formato (PDF/DOCX/MD)
  - `web.py`: Backend FastAPI com dashboard web em tempo real
  - `cli.py`: Interface de linha de comando com Rich
- `corpus/`: Repositório local de precedentes autênticos indexados
- `output/`: Documentos finais consolidados (Markdown, PDF ABNT e DOCX)
- `tests/`: Bateria completa com 43 testes unitários e de integração

