# Pipeline Autônomo Local de Pesquisa, Redação Acadêmica e Projetos de Doutorado com Integração MCP

Sistema multiagente em ambiente local (*on-premises*) para produção de artigos científicos e teses de doutorado (*stricto sensu*), governado por um **Agente Revisor Geral** com 6 Quality Gates eliminatórios e integrado nativamente ao **JurisprudênciaIA MCP** para garantia de **Zero Alucinação**.

Desenvolvido segundo a metodologia **Spec-Driven Development (SDD)** do **GitHub Spec Kit** (`specify`).

---

## 🏛️ Princípios Arquiteturais e Governança

1. **Supervisão Contínua (Supervisor Pattern):** O `chief_academic_reviewer` avalia cada avanço através de 6 Quality Gates eliminatórios com nota de corte mínima de **85.0/100**.
2. **Zero Alucinação Jurisprudencial:** Conexão direta com 14 ferramentas MCP via JSON-RPC 2.0 e indexação no corpus local com metadados em **YAML Frontmatter**.
3. **Densidade Dialética:** Confrontação de correntes doutrinárias, *overruling*, *distinguishing* e jurimetria descritiva.
4. **Conformidade ABNT:** Exportação automática em Markdown, DOCX e PDF conforme as normas NBR 14724, NBR 6023 e NBR 10520.

---

## 🚀 Como Executar

### 1. Testes Automatizados
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
- `src/`:
  - `mcp_client.py`: Cliente JSON-RPC 2.0 assíncrono com fallback resiliente
  - `rag_store.py`: Armazenamento e conferência de citações em Markdown com YAML
  - `schemas.py`: Modelos de dados e validação Pydantic v2
  - `agents/`: Agente Revisor Geral e os 5 agentes especialistas
  - `orchestrator.py`: Grafo de estados e supervisor com Quality Gates
  - `exporter.py`: Compilador acadêmico ABNT (Pandoc / DOCX / PDF)
  - `cli.py`: Interface de linha de comando com Rich
- `corpus/`: Repositório local de precedentes autênticos indexados
- `output/`: Documentos finais consolidados (Markdown e DOCX)
- `tests/`: Bateria completa de testes unitários e de integração
