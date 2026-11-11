# Constituição do Pipeline Autônomo de Artigos e Teses de Doutorado

## Princípios Fundamentais do Sistema

### I. Supervisão Acadêmica Contínua e Quality Gates Eliminatórios
Todo o ciclo de vida da pesquisa e da redação acadêmica (*stricto sensu*) é estritamente governado pelo **Agente Revisor Geral (Supervisor / Chief Academic Auditor)**. 
Nenhum artefato, capítulo ou tese avança entre etapas sem submissão e aprovação formal através dos 6 Quality Gates:
- **Gate 1 (Epistêmico):** Problema contemporâneo, hipótese refutável e delimitação do marco teórico.
- **Gate 2 (Bibliográfico):** Revisão sistemática de literatura (RSL/PRISMA), tripé doutrinário e precedentes qualificados.
- **Gate 3 (Metodológico):** Coerência entre desenho de pesquisa, amostragem e jurimetria empírica.
- **Gate 4 (Redação Seccional):** Densidade dialética, transições lógicas e sustentação dogmática.
- **Gate 5 (Auditoria de Citações e Banca Sintética):** Zero alucinação de fontes e resistência da tese a contra-argumentos.
- **Gate 6 (Homologação Final):** Parecer global consolidado e conformidade para compilação.
O limiar mínimo de aprovação em qualquer gate é de 85/100 na Matriz Multidimensional. Notas inferiores exigem refatoração imediata guiada por diretrizes explícitas.

### II. Zero Alucinação Jurisprudencial e Normativa (MCP-First)
É expressamente proibida a fabricação, truncamento ou suposição de dados jurisprudenciais (numeração de acórdãos, datas, relatores, teses de repetitivos/repercussão geral ou enunciados de súmulas).
Todas as referências a julgados dos Tribunais Superiores (STF, STJ, TJs, TRFs) devem obrigatoriamente:
1. Ser consultadas e extraídas via **JurisprudênciaIA MCP** (Model Context Protocol via JSON-RPC 2.0).
2. Ser persistidas localmente no corpus RAG com metadados estruturados em **YAML Frontmatter** (id, tipo, tribunal, relator, data, tema repetitivo, fonte).
3. Ser checadas cruzadamente na fase de banca pelo `defense_validator_agent`.

### III. Densidade Dialética e Rigor Epistemológico Stricto Sensu
O sistema rejeita compilações meramente expositivas ou resumos superficiais de jurisprudência. Toda redação acadêmica deve apresentar:
- Confronto dialético explícito entre correntes doutrinárias minoritárias e majoritárias.
- Identificação precisa de viragens jurisprudenciais (*overruling*), distinções (*distinguishing*) e mutações constitucionais.
- Aderência metodológica comprovável (metodologias qualitativas, quantitativas e jurimetria descritiva).

### IV. Arquitetura Modular, Resiliente e Execução Local (On-Premises)
O pipeline é projetado para operar prioritariamente na estação de trabalho local do pesquisador/engenheiro:
- Orquestração via grafo de estados (LangGraph) com divisão clara de responsabilidades por agentes especialistas.
- Cliente MCP com fallback automático e tratamento resiliente de erros JSON-RPC.
- Separação estrita entre camadas de ingestão, orquestração, RAG em Markdown e compilação documental.

### V. Conformidade Estrita com Normas Técnicas e Tipografia Acadêmica
O pipeline final deve gerar documentos prontos para submissão em programas de pós-graduação e periódicos Qualis A:
- Normas ABNT (NBR 14724 para trabalhos acadêmicos, NBR 6023 para referências, NBR 10520 para citações diretas e indiretas) e suporte a APA 7ª ed.
- Compilação via Pandoc 3.x com motor `lualatex` para PDF tipográfico e Pandoc DOCX com estilos acadêmicos padronizados.

---

## Padrões Tecnológicos e Restrições de Engenharia

1. **Linguagem & Runtime:** Python 3.11+ / 3.12 (tipagem estrita com `pydantic` v2).
2. **Protocolo MCP:** JSON-RPC 2.0 assíncrono via `httpx` (suporte a `http://localhost:8787/mcp` e bridge HTTPS Bearer).
3. **Modelos:**
   - Modelos de alta capacidade analítica (`gemini-2.5-pro` ou superior) para supervisão, síntese epistêmica, redação modular e banca sintética.
   - Modelos rápidos (`gemini-2.5-flash`) para extração de chunks, sanitização e normalização.
4. **Governança de Dados:** Todos os intermediários de escrita e corpora de pesquisa devem ser armazenados em arquivos Markdown legíveis por humanos no workspace local.

---

## Governança e Evolução

- Esta Constituição tem prevalência sobre quaisquer especificações de funcionalidade, decisões de implementação ou templates individuais.
- Alterações nos princípios de governança exigem justificativa arquitetural e incremento de versão semântica.

**Versão**: 1.0.0 | **Ratificado**: 2026-11-11 | **Última Atualização**: 2026-11-11
