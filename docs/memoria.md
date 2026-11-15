# Memória de Engenharia, Evolução e Decisões Técnicas · StrictoSensu

Este documento registra cronologicamente todas as novas alterações, melhorias de arquitetura, correções de bugs, decisões técnicas e aprimoramentos de UI/UX implementados no projeto **StrictoSensu**.

---

## [2026-11-14] — Consolidação da Arquitetura, Nova UI e Validação em Produção

### 1. Interface Web & Identidade Visual (UI/UX)
- **Barra Lateral Esquerda (*Dark Navy* `#091322`):**
  - Implementação de sidebar fixa com logo oficial `logo_emblem.png`, título tipográfico *StrictoSensu* e badge `QUALIS A · ABNT`.
  - Navegação vertical com ícones em linha (Gerar Paper / Tese, Revisar & Elevar Paper, Histórico & Acervo, Monitor de Gates, Configurações e Suporte).
  - Rodapé da barra lateral com telemetria do servidor MCP Cloudflare, contador do Corpus RAG e botão de alternância para o modo escuro.
- **Header Superior Limpo (*Warm Alabaster*):**
  - Eliminação de container escuro inflado no topo; inclusão de divisória em ouro envelhecido (*accent gold*), título em caixa alta e subtítulo institucional.
  - Pílulas de telemetria discretas e pílula de seleção de tema.
- **Card de Formulário Acadêmico (Coluna Esquerda):**
  - Inclusão do **Hero Banner Azul Royal** em gradiente com emblema dourado com louros (Qualis A / ABNT).
  - Ícones estilizados em tom âmbar nos rótulos de cada campo do formulário.
  - Seletor de tipologia documental (*Artigo Científico ABNT NBR 6022* vs *Projeto de Tese ABNT NBR 15287 / 14724*).
  - Justificação tipográfica aplicada aos textos descritivos das opções (`.doctype-desc`) para perfeito alinhamento e legibilidade.
  - Botão principal arredondado centralizado em azul royal com ícone de ação.
- **Card de Monitor de Quality Gates (Coluna Direita):**
  - Cabeçalho com ícone de telemetria e pílula `● Em espera` sem quebra de linha (`white-space: nowrap; flex-shrink: 0;`).
  - Título do monitor ajustado com `clamp` e `white-space: nowrap;` para acomodação em linha única em todas as resoluções.
  - **Stepper Horizontal:** Linha conectora com nós circulares de G1 a G6 e contador de progresso dinâmico (`0/6`).
  - **Linha do Tempo Vertical:** Badges `G1` a `G6`, ícones especializados para cada gate e tags de status (`AGUARDANDO`, `EM EXECUÇÃO`, `APROVADO`, `AJUSTES`).
  - **Console de Atividade Terminal (`>_ Console de Atividade`):** Container com barra de status verde `● Tempo real` e rolagem automática de logs.

### 2. Engenharia de Agentes & Orquestrador
- **Indexação Dinâmica no Corpus RAG:**
  - Ajustado o `LiteratureReviewAgent` (`src/agents/literature_review_agent.py`) para salvar e indexar automaticamente no `RagStore` todas as teses vinculantes e linhas do tempo retornadas pelo servidor MCP.
  - Atualizado o `SectionalWriterAgent` (`src/agents/sectional_writer_agent.py`) para receber a referência do `RagStore` e indexar as ementas e acórdãos consultados em tempo de redação.
  - Vinculado o `rag_store` ao instanciar o `SectionalWriterAgent` dentro do `AcademicPipelineOrchestrator` (`src/orchestrator.py`).
- **Resolução de Falsos Positivos no Gate 5 (Auditoria Anti-Alucinação):**
  - Com a indexação automática dos julgados reais retornados pelo MCP, o `DefenseValidatorAgent` valida com precisão matemática as citações de processos (como acórdãos do STJ sobre a Lei Maria da Penha e Tema Repetitivo 1.249/STJ), chancelando notas elevadas (ex.: **94.0/100**) no Gate 5.

### 3. Teste Prático Real de Doutorado
- **Tema Avaliado:** *"A EFETIVIDADE DA PROTEÇÃO À MULHER EM SITUAÇÃO DE VIOLÊNCIA: UMA ANÁLISE DAS ALTERAÇÕES NA LEI MARIA DA PENHA (2025-2026)"*.
- **Resultado:** **`HOMOLOGADO_SUCESSO`** com notas superiores a 90 em todos os gates (G1: 90.0, G2: 92.0, G3: 91.75, G4: 91.25, G5: 94.0, G6: 95.5).
- **Entregáveis:** Artigo acadêmico completo com mais de **7.600 palavras** compilado em Markdown, PDF ABNT e DOCX Word.

