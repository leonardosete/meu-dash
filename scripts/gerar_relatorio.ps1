<#
.SYNOPSIS
    Script Orquestrador para Análise de Alertas e Tendências.
.DESCRIPTION
    Este script automatiza a execução da análise de dados, comparação de
    tendências e geração de um dashboard HTML interativo.
    Esta é uma conversão para PowerShell do script original 'gerar_relatorio.sh'.
#>

# --- Tratamento de Erros e Modo Estrito ---
# Emula 'set -euo pipefail' do Bash para parar o script em erros.
$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

# =============================================================================
# --- Variáveis de Configuração Centralizadas ---
# =============================================================================
$PSScriptRoot = Get-Location # Diretório onde este script PowerShell está localizado.
$SourceDir = Join-Path $PSScriptRoot "src"
$VenvDir = Join-Path $PSScriptRoot ".venv"

# Define os executáveis Python de forma portável (Windows/Linux)
if ($IsWindows) {
    $PythonExec = Join-Path $VenvDir "Scripts" "python.exe"
    $PipExec = Join-Path $VenvDir "Scripts" "pip.exe"
}
else {
    $PythonExec = Join-Path $VenvDir "bin" "python3"
    $PipExec = Join-Path $VenvDir "bin" "pip"
}

# Scripts Python necessários para a operação completa
$RequiredScripts = @(
    (Join-Path $SourceDir "analisar_alertas.py"),
    (Join-Path $SourceDir "selecionar_arquivos.py"),
    (Join-Path $SourceDir "get_date_range.py"),
    (Join-Path $SourceDir "analise_tendencia.py")
)
$EditorTemplate = Join-Path $PSScriptRoot "templates" "editor_template.html"
$CsvDir = Join-Path $PSScriptRoot "data" "put_csv_here"

# =============================================================================
# --- Funções de Validação e Preparação ---
# =============================================================================

function Test-Prerequisites {
    Write-Host "🔎 Verificando pré-requisitos..." -ForegroundColor Cyan
    $allFound = $true

    foreach ($script in $RequiredScripts) {
        if (-not (Test-Path -Path $script -PathType Leaf)) {
            Write-Host "   -> ❌ ERRO: Script essencial não encontrado: $script" -ForegroundColor Red
            $allFound = $false
        }
    }

    if (-not (Test-Path -Path $EditorTemplate -PathType Leaf)) {
        Write-Host "   -> ❌ ERRO: O arquivo de template '$EditorTemplate' não foi encontrado." -ForegroundColor Red
        $allFound = $false
    }

    if (-not (Test-Path -Path $CsvDir -PathType Container)) {
        Write-Host "   -> ❌ ERRO: O diretório de entrada '$CsvDir' não foi encontrado." -ForegroundColor Red
        $allFound = $false
    }

    if (-not $allFound) {
        throw "Um ou mais pré-requisitos não foram encontrados. Abortando."
    }
    
    Write-Host "   -> ✅ Todos os scripts, templates e diretórios necessários foram encontrados." -ForegroundColor Green
}

function Initialize-Environment {
    Write-Host "🛠️  Preparando ambiente de execução..." -ForegroundColor Cyan
    if (-not (Test-Path -Path $VenvDir -PathType Container)) {
        Write-Host "   -> Criando ambiente virtual em '$VenvDir'..."
        # Tenta usar 'python3' primeiro, depois 'python' para maior compatibilidade
        try {
            python3 -m venv $VenvDir
        } catch {
            python -m venv $VenvDir
        }
    }

    Write-Host "   -> Verificando e instalando dependências (pandas, openpyxl)..."
    & $PipExec install --upgrade pip -q
    & $PipExec install pandas openpyxl -q
    Write-Host "   -> ✅ Ambiente pronto." -ForegroundColor Green
}

# =============================================================================
# --- Funções de Análise ---
# =============================================================================

function Start-FullAnalysis {
    param(
        [string]$InputFile,
        [string]$OutputDir,
        [string]$TrendReportArg
    )
    Write-Host "`n---`n⚙️  Executando análise completa para: $InputFile" -ForegroundColor Yellow
    
    $arguments = @(
        (Join-Path $SourceDir "analisar_alertas.py"),
        $InputFile,
        "--output-summary", (Join-Path $OutputDir "resumo_geral.html"),
        "--output-actuation", (Join-Path $OutputDir "atuar.csv"),
        "--output-ok", (Join-Path $OutputDir "remediados.csv"),
        "--output-instability", (Join-Path $OutputDir "remediados_frequentes.csv"),
        "--plan-dir", (Join-Path $OutputDir "planos_squad"),
        "--details-dir", (Join-Path $OutputDir "detalhes_problemas"),
        "--output-json", (Join-Path $OutputDir "resumo_problemas.json")
    )

    if (-not [string]::IsNullOrEmpty($TrendReportArg)) {
        $arguments += $TrendReportArg.Split(' ')
    }

    & $PythonExec $arguments
    
    Write-Host "   -> Análise completa de '$InputFile' concluída." -ForegroundColor Green
}

