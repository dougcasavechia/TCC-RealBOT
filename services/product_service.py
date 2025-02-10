import pandas as pd
from config import PROJECT_FILE_PATH
from logger import logger  # Importando o módulo de logs

def carregar_tabela_projetos():
    """
    Carrega a tabela de projetos do arquivo Excel.
    Retorna um DataFrame vazio caso haja erro.
    """
    try:
        df = pd.read_excel(PROJECT_FILE_PATH)
        if df.empty:
            logger.warning(f"⚠️ O arquivo de projetos está vazio: {PROJECT_FILE_PATH}")
        else:
            logger.info("📊 Tabela de projetos carregada com sucesso.")
        return df
    except FileNotFoundError:
        logger.error(f"❌ Arquivo de projetos não encontrado: {PROJECT_FILE_PATH}")
    except Exception as e:
        logger.exception(f"❌ Erro ao carregar tabela de projetos: {e}")
    
    return pd.DataFrame()  # Retorna um DataFrame vazio em caso de erro

def gerar_menu_inicial(medida_final):
    """
    Gera o menu inicial com base na coluna 'definicao_1' da tabela de projetos e na medida selecionada.
    """
    df = carregar_tabela_projetos()

    if df.empty or "definicao_1" not in df.columns:
        logger.warning("⚠️ A tabela de projetos está vazia ou não contém a coluna 'definicao_1'.")
        return []

    produtos_filtrados = df[df["medida_final"] == medida_final]

    if produtos_filtrados.empty:
        logger.info("⚠️ Nenhum produto encontrado para a medida selecionada.")
        return []

    opcoes_iniciais = produtos_filtrados["definicao_1"].dropna().unique().tolist()
    logger.info(f"📋 {len(opcoes_iniciais)} opções carregadas para o menu inicial (Medida Final: {medida_final}).")
    
    return opcoes_iniciais


def filtrar_projetos_por_escolhas(definicao_1=None, definicao_2=None, definicao_3=None, definicao_4=None, medida_final=None):
    """
    Filtra os projetos com base nas escolhas do usuário e no tipo de medida.
    Agora inclui a definição_4 na filtragem.
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
    if definicao_4:
        df = df[df["definicao_4"] == definicao_4]

    # Retornar registros filtrados como dicionários
    projetos = df.to_dict("records")
    logger.info(f"📌 {len(projetos)} projetos filtrados para as definições fornecidas.")
    return projetos


def gerar_menu_por_definicao(df, coluna, filtros):
    """
    Gera um menu com as opções únicas de uma determinada coluna (definição) do DataFrame de projetos,
    garantindo que apenas as opções dentro do escopo já filtrado sejam consideradas.
    """
    if coluna not in df.columns:
        logger.warning(f"⚠️ A coluna '{coluna}' não existe no DataFrame. Retornando lista vazia.")
        return []

    # ✅ Aplicar os filtros anteriores antes de buscar as opções
    for chave, valor in filtros.items():
        if valor is not None and chave in df.columns:
            df = df[df[chave] == valor]
            logger.info(f"🔎 Aplicado filtro '{chave}': {valor}. Linhas restantes: {df.shape[0]}")

    if df.empty:
        logger.warning(f"⚠️ Nenhum dado disponível após filtragem para '{coluna}'.")
        return []

    # ✅ Retornar apenas opções compatíveis com os filtros aplicados
    opcoes = df[coluna].dropna().unique().tolist()
    logger.info(f"✅ Opções disponíveis para '{coluna}': {opcoes}")

    return opcoes


def gerar_menu_por_definicao_mp(df, coluna):
    """
    Gera um menu com as opções únicas de uma determinada coluna (definição) do DataFrame de matéria-prima.
    Retorna uma lista com as opções disponíveis.
    """
    if coluna not in df.columns:
        logger.warning(f"⚠️ A coluna '{coluna}' não existe no DataFrame. Retornando lista vazia.")
        return []

    # Obter opções únicas da definição, removendo valores nulos e duplicados
    opcoes = df[coluna].dropna().unique().tolist()

    if not opcoes:
        logger.info(f"⚠️ Nenhuma opção válida encontrada para '{coluna}'.")
        return []

    return opcoes
