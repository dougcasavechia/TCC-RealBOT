# import pandas as pd
# import os
# from config import TABLE_FILE_PATH
# from logger import logger

# def carregar_tabela():
#     """Carrega a tabela de projetos do arquivo Excel."""
#     if not os.path.exists(TABLE_FILE_PATH):
#         logger.error(f"Arquivo de tabela não encontrado: {TABLE_FILE_PATH}")
#         return pd.DataFrame()  # Retorna DataFrame vazio se não encontrar o arquivo
#     try:
#         return pd.read_excel(TABLE_FILE_PATH)
#     except Exception as e:
#         logger.error(f"Erro ao carregar a tabela: {e}")
#         return pd.DataFrame()

# def filtrar_tabela(tabela, definicao_1=None, definicao_2=None, definicao_3=None):
#     """Filtra a tabela de projetos conforme as definições informadas."""
#     colunas_validas = {"definicao_1", "definicao_2", "definicao_3"}
#     colunas_presentes = set(tabela.columns)

#     for definicao, coluna in zip([definicao_1, definicao_2, definicao_3], colunas_validas):
#         if definicao and coluna in colunas_presentes:
#             tabela = tabela[tabela[coluna] == definicao]

#     return tabela


