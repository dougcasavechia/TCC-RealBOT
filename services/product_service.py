import pandas as pd
from config import PROJECT_FILE_PATH
from logger import logger  # Importando o módulo de logs

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

def gerar_menu_inicial(medida_final):
    """
    Gera o menu inicial com base na coluna 'definicao_1' da tabela de projetos e na medida selecionada.
    """
    df = carregar_tabela_projetos()

    if df.empty:
        logger.warning("⚠️ A tabela de projetos está vazia ou não foi carregada.")
        return []

    # Filtrar os produtos com base na medida_final
    produtos_filtrados = df[df["medida_final"] == medida_final]

    # Obter opções únicas de definicao_1
    opcoes_iniciais = produtos_filtrados["definicao_1"].dropna().unique().tolist()
    logger.info(f"📋 {len(opcoes_iniciais)} opções carregadas para o menu inicial (Medida Final: {medida_final}).")
    
    return opcoes_iniciais


def filtrar_projetos_por_escolhas(definicao_1=None, definicao_2=None, definicao_3=None, medida_final=None):
    """
    Filtra os projetos com base nas escolhas do usuário e no tipo de medida.
    """
    df = carregar_tabela_projetos()

    if df.empty:
        logger.warning("⚠️ A tabela de projetos está vazia ou não foi carregada.")
        return []

    # Filtrar dinamicamente com base nas escolhas e na medida
    if medida_final is not None:
        df = df[df["medida_final"] == medida_final]
    if definicao_1:
        df = df[df["definicao_1"] == definicao_1]
    if definicao_2:
        df = df[df["definicao_2"] == definicao_2]
    if definicao_3:
        df = df[df["definicao_3"] == definicao_3]

    # Retornar registros filtrados como dicionários
    projetos = df.to_dict("records")
    logger.info(f"📌 {len(projetos)} projetos filtrados para as definições fornecidas.")
    return projetos


def gerar_menu_por_definicao(df, definicao_coluna):
    """
    Gera o menu baseado em uma coluna específica da tabela filtrada.
    Ignora definições completamente vazias.
    """
    if definicao_coluna not in df.columns or df[definicao_coluna].dropna().empty:
        logger.warning(f"⚠️ A coluna '{definicao_coluna}' está vazia ou não existe na tabela.")
        return []

    # Obter opções únicas, ignorando valores nulos
    opcoes = df[definicao_coluna].dropna().unique().tolist()
    logger.info(f"📋 {len(opcoes)} opções geradas para '{definicao_coluna}'.")
    return opcoes