function Start-SummaryOnlyAnalysis {
    param(
        [string]$InputFile,
        [string]$OutputDir
    )
    Write-Host "`n---`n⚙️  Executando análise otimizada (apenas resumo) para: $InputFile" -ForegroundColor Yellow
    
    & $PythonExec (Join-Path $SourceDir "analisar_alertas.py") $InputFile `
        --output-json (Join-Path $OutputDir "resumo_problemas.json") `
        --resumo-only
    
    Write-Host "   -> Análise otimizada de '$InputFile' concluída." -ForegroundColor Green
}

# =============================================================================
# --- Função de Finalização ---
# =============================================================================

function Complete-Report {
    param(
        [string]$TargetDir
    )
    $EntryFile = "resumo_geral.html"
    $EditorFinal = "editor_atuacao.html"
    $CsvSourcePath = Join-Path $TargetDir "atuar.csv"

    Write-Host "`n---`n📦 Finalizando relatório interativo..." -ForegroundColor Cyan

    if (-not (Test-Path -Path $CsvSourcePath -PathType Leaf)) {
        Write-Host "   -> ⚠️ Aviso: Arquivo '$CsvSourcePath' não encontrado. O editor interativo será gerado vazio." -ForegroundColor Yellow
        New-Item -Path $CsvSourcePath -ItemType File | Out-Null
    }
    
    $templateContent = Get-Content -Path $EditorTemplate -Raw
    $csvContent = Get-Content -Path $CsvSourcePath -Raw
    
    # Prepara o payload para injeção no template. O acento grave (`) é o caractere de escape em strings JS.
    $replacementPayload = "const csvDataPayload = `${csvContent}`;"

    # Substitui a linha do placeholder no template pelo conteúdo do CSV.
    $finalContent = $templateContent -replace '^\s*const csvDataPayload = `__CSV_DATA_PLACEHOLDER__`', "        $replacementPayload"

    $finalContent | Set-Content -Path (Join-Path $TargetDir $EditorFinal) -Encoding UTF8
    Write-Host "   -> Editor interativo '$EditorFinal' criado com sucesso." -ForegroundColor Green

    $absolutePathDir = (Resolve-Path -Path $TargetDir).ProviderPath
    # Garante que a URI do arquivo use barras normais (/) para compatibilidade
    $fileUri = "file:///$($absolutePathDir -replace '\\', '/')/$EntryFile"

    Write-Host "`n=============================================================================" -ForegroundColor Green
    Write-Host "✅ ANÁLISE CONCLUÍDA! Relatórios gerados em: $absolutePathDir" -ForegroundColor Green
    Write-Host "=============================================================================`n" -ForegroundColor Green
    Write-Host "🚀 O relatório é totalmente local e NÃO REQUER UM SERVIDOR." -ForegroundColor Cyan
    Write-Host "   Para visualizar, abra o link abaixo no seu navegador:"
    
    # Gera um hyperlink clicável no terminal (funciona melhor no Windows Terminal e PS Core)
    $esc = [char]27
    $linkText = "🔗 Link para o relatório: "
    $hyperlink = "${esc}]8;;${fileUri}${esc}\${fileUri}${esc}]8;;${esc}\"
    Write-Host "$linkText$hyperlink"
    Write-Host "-----------------------------------------------------------------------------"
}

