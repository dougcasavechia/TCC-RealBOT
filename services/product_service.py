import pandas as pd
from config import PRODUCT_FILE_PATH

def carregar_tabela_tipo_produto():
    """
    Carrega os produtos disponíveis do arquivo Excel.
    """
    try:
        df = pd.read_excel(PRODUCT_FILE_PATH)
        return df["descricao_tipo_produto"].dropna().tolist()
    except Exception as e:
        print(f"Erro ao carregar produtos: {e}")
        return []
