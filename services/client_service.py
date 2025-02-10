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
    def carregar_clientes(cls, forcar_atualizacao=False):
        """Carrega informações dos clientes, armazenando em cache."""
        if cls._cache is None or (time.time() - cls._timestamp > cls._timeout) or forcar_atualizacao:
            try:
                df = pd.read_excel(CLIENT_FILE_PATH, dtype={'celular': str})
                df['celular'] = df['celular'].str.strip()
                
                # Garantir que colunas essenciais existam
                colunas_esperadas = ["id_cliente", "nome_cliente", "celular"]
                for coluna in colunas_esperadas:
                    if coluna not in df.columns:
                        logger.error(f"❌ Coluna obrigatória '{coluna}' não encontrada no arquivo {CLIENT_FILE_PATH}.")
                        return pd.DataFrame()

                cls._cache = df
                cls._timestamp = time.time()
                logger.info("📄 Clientes carregados e armazenados em cache.")
            except FileNotFoundError:
                logger.error(f"❌ Arquivo não encontrado: {CLIENT_FILE_PATH}")
                cls._cache = pd.DataFrame()
            except Exception as e:
                logger.exception(f"❌ Erro ao carregar clientes: {e}", exc_info=True)
                cls._cache = pd.DataFrame()
        return cls._cache

    @classmethod
    def buscar_cliente_por_telefone(cls, contato):
        """Busca um cliente pelo número de telefone no cache."""
        logger.debug(f"🔍 Buscando cliente pelo telefone: {contato}")
        df_clientes = cls.carregar_clientes()

        if df_clientes.empty:
            logger.warning("⚠️ Tentativa de busca em um banco de clientes vazio.")
            return None  

        contato = str(contato).strip()
        cliente = df_clientes.loc[df_clientes['celular'] == contato]

        if not cliente.empty:
            logger.info(f"✅ Cliente encontrado: {contato}")

            # Procurar a coluna correta do nome do cliente
            col_nome_cliente = next((col for col in df_clientes.columns 
                                     if col.strip().lower() in ["nome", "nome_cliente", "cliente", "nome_do_cliente"]), None)

            if not col_nome_cliente:
                logger.error("❌ Nenhuma coluna correspondente a 'nome' encontrada no arquivo de clientes!")
                return None

            return {
                "id_cliente": cliente.iloc[0]["id_cliente"],
                "nome_cliente": cliente.iloc[0][col_nome_cliente],  
                "telefone": contato
            }

        logger.warning(f"❌ Cliente não encontrado: {contato}")
        return None

    @classmethod
    def limpar_cache(cls):
        """Força a limpeza do cache."""
        cls._cache = None
        cls._timestamp = 0
        logger.info("🔄 Cache de clientes foi limpo.")

