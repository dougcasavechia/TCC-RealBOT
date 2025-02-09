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
        self.status_usuario = {}
        self.ultima_interacao_usuario = {}
        self.ultimo_menu_usuario = {}
        self.informacoes_cliente = {}

    def limpar_dados_usuario(self, contato):
        """Remove os dados do usuário do estado global."""
        for attr in ["status_usuario", "ultima_interacao_usuario", "ultimo_menu_usuario", "informacoes_cliente"]:
            getattr(self, attr).pop(contato, None)

global_state = GlobalState()
