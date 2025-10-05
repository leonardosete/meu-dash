import sys
import pandas as pd
from typing import List, Tuple, Optional

NOME_DA_COLUNA_DE_DATA = 'sys_created_on'

def get_max_date_from_file(filepath: str) -> Optional[pd.Timestamp]:
    """
    Extrai a data máxima de uma coluna específica em um arquivo CSV.

    Args:
        filepath (str): O caminho para o arquivo CSV a ser processado.

    Returns:
        Optional[pd.Timestamp]: A data máxima encontrada ou None em caso de erro.
    """
    try:
        df = pd.read_csv(filepath, sep=';', on_bad_lines='skip', engine='python', usecols=[NOME_DA_COLUNA_DE_DATA])
        
        if NOME_DA_COLUNA_DE_DATA not in df.columns:
            print(f"Aviso: Coluna '{NOME_DA_COLUNA_DE_DATA}' não encontrada em '{filepath}'.", file=sys.stderr)
            return None
        
        df[NOME_DA_COLUNA_DE_DATA] = pd.to_datetime(df[NOME_DA_COLUNA_DE_DATA], errors='coerce', format='mixed')
        df.dropna(subset=[NOME_DA_COLUNA_DE_DATA], inplace=True)

        if df.empty:
            print(f"Aviso: Nenhuma data válida encontrada em '{filepath}'.", file=sys.stderr)
            return None
            
        return df[NOME_DA_COLUNA_DE_DATA].max()
    except Exception as e:
        print(f"Erro ao processar o arquivo '{filepath}': {e}", file=sys.stderr)
        return None

def sort_files_by_date(filepaths: List[str]) -> Optional[Tuple[str, str]]:
    """
    Ordena uma lista de arquivos CSV com base na data mais recente contida neles.

    Args:
        filepaths (List[str]): Uma lista de caminhos para os arquivos CSV.

    Returns:
        Optional[Tuple[str, str]]: Uma tupla contendo (caminho_arquivo_atual, caminho_arquivo_anterior).
                                   Retorna None se não for possível processar pelo menos dois arquivos.
    """
    if len(filepaths) < 2:
        return None

    file_dates = []
    for f in filepaths:
        max_date = get_max_date_from_file(f)
        if max_date:
            file_dates.append((max_date, f))
    
    if len(file_dates) < 2:
        print("Erro: Não foi possível determinar as datas de pelo menos dois arquivos.", file=sys.stderr)
        return None

    file_dates.sort(key=lambda x: x[0], reverse=True)
    
    return (file_dates[0][1], file_dates[1][1]) # (atual, anterior)