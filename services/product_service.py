import pandas as pd
from config import PRODUCT_FILE_PATH, PROJECT_FILE_PATH
from logger import logger  # Importando o módulo de logs

def carregar_tabela_tipo_produto():
    """
    Carrega os produtos disponíveis do arquivo Excel.
    """
    try:
        df = pd.read_excel(PRODUCT_FILE_PATH)
        produtos = df["descricao_tipo_produto"].dropna().tolist()
        logger.info(f"📦 {len(produtos)} tipos de produtos carregados com sucesso.")
        return produtos
    except FileNotFoundError:
        logger.error(f"❌ Arquivo de produtos não encontrado: {PRODUCT_FILE_PATH}")
    except Exception as e:
        logger.exception(f"❌ Erro ao carregar produtos: {e}")
    
    return []

def carregar_tabela_projetos():
    """
    Carrega a tabela de projetos do arquivo Excel.
    """
    try:
        df = pd.read_excel(PROJECT_FILE_PATH)
        logger.info("📊 Tabela de projetos carregada com sucesso.")
        return df
    except FileNotFoundError:
        logger.error(f"❌ Arquivo de projetos não encontrado: {PROJECT_FILE_PATH}")
    except Exception as e:
        logger.exception(f"❌ Erro ao carregar tabela de projetos: {e}")
    
    return pd.DataFrame()

def filtrar_projetos(id_tipo_produto, medida_final):
    """
    Filtra os projetos com base no ID do tipo de produto e na medida escolhida.
    """
    df = carregar_tabela_projetos()

    if df.empty:
        logger.warning("⚠️ A tabela de projetos está vazia ou não foi carregada.")
        return []

    # Filtrar projetos por id_tipo_produto e medida_final
    projetos_filtrados = df[
        (df["id_tipo_produto"] == id_tipo_produto) & (df["medida_final"] == medida_final)
    ]

    projetos = projetos_filtrados.to_dict("records")
    logger.info(f"📌 {len(projetos)} projetos filtrados para ID {id_tipo_produto} (Medida Final: {medida_final}).")
    
    return projetos




