from collections import defaultdict
from logger import logger

class GlobalState:
    """Singleton para armazenar o estado global dos usuários."""
    
    _instance = None  

    def __new__(cls):
        if not cls._instance:
            cls._instance = super().__new__(cls)
            cls._instance._reset_state()
        return cls._instance

    def _reset_state(self):
        """Inicializa os dicionários de estado."""
        self.status_usuario = defaultdict(str)
        self.ultima_interacao_usuario = defaultdict(float)
        self.ultimo_menu_usuario = defaultdict(list)
        self.informacoes_cliente = defaultdict(dict)

    def limpar_dados_usuario(self, contato):
        """Remove os dados do usuário do estado global."""
        removido = False

        for attr in ["status_usuario", "ultima_interacao_usuario", "ultimo_menu_usuario", "informacoes_cliente"]:
            if contato in getattr(self, attr):
                del getattr(self, attr)[contato]
                removido = True

        if removido:
            logger.info(f"🗑️ Dados do usuário {contato} foram removidos do estado global.")
        else:
            logger.warning(f"⚠️ Tentativa de remover {contato}, mas ele não estava armazenado.")

# Instância única do estado global
global_state = GlobalState()
