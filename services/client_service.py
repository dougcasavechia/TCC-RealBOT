import pandas as pd
import time
from config import CLIENT_FILE_PATH
from logger import logger


CACHE_CLIENTES = None
CACHE_TIMESTAMP = 0
CACHE_TIMEOUT = 60  # Atualiza a cada 60 segundos

def carregar_informacoes_dos_clientes():
    global CACHE_CLIENTES, CACHE_TIMESTAMP
    if CACHE_CLIENTES is None or (time.time() - CACHE_TIMESTAMP > CACHE_TIMEOUT):
        try:
            df = pd.read_excel(CLIENT_FILE_PATH, dtype={'celular': str})
            df['celular'] = df['celular'].astype(str).str.strip()  # Conversão única
            CACHE_CLIENTES = df
            CACHE_TIMESTAMP = time.time()
            logger.info("Clientes carregados e armazenados em cache.")
        except FileNotFoundError:
            logger.error(f"Arquivo não encontrado: {CLIENT_FILE_PATH}")
            CACHE_CLIENTES = pd.DataFrame()
        except Exception as e:
            logger.exception(f"Erro ao carregar clientes: {e}")
            CACHE_CLIENTES = pd.DataFrame()
    return CACHE_CLIENTES


def buscar_cliente_por_telefone(contato):
    """
    Busca um cliente pelo número de telefone no cache.
    """
    logger.debug(f"🔍 Buscando cliente pelo telefone: {contato}")

    informacoes_dos_clientes = carregar_informacoes_dos_clientes()

    if informacoes_dos_clientes.empty:
        logger.warning("⚠️ Tentativa de busca em um banco de clientes vazio.")
        return None

    contato = str(contato).strip()  # Normaliza a entrada
    cliente = informacoes_dos_clientes.loc[informacoes_dos_clientes['celular'] == contato]

    if not cliente.empty:
        logger.info(f"✅ Cliente encontrado: {contato}")
        return cliente.iloc[0].to_dict()

    logger.warning(f"❌ Cliente não encontrado: {contato}")
    return None




