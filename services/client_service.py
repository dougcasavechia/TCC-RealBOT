import pandas as pd
from config import CLIENT_FILE_PATH
from logger import logger  # Importando nosso logger


def carregar_informacoes_dos_clientes():
    """
    Carrega os dados dos clientes de um arquivo Excel.
    """
    try:
        df = pd.read_excel(CLIENT_FILE_PATH, dtype={'celular': str})
        logger.info("Clientes carregados com sucesso.")
        return df
    except FileNotFoundError:
        logger.error(f"Arquivo não encontrado: {CLIENT_FILE_PATH}")
    except Exception as e:
        logger.exception(f"Erro ao carregar clientes: {e}")
    
    return pd.DataFrame()  # Retorna um DataFrame vazio se houver erro


# Apenas mantenha a função carregada no mesmo arquivo
def buscar_cliente_por_telefone(contato):
    """
    Busca um cliente pelo número de telefone no Excel.
    """

    logger.debug(f"🔍 Buscando cliente pelo telefone: {contato}")

    informacoes_dos_clientes = carregar_informacoes_dos_clientes()  # Agora funciona corretamente

    if informacoes_dos_clientes.empty:
        logger.warning("⚠️ Tentativa de busca em um banco de clientes vazio.")
        return None

    informacoes_dos_clientes['celular'] = informacoes_dos_clientes['celular'].astype(str).str.strip()
    contato = str(contato).strip()  

    cliente = informacoes_dos_clientes.loc[informacoes_dos_clientes['celular'] == contato]

    if not cliente.empty:
        logger.info(f"✅ Cliente encontrado: {contato}")
        return cliente.iloc[0].to_dict()

    logger.warning(f"❌ Cliente não encontrado: {contato}")
    return None



