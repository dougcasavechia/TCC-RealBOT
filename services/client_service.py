import pandas as pd
import time
from config import CLIENT_FILE_PATH
from logger import logger

class ClienteCache:
    """Gerencia o cache de clientes para evitar carregamento desnecessário."""
    _cache = None
    _timestamp = 0
    _timeout = 60  # Atualiza a cada 60 segundos

    @classmethod
    def carregar_clientes(cls):
        """Carrega informações dos clientes, armazenando em cache."""
        if cls._cache is None or (time.time() - cls._timestamp > cls._timeout):
            try:
                df = pd.read_excel(CLIENT_FILE_PATH, dtype={'celular': str})
                df['celular'] = df['celular'].str.strip()
                cls._cache = df
                cls._timestamp = time.time()
                logger.info("📄 Clientes carregados e armazenados em cache.")
            except FileNotFoundError:
                logger.error(f"❌ Arquivo não encontrado: {CLIENT_FILE_PATH}")
                cls._cache = pd.DataFrame()
            except Exception as e:
                logger.exception(f"❌ Erro ao carregar clientes: {e}")
                cls._cache = pd.DataFrame()
        return cls._cache

    @classmethod
    def buscar_cliente_por_telefone(cls, contato):
        """Busca um cliente pelo número de telefone no cache."""
        logger.debug(f"🔍 Buscando cliente pelo telefone: {contato}")
        df_clientes = cls.carregar_clientes()

        if df_clientes.empty:
            logger.warning("⚠️ Tentativa de busca em um banco de clientes vazio.")
            return None  # Nenhum cliente encontrado

        # ✅ Mostrar colunas reais do arquivo
        logger.debug(f"🔍 Colunas disponíveis no DataFrame de clientes: {df_clientes.columns.tolist()}")

        contato = str(contato).strip()
        cliente = df_clientes.loc[df_clientes['celular'] == contato]

        if not cliente.empty:
            logger.info(f"✅ Cliente encontrado: {contato}")

            # ✅ Procurar a coluna correta do nome do cliente
            col_nome_cliente = None
            for col in df_clientes.columns:
                if col.strip().lower() in ["nome", "nome_cliente", "cliente", "nome_do_cliente"]:
                    col_nome_cliente = col
                    break

            if not col_nome_cliente:
                logger.error("❌ Erro: Nenhuma coluna correspondente a 'nome' encontrada no arquivo de clientes!")
                return None

            return {
                "id_cliente": cliente.iloc[0]["id_cliente"],  # Já corrigido antes
                "nome_cliente": cliente.iloc[0]["nome_cliente"],  # Usa a coluna correta do nome
                "telefone": contato
            }

        logger.warning(f"❌ Cliente não encontrado: {contato}")
        return None
