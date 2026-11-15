# Regras de Desenvolvimento e Governança do Projeto StrictoSensu

## 1. Registro Obrigatório de Memória de Engenharia
Sempre que qualquer alteração, correção, refatoração ou melhoria for implementada no projeto:
- O agente **DEVE OBRIGATORIAMENTE** atualizar o arquivo `docs/memoria.md`.
- Cada registro deve incluir a data, a categoria da alteração (UI/UX, Backend, Agentes, Correção de Bug, etc.), a descrição concisa do que foi alterado e o impacto no sistema.
- Nunca encerre uma rodada de melhorias ou correções sem refletir o resumo dessas mudanças em `docs/memoria.md`.

## 2. Princípios de Engenharia de Software
- **Clean Code & Simplicidade:** Mudanças cirúrgicas, código legível e sem excesso de complexidade.
- **SOLID:** Manter a alta coesão e baixo acoplamento entre os agentes e as camadas de dados.
- **Prevenção de Regressão:** Após qualquer alteração no código de backend ou frontend, executar a suíte de testes com `python -m pytest -q` para garantir 100% de testes verdes.
- **Segurança:** Sanitização rigorosa de caminhos de arquivos (`Path Traversal`) e dados renderizados no DOM (`XSS`).
