# 📈 Plano de Implementação: Histórico de Relatórios de Tendência

Este documento descreve o plano de ação para implementar a funcionalidade de histórico de relatórios de tendência. O objetivo é rastrear o progresso e garantir que todos os passos sejam concluídos, incluindo testes.

## Roadmap da Funcionalidade

### Prioridade 1: Estrutura de Dados

- [x] **Criar Modelo `TrendAnalysis`:** Em `src/app.py`, definir a nova classe `TrendAnalysis(db.Model)`.
- [x] **Gerar Migração do Banco de Dados:** Executar `flask db migrate -m "Add TrendAnalysis table"`.
- [x] **Aplicar Migração:** Executar `flask db upgrade`.

### Prioridade 2: Lógica de Negócio

- [x] **Atualizar `services.py`:** Na função `process_upload_and_generate_reports`, salvar uma nova instância de `TrendAnalysis` no banco de dados sempre que uma tendência for gerada.

### Prioridade 3: Camada de Apresentação

- [x] **Otimizar Rota Principal:** Em `src/app.py`, na rota `/`, consultar a tabela `TrendAnalysis` para buscar os últimos 60 registros.
- [x] **Atualizar Template `upload.html`:** Modificar o card de "Análise de Tendência" para exibir a lista de históricos.

### Prioridade 4: Testes e Validação

- [x] **Criar Teste de Modelo:** Validar a criação do objeto `TrendAnalysis`.
- [x] **Atualizar Teste de Serviço:** Verificar se um registro `TrendAnalysis` é criado após a análise.
- [x] **Criar Teste de Rota:** Validar se a rota `/` carrega e exibe o histórico.
- [x] **Teste Manual:** Executar o fluxo completo na interface.
