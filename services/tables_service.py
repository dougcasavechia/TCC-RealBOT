import pandas as pd

# Função para carregar a tabela
def carregar_tabela():
    return pd.read_excel("nova_tabela.xlsx")

# Função para filtrar a tabela com base nas definições
def filtrar_tabela(tabela, definicao_1=None, definicao_2=None, definicao_3=None):
    if definicao_1:
        tabela = tabela[tabela["definicao_1"] == definicao_1]
    if definicao_2:
        tabela = tabela[tabela["definicao_2"] == definicao_2]
    if definicao_3:
        tabela = tabela[tabela["definicao_3"] == definicao_3]
    return tabela

