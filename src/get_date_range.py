
import pandas as pd
import sys

def get_date_range(filepath: str):
    """Extrai e exibe o intervalo de datas de um arquivo CSV.

    Lê um arquivo CSV especificado, extrai as datas da coluna 'sys_created_on',
    e identifica as datas mais antiga e mais recente. O intervalo de datas
    resultante é impresso no formato 'DD/MM/YYYY a DD/MM/YYYY'.

    Args:
        filepath (str): O caminho para o arquivo CSV a ser processado.
            O arquivo deve conter uma coluna chamada 'sys_created_on'.

    Raises:
        SystemExit: Sai com o código 1 em caso de erro de arquivo não encontrado,
            erro de valor na conversão de data, ou se a coluna 'sys_created_on'
            não for encontrada. Uma mensagem de erro "N/A" é impressa no stderr.

    Side Effects:
        - Imprime o intervalo de datas formatado para stdout se as datas forem encontradas.
        - Imprime "N/A" para stdout se não houver datas válidas na coluna.
        - Imprime "N/A" para stderr em caso de erro na leitura ou processamento do arquivo.
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
