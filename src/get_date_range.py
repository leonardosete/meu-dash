import pandas as pd
import sys
from typing import Optional, Tuple
from datetime import datetime

def get_date_range_from_file(filepath: str) -> Optional[Tuple[str, datetime]]:
    """
    Extrai o intervalo de datas de um arquivo CSV e o retorna como uma string e objeto.

    Args:
        filepath (str): O caminho para o arquivo CSV.

    Returns:
        Optional[Tuple[str, datetime]]: Uma tupla contendo a string formatada 
        'DD/MM/YYYY a DD/MM/YYYY' e o objeto datetime da data máxima, ou None.
    """
    try:
        df = pd.read_csv(filepath, usecols=['sys_created_on'], encoding="utf-8-sig", sep=None, engine='python')
        datetimes = pd.to_datetime(df['sys_created_on'], errors='coerce', format='mixed')
        valid_dates = datetimes.dropna()
        
        if valid_dates.empty:
            return None
        else:
            min_date = valid_dates.min()
            max_date = valid_dates.max()
            return (f"{min_date.strftime('%d/%m/%Y')} a {max_date.strftime('%d/%m/%Y')}", max_date)
            
    except (FileNotFoundError, ValueError, KeyError) as e:
        print(f"⚠️  Aviso: Não foi possível ler as datas do arquivo '{filepath}'. Erro: {e}", file=sys.stderr)
        return None

def main_cli():
    """Função para manter a compatibilidade com a execução via linha de comando."""
    if len(sys.argv) != 2:
        print("Uso: python get_date_range.py <caminho_para_o_csv>", file=sys.stderr)
        sys.exit(1)
    
    result = get_date_range_from_file(sys.argv[1])
    if result:
        date_range_str, _ = result
        print(date_range_str)
    else:
        print("N/A", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main_cli()
