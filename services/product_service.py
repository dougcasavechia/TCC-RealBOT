import pandas as pd
from config import PRODUCT_FILE_PATH, PROJECT_FILE_PATH

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


def carregar_tabela_projetos():
    """
    Carrega a tabela de projetos do arquivo Excel.
    """
    try:
        file_path = "input/projetos.xlsx"  # Caminho do arquivo
        df = pd.read_excel(PROJECT_FILE_PATH)
        return df
    except Exception as e:
        print(f"[ERROR] Erro ao carregar tabela de projetos: {e}")
        return pd.DataFrame()
    
def filtrar_projetos(id_tipo_produto, medida_final):
    """
    Filtra os projetos com base no id_tipo_produto e na medida_final.

    :param id_tipo_produto: ID do tipo de produto selecionado
    :param medida_final: Booleano (0 para medida de vão, 1 para medida final)
    :return: Lista de projetos filtrados
    """
    df = carregar_tabela_projetos()

    if df.empty:
        print("[WARNING] A tabela de projetos está vazia ou não foi carregada.")
        return []

    # Filtrar projetos por id_tipo_produto e medida_final
    projetos_filtrados = df[
        (df["id_tipo_produto"] == id_tipo_produto) &
        (df["medida_final"] == medida_final)
    ]

    # Retornar apenas as descrições de projeto
    return projetos_filtrados["descricao_projeto"].tolist()

