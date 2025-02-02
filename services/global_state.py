class GlobalState:
    """
    Classe Singleton para armazenar o estado global dos usuários.
    """

    _instance = None  # Variável privada para armazenar a única instância da classe

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(GlobalState, cls).__new__(cls)
            cls._instance.status_usuario = {}           # Armazena o estado atual de cada usuário
            cls._instance.ultima_interacao_usuario = {} # Timestamp da última interação
            cls._instance.ultimo_menu_usuario = {}      # Último menu enviado ao usuário
            cls._instance.informacoes_cliente = {}      # Informações dos clientes cadastrados
        return cls._instance

    def limpar_dados_usuario(self, contato):
        """
        Remove os dados do usuário do estado global.
        """
        self.status_usuario.pop(contato, None)
        self.ultima_interacao_usuario.pop(contato, None)
        self.ultimo_menu_usuario.pop(contato, None)
        self.informacoes_cliente.pop(contato, None)

# Criar uma instância global para ser usada em toda a aplicação
global_state = GlobalState()
