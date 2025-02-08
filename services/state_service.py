import time
from config import TIMEOUT_WARNING, TIMEOUT_FINAL
from services.message_service import enviar_mensagem, salvar_mensagem_em_arquivo
from services.global_state import global_state

def monitor_inactivity():
    """
    Monitora a inatividade dos usuários e envia avisos ou encerra a conversa após um tempo limite.
    """
    while True:
        horario_atual = time.time()

        for contato in list(global_state.ultima_interacao_usuario.keys()):
            ultima_interacao = global_state.ultima_interacao_usuario[contato]
            status = global_state.status_usuario.get(contato)

            # Se o usuário estiver inativo e ainda não recebeu um aviso
            if horario_atual - ultima_interacao > TIMEOUT_WARNING and status and not status.startswith("inativo_"):
                enviar_aviso_inatividade(contato, status)

            # Se o usuário continuar inativo após o aviso, encerra a conversa
            elif horario_atual - ultima_interacao > TIMEOUT_WARNING + TIMEOUT_FINAL:
                encerrar_conversa_por_inatividade(contato)

        time.sleep(5)

def atualizar_ultima_atividade(contato):
    """
    Atualiza o tempo da última atividade do usuário.
    """
    global_state.ultima_interacao_usuario[contato] = time.time()


def enviar_aviso_inatividade(contato, status):
    """
    Envia um aviso de inatividade ao usuário com base no estado atual correto.
    """
    nome_cliente = global_state.informacoes_cliente.get(contato, {}).get("nome_cliente", "Desconhecido")

    if status in ["aguardando_altura", "aguardando_largura", "aguardando_quantidade"]:
        # ✅ Se o usuário estava inserindo medidas, refazemos a pergunta correta
        if status == "aguardando_altura":
            enviar_mensagem(contato, "Você está inativo. Seu fluxo será encerrado em XXXX segundos se não interagir com o bot.")
            enviar_mensagem(contato, "Por favor, informe a altura em milímetros:")
        elif status == "aguardando_largura":
            enviar_mensagem(contato, "Você está inativo. Seu fluxo será encerrado em XXXX segundos se não interagir com o bot.")
            enviar_mensagem(contato, "Por favor, informe a largura em milímetros:")
        elif status == "aguardando_quantidade":
            enviar_mensagem(contato, "Você está inativo. Seu fluxo será encerrado em XXXX segundos se não interagir com o bot.")
            enviar_mensagem(contato, "Quantas unidades desse projeto você deseja?")
        
        salvar_mensagem_em_arquivo(contato, nome_cliente, f"Bot: Aviso de inatividade para {status}.")
    
    else:
        # ✅ Se o usuário estava em um menu dinâmico, reenviamos o último menu corretamente
        ultimo_menu = global_state.ultimo_menu_usuario.get(contato, [])
        if ultimo_menu:
            menu_formatado = "\n".join([f"{i + 1}. {opcao}" for i, opcao in enumerate(ultimo_menu)])
            enviar_mensagem(contato, "Você está inativo. Seu fluxo será encerrado em XXXX segundos se não interagir com o bot.")
            enviar_mensagem(contato, "Por favor, escolha uma das opções listadas abaixo:")
            enviar_mensagem(contato, menu_formatado)
            salvar_mensagem_em_arquivo(contato, nome_cliente, "Bot: Aviso de inatividade com menu enviado.")
        else:
            enviar_mensagem(contato, "Você está inativo, mas ainda não há opções disponíveis.")
            salvar_mensagem_em_arquivo(contato, nome_cliente, "Bot: Aviso de inatividade sem menu.")

    # ✅ Marcar o estado como "inativo_<status>" para que possamos retomá-lo corretamente depois
    if status and not status.startswith("inativo_"):
        global_state.status_usuario[contato] = f"inativo_{status}"


def encerrar_conversa_por_inatividade(contato):
    """
    Encerra a conversa do usuário se o tempo limite de inatividade for atingido.
    """
    if global_state.status_usuario.get(contato) != "conversa_encerrada":
        enviar_mensagem(contato, "Conversa encerrada por inatividade. Para reiniciar, envie qualquer mensagem.")
        nome_cliente = global_state.informacoes_cliente.get(contato, {}).get("nome_cliente", "Desconhecido")
        salvar_mensagem_em_arquivo(contato, nome_cliente, "Bot: Conversa encerrada por inatividade.")

    # Limpar os dados do usuário
    global_state.limpar_dados_usuario(contato)
