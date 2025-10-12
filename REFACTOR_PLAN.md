# 📝 Plano de Refatoração: `app.py`

**Data:** 06/10/2025
**Autor:** Gemini Code Assist

## 1. Objetivo

Este documento delineia o plano para refatorar o arquivo `src/app.py`, movendo toda a lógica de negócio para a camada de serviço (`src/services.py`). O objetivo é alinhar 100% a implementação com a arquitetura documentada (`GEMINI.md`, `doc_tecnica.html`), onde `app.py` atua exclusivamente como um **Controller fino**.

## 2. Justificativa

A análise de conformidade do código com a documentação revelou que `app.py` atualmente contém lógica de negócio, violando o princípio de separação de responsabilidades. Esta refatoração irá:

- **Melhorar a Manutenibilidade:** Centralizar a lógica de negócio na camada de serviço.
- **Aumentar a Testabilidade:** Facilitar a criação de testes unitários para a lógica de negócio, isolando-a do contexto web (Flask).
- **Garantir a Consistência Arquitetural:** Fazer com que o código reflita fielmente a arquitetura de camadas definida.

---

## 3. Plano de Ação e Checklist

A refatoração será executada em duas etapas incrementais e seguras.

### Etapa 1: Mover Lógica de Cálculo de KPIs

**Problema:** A função `_calculate_kpi_summary` está implementada em `app.py`, mas sua responsabilidade é da camada de serviço/análise.

- [x] **Criar nova função em `services.py`:**
  - Criar uma função pública `calculate_kpi_summary(report_path: str) -> dict | None` em `src/services.py`.
- [x] **Mover e Adaptar a Lógica:**
  - Mover o corpo da função `_calculate_kpi_summary` de `app.py` para a nova função em `services.py`.
  - Garantir que as constantes (`ACAO_FLAGS_ATUACAO`, etc.) sejam importadas corretamente em `services.py`.
- [x] **Atualizar Chamadas no Controller:**
  - Em `app.py`, substituir todas as chamadas a `_calculate_kpi_summary` por `services.calculate_kpi_summary`.
- [x] **Limpeza:**
  - Remover a função privada `_calculate_kpi_summary` de `app.py`.

### Etapa 2: Mover Lógica de Exclusão de Relatórios

**Problema:** A rota `delete_report` em `app.py` contém lógica de manipulação de arquivos e banco de dados que pertence à camada de serviço.

- [x] **Criar nova função em `services.py`:**
  - Criar uma função pública `delete_report_and_artifacts(report_id: int, db, Report)` em `src/services.py`.
- [x] **Encapsular a Lógica de Exclusão:**
  - Mover toda a lógica de `try/except`, `shutil.rmtree`, `db.session.delete` e `db.session.commit` da rota `delete_report` para a nova função de serviço.
- [x] **Simplificar o Controller:**
  - Atualizar a rota `delete_report` em `app.py` para apenas chamar `services.delete_report_and_artifacts()`.
  - Manter a lógica de `flash` e `redirect` no controller, pois são responsabilidades da camada de apresentação.
