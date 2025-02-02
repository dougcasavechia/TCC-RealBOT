import time
from services.message_service import enviar_mensagem, salvar_mensagem_em_arquivo
from config import TIMEOUT_WARNING, TIMEOUT_FINAL
from services.global_state import global_state  # Agora usamos a instância global

def monitor_inactivity():
    """
    Monitora a inatividade dos usuários e envia avisos ou encerra a conversa após um tempo limite.
    """
    while True:
        horario_atual = time.time()

        for contato in list(global_state.ultima_interacao_usuario.keys()):
            ultima_interacao = global_state.ultima_interacao_usuario[contato]
            status = global_state.status_usuario.get(contato)

            # Se o usuário estiver inativo, envia um aviso
            if horario_atual - ultima_interacao > TIMEOUT_WARNING and not (status and status.startswith("inativo_")):
                enviar_aviso_inatividade(contato, status)

            # Se o usuário continuar inativo, encerra a conversa
            elif horario_atual - ultima_interacao > TIMEOUT_WARNING + TIMEOUT_FINAL:
                encerrar_conversa_por_inatividade(contato)

        time.sleep(5)

def enviar_aviso_inatividade(contato, status):
    """
    Envia um aviso de inatividade ao usuário com base no estado atual.
    """
    nome_cliente = global_state.informacoes_cliente.get(contato, {}).get("nome_cliente", "Desconhecido")

    if status == "coletando_altura":
        tipo_medida = "final" if global_state.informacoes_cliente[contato].get("medida_final") else "vão"
        enviar_mensagem(contato, f"Você está inativo. Informe a medida da altura em milímetros (mm) ({tipo_medida}):")
    elif status == "coletando_largura":
        tipo_medida = "final" if global_state.informacoes_cliente[contato].get("medida_final") else "vão"
        altura = global_state.informacoes_cliente[contato].get("altura", "não registrada")
        enviar_mensagem(contato, f"Você está inativo. Altura registrada: {altura} mm. Informe a largura em milímetros (mm) ({tipo_medida}):")
    elif status == "coletando_quantidade":
        enviar_mensagem(contato, "Você está inativo. Quantas unidades você deseja para este projeto?")
    else:
        ultimo_menu = global_state.ultimo_menu_usuario.get(contato, "Ainda não há opções disponíveis.")
        enviar_mensagem(contato, "Você está inativo. Essa conversa será encerrada em breve se você não responder:")
        enviar_mensagem(contato, ultimo_menu)

    salvar_mensagem_em_arquivo(contato, nome_cliente, "Bot: Aviso de inatividade.")
    global_state.status_usuario[contato] = f"inativo_{status}"

def encerrar_conversa_por_inatividade(contato):
    """
    Encerra a conversa do usuário se o tempo limite de inatividade for atingido.
    """
    if global_state.status_usuario.get(contato) != "conversa_encerrada":
        enviar_mensagem(contato, "Conversa encerrada por inatividade. Para reiniciar, envie qualquer mensagem.")
        nome_cliente = global_state.informacoes_cliente.get(contato, {}).get("nome_cliente", "Desconhecido")
        salvar_mensagem_em_arquivo(contato, nome_cliente, "Bot: Conversa encerrada por inatividade.")
    
    global_state.limpar_dados_usuario(contato)


