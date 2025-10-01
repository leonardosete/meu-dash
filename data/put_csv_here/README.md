# 📥 Diretório de Entrada de Dados

Este diretório (`data/put_csv_here/`) é o local onde você deve colocar os arquivos de dados (`.csv`) para serem analisados.

---

### 🚀 Como Usar

1.  **Coloque seus arquivos aqui:** Salve um ou mais arquivos `.csv` com os dados de alerta neste diretório.
    *   **Análise Simples:** Use 1 arquivo para um relatório do período.
    *   **Análise de Tendência:** Use 2 ou mais arquivos para comparar o período atual com o anterior.

2.  **Execute o projeto:** Utilize o script `gerar_relatorio.sh` ou `gerar_relatorio.ps1` na raiz do projeto.

---

### ✅ Requisitos do Arquivo CSV

Para que a análise funcione corretamente, seu arquivo `.csv` **deve conter as seguintes colunas essenciais**:

*   `sys_created_on`: Data e hora em que o alerta foi criado. Usada para ordenação cronológica.
*   `severity`: A severidade do alerta (ex: `Critical`, `Major`).
*   `sn_priority_group`: O grupo de prioridade do alerta (ex: `Urgente`, `Alto(a)`).
*   `self_healing_status`: O status da automação de remediação (ex: `REM_OK`, `REM_NOT_OK`, ou vazio).

Além disso, as colunas a seguir são cruciais para o agrupamento e categorização dos problemas:
*   `assignment_group`: A squad ou time responsável.
*   `metric_name`: O nome da métrica ou tipo de problema.
*   `cmdb_ci` ou `node`: O recurso (CI/Nó) afetado pelo alerta.
*   `description`: A descrição detalhada do alerta, usada para desambiguar e agrupar casos corretamente.