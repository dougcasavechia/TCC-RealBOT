import pandas as pd
from config import CLIENT_FILE_PATH

def load_informacoes_dos_clientes():
    """
    Carrega os dados dos clientes de um arquivo Excel.
    """
    try:
        df = pd.read_excel(CLIENT_FILE_PATH, dtype={'celular': str})
        return df
    except Exception as e:
        print(f"Erro ao carregar clientes: {e}")
        return pd.DataFrame()

def buscar_cliente_por_telefone(contato):
    """
    Verifica se o número está cadastrado no Excel e retorna os dados.
    """
    informacoes_dos_clientes = load_informacoes_dos_clientes()
    if informacoes_dos_clientes.empty:
        return None
    client = informacoes_dos_clientes.loc[informacoes_dos_clientes['celular'] == contato]
    if not client.empty:
        return client.iloc[0].to_dict()
    return None
