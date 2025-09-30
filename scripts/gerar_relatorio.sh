#!/bin/bash

# Faz o script parar em caso de erro, variável não definida ou erro em um pipe.
set -euo pipefail

# =============================================================================
# Script Orquestrador para Análise de Alertas e Tendências
#
# Este script automatiza a execução da análise de dados, comparação de
# tendências e geração de um dashboard HTML interativo.
# =============================================================================

# --- Variáveis de Configuração Centralizadas ---
SCRIPT_DIR="src"
VENV_DIR=".venv"
PYTHON_EXEC="${VENV_DIR}/bin/python3"
PIP_EXEC="${VENV_DIR}/bin/pip"

# Scripts Python necessários para a operação completa
REQUIRED_SCRIPTS=(
  "${SCRIPT_DIR}/analisar_alertas.py"
  "${SCRIPT_DIR}/selecionar_arquivos.py"
  "${SCRIPT_DIR}/get_date_range.py"
  "${SCRIPT_DIR}/analise_tendencia.py"
)
EDITOR_TEMPLATE="templates/editor_template.html"
CSV_DIR="data/put_csv_here"

# --- Funções de Validação e Preparação ---

check_requirements() {
  echo "🔎 Verificando pré-requisitos..."
  local all_found=true
  for script in "${REQUIRED_SCRIPTS[@]}"; do
    if [[ ! -f "${script}" ]]; then
      echo "   -> ❌ ERRO: Script essencial não encontrado: ${script}"
      all_found=false
    fi
  done
  if [[ ! -f "${EDITOR_TEMPLATE}" ]]; then
      echo "   -> ❌ ERRO: O arquivo de template '${EDITOR_TEMPLATE}' não foi encontrado."
      all_found=false
  fi
  if [[ ! -d "${CSV_DIR}" ]]; then
      echo "   -> ❌ ERRO: O diretório de entrada '${CSV_DIR}' não foi encontrado."
      all_found=false
  fi
  if ! "${all_found}"; then
    exit 1
  fi
  echo "   -> ✅ Todos os scripts, templates e diretórios necessários foram encontrados."
}

prepare_environment() {
  echo "🛠️  Preparando ambiente de execução..."
  if [ ! -d "${VENV_DIR}" ]; then
    echo "   -> Criando ambiente virtual em '${VENV_DIR}'..."
    python3 -m venv "${VENV_DIR}"
  fi
  echo "   -> Verificando e instalando dependências (pandas, openpyxl)..."
  "${PIP_EXEC}" install --upgrade pip -q
  "${PIP_EXEC}" install pandas openpyxl -q
  echo "   -> ✅ Ambiente pronto."
}

# --- Funções de Análise ---

run_full_analysis() {
  local input_file=$1
  local output_dir=$2
  local trend_report_arg=$3
  echo -e "\n---\n⚙️  Executando análise completa para: ${input_file}"
  "${PYTHON_EXEC}" "${SCRIPT_DIR}/analisar_alertas.py" "${input_file}" \
      --output-summary "${output_dir}/resumo_geral.html" \
      --output-actuation "${output_dir}/atuar.csv" \
      --output-ok "${output_dir}/remediados.csv" \
      --output-instability "${output_dir}/remediados_frequentes.csv" \
      --plan-dir "${output_dir}/planos_squad" \
      --details-dir "${output_dir}/detalhes_problemas" \
      --output-json "${output_dir}/resumo_problemas.json" \
      ${trend_report_arg}
  echo "   -> Análise completa de '${input_file}' concluída."
}

run_summary_only_analysis() {
  local input_file=$1
  local output_dir=$2
  echo -e "\n---\n⚙️  Executando análise otimizada (apenas resumo) para: ${input_file}"
  "${PYTHON_EXEC}" "${SCRIPT_DIR}/analisar_alertas.py" "${input_file}" \
      --output-json "${output_dir}/resumo_problemas.json" \
      --resumo-only
  echo "   -> Análise otimizada de '${input_file}' concluída."
}

# --- Função de Finalização ---

finalize_and_show_link() {
  local target_dir=$1
  local entry_file="resumo_geral.html"
  local editor_final="editor_atuacao.html"
  local csv_source_path="${target_dir}/atuar.csv"

  echo -e "\n---\n📦 Finalizando relatório interativo..."

  if [[ ! -f "${csv_source_path}" ]]; then
      echo "   -> ⚠️ Aviso: Arquivo '${csv_source_path}' não encontrado. O editor interativo será gerado vazio."
      touch "${csv_source_path}"
  fi
  
  awk -v csv_file="${csv_source_path}" '
      /const csvDataPayload = `__CSV_DATA_PLACEHOLDER__`/ {
          print "        const csvDataPayload = `";
          while ((getline line < csv_file) > 0) { print line; }
          close(csv_file);
          print "`;";
          next;
      }
      { print }
  ' "${EDITOR_TEMPLATE}" > "${target_dir}/${editor_final}"
  echo "   -> Editor interativo '${editor_final}' criado com sucesso."

  local absolute_path_dir
  absolute_path_dir=$(cd "${target_dir}" && pwd)
  local file_uri="file://${absolute_path_dir}/${entry_file}"

  echo -e "\n============================================================================="
  echo "✅ ANÁLISE CONCLUÍDA! Relatórios gerados em: ${absolute_path_dir}"
  echo -e "=============================================================================\n"
  echo "🚀 O relatório é totalmente local e NÃO REQUER UM SERVIDOR."
  echo "   Para visualizar, abra o link abaixo no seu navegador:"
  printf '🔗 Link para o relatório: \e]8;;%s\a%s\e]8;;\a\n' "${file_uri}" "${file_uri}"
  echo "-----------------------------------------------------------------------------"
}

