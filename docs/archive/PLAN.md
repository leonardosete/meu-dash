# 📈 Plano de Implementação: Análise Comparativa

Este documento descreve o plano de ação para refatorar a lógica comparativa, garantindo que cada novo upload seja comparado com o relatório mais recente que participou de uma análise de comparativa anterior.

## Roadmap da Funcionalidade

### Prioridade 1: Lógica de Negócio (Service Layer)

- [x] **Refatorar `services.py`:** Modificar a função `process_upload_and_generate_reports` para alterar a lógica de busca do "relatório anterior".
  - Em vez de buscar o `Report` mais recente, a lógica deve buscar a `TrendAnalysis` mais recente.
  - A partir da `TrendAnalysis` mais recente, obter o `current_report` associado. Este será o verdadeiro "relatório anterior" para a nova comparação.
  - Se nenhuma `TrendAnalysis` existir, a lógica deve voltar ao comportamento antigo (comparar com o `Report` mais recente) para a primeira análise de tendência.

### Prioridade 2: Testes e Validação

- [x] **Atualizar Testes de Serviço:** Modificar os testes existentes para simular o novo fluxo:
  - Teste 1: Upload de arquivo A (sem tendência).
  - Teste 2: Upload de arquivo B (gera tendência B vs A).
  - Teste 3: Upload de arquivo C (deve gerar tendência C vs B).
- [x] **Teste Manual:** Executar o fluxo completo na interface para validar o comportamento esperado:
  - Fazer upload do `file-1.csv`.
  - Fazer upload do `file-2.csv` (verificar se a tendência foi gerada).
  - Fazer upload do `file-3.csv` (verificar se a nova tendência foi gerada comparando com o `file-2.csv`).