### 4. Documentação Técnica
- Criação da pasta oficial `docs/`.
- Criação do documento [especificacao_tecnica_strictosensu.md](file:///c:/App_Artigos_Cientificos/docs/especificacao_tecnica_strictosensu.md) contendo arquitetura em Mermaid, matriz de modelos, especificações de APIs, normas ABNT e manual de operação.
- Criação deste documento de rastreabilidade [memoria.md](file:///c:/App_Artigos_Cientificos/docs/memoria.md).

### 5. Qualidade de Código & Testes
- Bateria de testes automatizados com `pytest`: **34 aprovados** (100% verde).

---

## [2026-11-15] — Reforma Estrutural ABNT NBR 6022, Erradicação de Vazamento de Metadados e Síntese Jurisprudencial Orgânica

### 1. Diagnóstico e Autópsia Comparativa
- Confronto forense entre o artigo gerado anteriormente e artigos de referência humana (*Revista Eletrônica Direito e Sociedade* / Canoas v.13/2025 e TCC Artigo Científico / PUC Goiás 2026).
- Identificadas três anomalias centrais:
  1. Subversão caótica da ordem de seções (Seção 2 "Marco Teórico" inserida antes da Seção 1 "Introdução").
  2. Vazamento severo de logs de depuração do MCP/RAG (`Resultado JurisprudenciaIA`, `quando a fonte nao disponibilizar`, `Metadados ausentes`, marcadores `[J1 - STF]`).
  3. Falta de densidade dialética e excesso de formatação esquemática (116 bullets no PDF), além de citações genéricas descontextualizadas de Dworkin e Taruffo sobre direito tributário em temas de Lei Maria da Penha.

### 2. Implementações e Correções de Engenharia
- **Criação do Sanitizador Universal (`src/sanitizer.py`):**
  - Módulo puro e reutilizável com `sanitizar_texto_academico`, `verificar_vazamentos`, `calcular_proporcao_bullets` e `converter_dados_jurimetria_em_prosa`.
  - Expurgo determinístico de comandos literais de consulta, cabeçalhos de depuração, carimbos de API, notas de cautela sistêmica e marcadores não resolvidos.
- **Estruturação Normativa e Travamento Sequencial (ABNT NBR 6022):**
  - Inclusão dos campos de autoria, filiação acadêmica/institucional, resumo vernáculo (NBR 6028), abstract em língua estrangeira e keywords no `DocumentoAcademicoState` (`src/schemas.py`).
  - Ordenação canônica estrita das seções no `AcademicExporter` (`src/exporter.py`): garantia matemática de que a Seção 1 (Introdução) sempre antecede as seções de desenvolvimento, conclusão e referências.
  - Geração de referências bibliográficas e jurisprudenciais estritamente contextuais (Lei nº 11.340/2006, Lei nº 14.550/2023, STJ Tema 1249, STF ADI 6138, Alice Bianchini, Maria Berenice Dias) segundo a ABNT NBR 6023.
- **Agente de Síntese Jurisprudencial e Eliminação de Fallbacks Genéricos:**
  - `SectionalWriterAgent` e `MethodologyAgent` reestruturados para exigir e redigir estritamente em **prosa dissertativa contínua**, sem transcrição de ementas brutas ou blocos em caixa alta.
  - Contextualização dogmática dinâmica no fallback para temas de gênero, violência contra a mulher, tributário ou teoria geral dos precedentes.
- **Fortalecimento dos Quality Gates no Revisor Geral (`src/agents/chief_academic_reviewer.py`):**
  - Gate 4 com validação anti-vazamento, trava contra ordem de seções invertida e bloqueio contra tom esquemático (proporção de bullets > 15%).
  - Gate 6 com validação de conformidade com a ABNT NBR 6022 e higiene textual final.

### 3. Validação e Qualidade
- Bateria de testes expandida para **43 testes automatizados** com `pytest` (100% aprovados), cobrindo sanitização, detecção de vazamentos, proporção de bullets, ordenação ABNT e exportação PDF.
- Recompilação do artigo e do PDF de teste da Lei Maria da Penha demonstrando zero vazamento de dados técnicos e total fluidez argumentativa.

### 4. Revisão Técnica & Endurecimento Cirúrgico
- **Resolução de Falso-Positivo em Títulos Acadêmicos:** Aperfeiçoada a regex em `calcular_proporcao_bullets` (`src/sanitizer.py`) para reconhecer `^\d+(\.\d+)*\.?\s+(introdução|marco|...)`, impedindo que títulos de seções numeradas fossem erroneamente computados como marcadores de lista.
- **Higienização de Pontuação Pré-Textual:** Aplicado `strip(". ")` em `src/exporter.py` para palavras-chave e keywords, garantindo separação conforme a ABNT NBR 6022 sem pontos duplicados (`..`).
- **Resgate Seguro de Conclusão:** Salvaguarda em `src/exporter.py` para injetar a seção de considerações finais a partir de `state.conclusao` caso não indexada previamente no dicionário de capítulos.
- **Atualização da Especificação Técnica:** Atualizados [especificacao_tecnica_strictosensu.md](file:///c:/App_Artigos_Cientificos/docs/especificacao_tecnica_strictosensu.md), [spec.md](file:///c:/App_Artigos_Cientificos/specs/001-phd-articles-pipeline/spec.md), [plan.md](file:///c:/App_Artigos_Cientificos/specs/001-phd-articles-pipeline/plan.md), [tasks.md](file:///c:/App_Artigos_Cientificos/specs/001-phd-articles-pipeline/tasks.md) e [README.md](file:///c:/App_Artigos_Cientificos/README.md).