# =============================================================================
# --- Lógica Principal do Orquestrador ---
# =============================================================================
main() {
  check_requirements
  prepare_environment

  echo -e "\n---\n🔎 Procurando por arquivos de alerta (.csv) no diretório '${CSV_DIR}'..."
  local input_files=()
  for f in "${CSV_DIR}"/*.csv; do
    [[ -e "$f" ]] || continue
    input_files+=("$f")
  done

  local file_count=${#input_files[@]}
  echo "✅ Encontrado(s) ${file_count} arquivo(s) de dados."
  if [ "${file_count}" -eq 0 ]; then
    echo "❌ Erro: Nenhum arquivo .csv de entrada encontrado em '${CSV_DIR}'. Abortando."
    exit 1
  fi
  
  if [ "${file_count}" -eq 1 ]; then
    echo -e "\n1️⃣  Apenas um arquivo encontrado. Executando análise simples."
    local file_atual=${input_files[0]}
    local filename_base
    filename_base=$(basename "${file_atual}" .csv)
    local output_dir="reports/resultados-${filename_base}"
    
    if [ -d "${output_dir}" ]; then
      local backup_dir="${output_dir}.bkp-$(date +%Y%m%d-%H%M%S)"
      echo "   -> Diretório de resultados existente encontrado. Fazendo backup para '${backup_dir}'..."
      mv "${output_dir}" "${backup_dir}"
    fi
    mkdir -p "${output_dir}"

    run_full_analysis "${file_atual}" "${output_dir}" ""
    
    local resumo_file="${output_dir}/resumo_geral.html"
    echo "🔔 Adicionando nota sobre análise de tendência ao resumo..."
    echo -e '\n<hr><p style="font-style: italic; color: #a0a0b0; text-align: center;">Nota: A análise de tendência será gerada na próxima execução quando um novo arquivo de dados estiver disponível para comparação.</p>' >> "${resumo_file}"
    
    finalize_and_show_link "${output_dir}"
  fi

  if [ "${file_count}" -ge 2 ]; then
    echo -e "\n2️⃣  Múltiplos arquivos encontrados. Iniciando análise de tendência..."
    
    local latest_files=($("${PYTHON_EXEC}" "${SCRIPT_DIR}/selecionar_arquivos.py" "${input_files[@]}"))
    local file_atual=${latest_files[0]}
    local file_anterior=${latest_files[1]}
    echo "   - Período Atual:    ${file_atual}"
    echo "   - Período Anterior: ${file_anterior}"

    local dir_anterior="reports/resultados-temp-anterior"
    local dir_atual="reports/resultados-temp-atual"
    rm -rf "${dir_anterior}" "${dir_atual}"
    mkdir -p "${dir_anterior}" "${dir_atual}"

    run_summary_only_analysis "${file_anterior}" "${dir_anterior}"
    run_full_analysis "${file_atual}" "${dir_atual}" "--trend-report-path ../resumo_tendencia.html"

    echo -e "\n🗓️   Coletando intervalos de datas dos arquivos..."
    local date_range_anterior=$("${PYTHON_EXEC}" "${SCRIPT_DIR}/get_date_range.py" "${file_anterior}")
    local date_range_atual=$("${PYTHON_EXEC}" "${SCRIPT_DIR}/get_date_range.py" "${file_atual}")
    echo "   - Intervalo Anterior: ${date_range_anterior}"
    echo "   - Intervalo Atual:    ${date_range_atual}"

    echo "📊 Gerando relatório de tendência..."
    "${PYTHON_EXEC}" "${SCRIPT_DIR}/analise_tendencia.py" \
      "${dir_anterior}/resumo_problemas.json" "${dir_atual}/resumo_problemas.json" \
      "${file_anterior}" "${file_atual}" "${date_range_anterior}" "${date_range_atual}"

    local filename_base_atual
    filename_base_atual=$(basename "${file_atual}" .csv)
    local final_dir="reports/analise-comparativa-${filename_base_atual}"
    echo "📂 Consolidando todos os artefatos em: ${final_dir}"
    
    if [ -d "${final_dir}" ]; then
      local backup_dir="${final_dir}.bkp-$(date +%Y%m%d-%H%M%S)"
      echo "   -> Diretório de análise existente encontrado. Fazendo backup para '${backup_dir}'..."
      mv "${final_dir}" "${backup_dir}"
    fi
    mv "${dir_atual}" "${final_dir}"
    mv resumo_tendencia.html "${final_dir}/"
    mkdir -p "${final_dir}/dados_comparacao"
    mv "${dir_anterior}/resumo_problemas.json" "${final_dir}/dados_comparacao/resumo_problemas_anterior.json"
    rm -rf "${dir_anterior}"

    finalize_and_show_link "${final_dir}"
  fi
  
  if [ -f "invalid_self_healing_status.csv" ]; then
    local final_log_dir
    final_log_dir=$(find ./reports -maxdepth 1 -type d -name "resultados-*" -o -name "analise-comparativa-*" | head -n 1)
    if [[ -n "${final_log_dir}" ]]; then
        echo "   -> Movendo 'invalid_self_healing_status.csv' para '${final_log_dir}'..."
        mv invalid_self_healing_status.csv "${final_log_dir}/"
    fi
  fi
}

main