# =============================================================================
# --- Lógica Principal do Orquestrador ---
# =============================================================================
function Invoke-MainWorkflow {
    Test-Prerequisites
    Initialize-Environment

    Write-Host "`n---`n🔎 Procurando por arquivos de alerta (.csv) no diretório '$CsvDir'..." -ForegroundColor Cyan
    $inputFiles = Get-ChildItem -Path $CsvDir -Filter *.csv | ForEach-Object { $_.FullName }

    $fileCount = $inputFiles.Count
    Write-Host "✅ Encontrado(s) $($fileCount) arquivo(s) de dados." -ForegroundColor Green
    if ($fileCount -eq 0) {
        throw "❌ Erro: Nenhum arquivo .csv de entrada encontrado em '$CsvDir'. Abortando."
    }
    
    $finalReportDir = ""

    # --- Caso 1: Análise de arquivo único ---
    if ($fileCount -eq 1) {
        Write-Host "`n1️⃣  Apenas um arquivo encontrado. Executando análise simples." -ForegroundColor Cyan
        $fileAtual = $inputFiles[0]
        $filenameBase = [System.IO.Path]::GetFileNameWithoutExtension($fileAtual)
        $outputDir = Join-Path $PSScriptRoot "reports" "resultados-$filenameBase"
        $finalReportDir = $outputDir
        
        if (Test-Path -Path $outputDir) {
            $backupDir = "$($outputDir).bkp-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
            Write-Host "   -> Diretório de resultados existente encontrado. Fazendo backup para '$backupDir'..."
            Move-Item -Path $outputDir -Destination $backupDir
        }
        New-Item -Path $outputDir -ItemType Directory -Force | Out-Null

        Start-FullAnalysis -InputFile $fileAtual -OutputDir $outputDir -TrendReportArg ""
        
        $resumoFile = Join-Path $outputDir "resumo_geral.html"
        Write-Host "🔔 Adicionando nota sobre análise de tendência ao resumo..."
        $note = '<hr><p style="font-style: italic; color: #a0a0b0; text-align: center;">Nota: A análise de tendência será gerada na próxima execução quando um novo arquivo de dados estiver disponível para comparação.</p>'
        Add-Content -Path $resumoFile -Value $note
        
        Complete-Report -TargetDir $outputDir
    }

    # --- Caso 2: Análise comparativa com múltiplos arquivos ---
    if ($fileCount -ge 2) {
        Write-Host "`n2️⃣  Múltiplos arquivos encontrados. Iniciando análise de tendência..." -ForegroundColor Cyan
        
        $latestFiles = (& $PythonExec (Join-Path $SourceDir "selecionar_arquivos.py") $inputFiles)
        $fileAtual = $latestFiles[0]
        $fileAnterior = $latestFiles[1]
        Write-Host "   - Período Atual:    $fileAtual"
        Write-Host "   - Período Anterior: $fileAnterior"

        $dirAnterior = Join-Path $PSScriptRoot "reports" "resultados-temp-anterior"
        $dirAtual = Join-Path $PSScriptRoot "reports" "resultados-temp-atual"
        
        Remove-Item -Path $dirAnterior, $dirAtual -Recurse -Force -ErrorAction SilentlyContinue
        New-Item -Path $dirAnterior, $dirAtual -ItemType Directory -Force | Out-Null

        Start-SummaryOnlyAnalysis -InputFile $fileAnterior -OutputDir $dirAnterior
        Start-FullAnalysis -InputFile $fileAtual -OutputDir $dirAtual -TrendReportArg "--trend-report-path ../resumo_tendencia.html"

        Write-Host "`n🗓️   Coletando intervalos de datas dos arquivos..." -ForegroundColor Cyan
        $dateRangeAnterior = (& $PythonExec (Join-Path $SourceDir "get_date_range.py") $fileAnterior)
        $dateRangeAtual = (& $PythonExec (Join-Path $SourceDir "get_date_range.py") $fileAtual)
        Write-Host "   - Intervalo Anterior: $dateRangeAnterior"
        Write-Host "   - Intervalo Atual:    $dateRangeAtual"

        Write-Host "📊 Gerando relatório de tendência..." -ForegroundColor Cyan
        & $PythonExec (Join-Path $SourceDir "analise_tendencia.py") `
            (Join-Path $dirAnterior "resumo_problemas.json") `
            (Join-Path $dirAtual "resumo_problemas.json") `
            $fileAnterior $fileAtual $dateRangeAnterior $dateRangeAtual

        $filenameBaseAtual = [System.IO.Path]::GetFileNameWithoutExtension($fileAtual)
        $finalDir = Join-Path $PSScriptRoot "reports" "analise-comparativa-$filenameBaseAtual"
        $finalReportDir = $finalDir
        Write-Host "📂 Consolidando todos os artefatos em: $finalDir" -ForegroundColor Cyan
        
        if (Test-Path -Path $finalDir) {
            $backupDir = "$($finalDir).bkp-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
            Write-Host "   -> Diretório de análise existente encontrado. Fazendo backup para '$backupDir'..."
            Move-Item -Path $finalDir -Destination $backupDir
        }
        Move-Item -Path $dirAtual -Destination $finalDir
        Move-Item -Path (Join-Path $PSScriptRoot "resumo_tendencia.html") -Destination $finalDir
        
        $comparisonDataDir = Join-Path $finalDir "dados_comparacao"
        New-Item -Path $comparisonDataDir -ItemType Directory -Force | Out-Null
        Move-Item -Path (Join-Path $dirAnterior "resumo_problemas.json") -Destination (Join-Path $comparisonDataDir "resumo_problemas_anterior.json")
        
        Remove-Item -Path $dirAnterior -Recurse -Force

        Complete-Report -TargetDir $finalDir
    }
  
    # --- Passo Final de Limpeza ---
    $invalidLogFile = "invalid_self_healing_status.csv"
    if (Test-Path -Path $invalidLogFile) {
        if (-not [string]::IsNullOrEmpty($finalReportDir)) {
            Write-Host "   -> Movendo '$invalidLogFile' para '$finalReportDir'..."
            Move-Item -Path $invalidLogFile -Destination $finalReportDir
        }
    }
}

Invoke-MainWorkflow

# --- Limpeza Final ---
Write-Host "🧹 Limpando diretório __pycache__..." -ForegroundColor Cyan
Remove-Item -Path (Join-Path $PSScriptRoot "src/__pycache__") -Recurse -Force -ErrorAction SilentlyContinue
Write-Host "   -> ✅ Limpeza concluída." -ForegroundColor Green