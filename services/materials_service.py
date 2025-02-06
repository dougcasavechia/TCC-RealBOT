import pandas as pd
from config import MATERIAL_FILE_PATH
from logger import logger

def carregar_tabela_mp():
    """Carrega a tabela de matérias-primas do arquivo Excel."""
    try:
        df = pd.read_excel(MATERIAL_FILE_PATH, dtype={"id_materia_prima": str, "codigo_materia_prima": str})
        logger.info("📊 Tabela de matérias-primas carregada com sucesso.")
        return df
    except FileNotFoundError:
        logger.error(f"❌ Arquivo de matérias-primas não encontrado: {MATERIAL_FILE_PATH}")
    except Exception as e:
        logger.exception(f"❌ Erro ao carregar tabela de matérias-primas: {e}")
    
    return pd.DataFrame()  # Retorna DataFrame vazio se houver erro


def gerar_menu_materia_prima():
    """
    Gera o menu inicial com base na coluna 'cor_materia_prima' da tabela de matérias-primas.
    """
    df = carregar_tabela_mp()

    if df.empty:
        logger.warning("⚠️ A tabela de matérias-primas está vazia ou não foi carregada.")
        return []

    # Obter opções únicas de 'cor_materia_prima'
    opcoes_iniciais = df["cor_materia_prima"].dropna().unique().tolist()
    logger.info(f"📋 {len(opcoes_iniciais)} opções carregadas para o menu de matéria-prima.")
    
    return opcoes_iniciais


def filtrar_mp_por_escolhas(cor_materia_prima=None, espessura_materia_prima=None, beneficiamento=None):
    """
    Filtra as matérias-primas com base nas escolhas do usuário.
    """
    df = carregar_tabela_mp()

    if df.empty:
        logger.warning("⚠️ A tabela de matérias-primas está vazia ou não foi carregada.")
        return []

    # Filtrar dinamicamente com base nas escolhas
    if cor_materia_prima:
        df = df[df["cor_materia_prima"] == cor_materia_prima]
    if espessura_materia_prima:
        df = df[df["espessura_materia_prima"] == espessura_materia_prima]
    if beneficiamento:
        df = df[df["beneficiamento"] == beneficiamento]

    # Retornar registros filtrados como dicionários
    materias_primas = df.to_dict("records")
    logger.info(f"📌 {len(materias_primas)} matérias-primas filtradas para as definições fornecidas.")
    return materias_primas


def gerar_menu_por_definicao_mp(df, definicao_coluna):
    """
    Gera o menu baseado em uma coluna específica da tabela de matérias-primas.
    """
    if definicao_coluna not in df.columns or df[definicao_coluna].dropna().empty:
        logger.warning(f"⚠️ A coluna '{definicao_coluna}' está vazia ou não existe na tabela.")
        return []

    # Obter valores únicos, ignorando nulos
    opcoes = df[definicao_coluna].dropna().unique().tolist()
    logger.info(f"📋 {len(opcoes)} opções geradas para '{definicao_coluna}'.")
    return opcoes

