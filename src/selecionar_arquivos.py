import sys
import pandas as pd
from datetime import datetime

# --- IMPORTANTE ---
# O nome da coluna foi CORRIGIDO para 'sys_created_on', que é o correto para seus arquivos.
NOME_DA_COLUNA_DE_DATA = 'sys_created_on' 

def get_max_date_from_file(filepath):
    """
    Lê um arquivo CSV e retorna a data máxima encontrada.
    Retorna None se o arquivo não puder ser lido ou a coluna de data não for encontrada.
    """
    try:
        # Tenta ler o CSV com separador ponto e vírgula, comum no Brasil
        df = pd.read_csv(filepath, sep=';', on_bad_lines='skip', engine='python')
        
        if NOME_DA_COLUNA_DE_DATA not in df.columns:
            # Envia o aviso para o erro padrão para não poluir a saída principal
            print(f"Aviso: Coluna '{NOME_DA_COLUNA_DE_DATA}' não encontrada em '{filepath}'. Ignorando arquivo.", file=sys.stderr)
            return None
        
        # Converte a coluna para datetime, tratando múltiplos formatos e possíveis erros
        df[NOME_DA_COLUNA_DE_DATA] = pd.to_datetime(df[NOME_DA_COLUNA_DE_DATA], errors='coerce', format='mixed')
        
        # Remove valores NaT (Not a Time) que resultaram de erros de conversão
        df.dropna(subset=[NOME_DA_COLUNA_DE_DATA], inplace=True)

        if df.empty:
            print(f"Aviso: Nenhuma data válida encontrada em '{filepath}'.", file=sys.stderr)
            return None
            
        return df[NOME_DA_COLUNA_DE_DATA].max()
    except Exception as e:
        print(f"Erro ao processar o arquivo '{filepath}': {e}", file=sys.stderr)
        return None

def main():
    """
    Função principal que processa os arquivos passados como argumentos,
    os ordena pela data interna e imprime os dois mais recentes.
    """
    files = sys.argv[1:]
    if len(files) < 2:
        return

    file_dates = []
    for f in files:
        max_date = get_max_date_from_file(f)
        if max_date:
            file_dates.append((max_date, f))
    
    if len(file_dates) < 2:
        print("Erro: Não foi possível determinar as datas de pelo menos dois arquivos CSV válidos para comparação.", file=sys.stderr)
        sys.exit(1)

    # Ordena a lista de tuplas pela data (primeiro elemento), em ordem decrescente
    file_dates.sort(key=lambda x: x[0], reverse=True)
    
    # Imprime o nome do arquivo mais recente (o atual)
    print(file_dates[0][1])
    # Imprime o nome do segundo arquivo mais recente (o anterior)
    print(file_dates[1][1])

if __name__ == "__main__":
    main()

