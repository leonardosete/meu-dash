
import pandas as pd
import sys

def get_date_range(filepath: str):
    """
    Lê um arquivo CSV, encontra a data mais antiga e a mais recente na coluna 'sys_created_on'
    e imprime o intervalo formatado (DD/MM/YYYY a DD/MM/YYYY).
    """
    try:
        df = pd.read_csv(filepath, usecols=['sys_created_on'], encoding="utf-8-sig", sep=None, engine='python')
        datetimes = pd.to_datetime(df['sys_created_on'], errors='coerce', format='mixed')
        valid_dates = datetimes.dropna()
        
        if valid_dates.empty:
            print("N/A")
        else:
            min_date = valid_dates.min()
            max_date = valid_dates.max()
            print(f"{min_date.strftime('%d/%m/%Y')} a {max_date.strftime('%d/%m/%Y')}")
            
    except (FileNotFoundError, ValueError, KeyError) as e:
        print("N/A", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Uso: python get_date_range.py <caminho_para_o_csv>", file=sys.stderr)
        sys.exit(1)
    get_date_range(sys.argv[1])
