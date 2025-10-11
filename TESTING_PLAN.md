# 🧪 Plano de Testes de Aceitação - Redesign da Interface

Este documento descreve os cenários de teste para validar a nova experiência do usuário (UX) implementada na página `index.html`, conforme definido no `PLAN-UX.md`.

**Objetivo:** Garantir que a nova interface atende às necessidades das personas definidas (Analista, Gestor) e que todos os fluxos de trabalho são intuitivos e funcionais.

---

## Cenário 1: Fluxo do Analista de Operações

**Persona:** Analista de Operações
**Objetivo:** Realizar uma análise de rotina, comparando um novo arquivo de dados com o histórico mais recente, e verificar os KPIs atualizados sem sair da página.

| Passo | Ação do Usuário | Resultado Esperado | Status |
| :--- | :--- | :--- | :--- |
| 1 | Acessar a página principal. | A página carrega com a aba "Análise Padrão" ativa por padrão. | `[x]` |
| 2 | Arrastar e soltar (ou selecionar) um arquivo `.csv` no campo de upload da aba "Análise Padrão". | O nome do arquivo aparece, e o texto "Clique ou arraste..." desaparece. | `[x]` |
| 3 | Clicar no botão "Analisar e Comparar com Histórico". | O botão fica desabilitado com o texto "Processando...". | `[x]` |
| 4 | Aguardar o processamento. | Uma notificação "toast" de sucesso aparece no canto da tela. O botão volta ao estado normal. | `[x]` |
| 5 | Observar o dashboard de KPIs. | O dashboard de KPIs no topo da página é atualizado com os novos valores da análise recém-concluída. | `[x]` |
| 6 | Clicar na "orelha" de link no card de KPI "Sucesso da Automação". | O relatório completo (`resumo_geral.html`) da nova análise é aberto em uma nova aba do navegador. | `[x]` |

---

## Cenário 2: Fluxo do Gestor de Equipe

**Persona:** Gestor de Equipe
**Objetivo:** Realizar uma análise comparativa pontual entre dois arquivos específicos para uma reunião.

| Passo | Ação do Usuário | Resultado Esperado | Status |
| :--- | :--- | :--- | :--- |
| 1 | Acessar a página principal. | A página carrega normalmente. | `[x]` |
| 2 | Clicar na aba "Comparação Direta". | O conteúdo da aba muda, exibindo um único campo de upload múltiplo. | `[x]` |
| 3 | Selecionar dois arquivos `.csv` nos respectivos campos de upload. | Os nomes dos arquivos aparecem corretamente em cada campo. | `[x]` |
| 4 | Clicar no botão "Comparar Arquivos". | O botão fica desabilitado com o texto "Comparando...". A página é redirecionada para o relatório de tendência (`comparativo_periodos.html`) após o processamento. | `[x]` |
| 5 | Verificar o relatório de tendência. | O relatório gerado contém a comparação dos dois arquivos selecionados, e não do histórico automático. | `[x]` |

---

## Cenário 3: Revisão de Acessos Rápidos e Links Gerais

**Persona:** Qualquer Usuário
**Objetivo:** Validar que todos os links de navegação e acesso rápido na barra lateral e no rodapé estão funcionando corretamente.

| Passo | Ação do Usuário | Resultado Esperado | Status |
| :--- | :--- | :--- | :--- |
| 1 | Clicar no link "Documentação Gerencial" na barra lateral. | O `doc_gerencial.html` abre em uma nova aba. | `[x]` |
| 2 | Clicar no link "Documentação Técnica" na barra lateral. | O `doc_tecnica.html` abre em uma nova aba. | `[x]` |
| 3 | Clicar no link "Ver Última Análise de Tendência" (se disponível). | O último relatório de tendência abre em uma nova aba. | `[x]` |
| 4 | Clicar no link "Ver Histórico de Análises" no card da "Análise Padrão". | O usuário é redirecionado para a página `/relatorios`. | `[x]` |
| 5 | Clicar no card "Acesso Administrativo" na barra lateral. | O usuário é redirecionado para a página de login de administrador. | `[x]` |

---

## Coleta de Feedback Qualitativo

- `[ ]` Apresentar a nova interface para um usuário de cada persona (Analista, Gestor).
- `[ ]` Observar a interação sem dar instruções.
- `[ ]` Coletar impressões sobre a clareza, facilidade de uso e percepção de valor do novo layout.
