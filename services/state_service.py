import time
from config import TIMEOUT_WARNING, TIMEOUT_FINAL
from services.message_service import enviar_mensagem, salvar_mensagem_em_arquivo
from services.global_state import global_state

def monitor_inactivity():
    """Monitora usuários inativos e envia avisos ou encerra conversas."""
    while True:
        try:
            horario_atual = time.time()

            for contato, ultima_interacao in list(global_state.ultima_interacao_usuario.items()):
                status = global_state.status_usuario.get(contato)

                if not status or status.startswith("inativo_"):
                    continue  # Ignorar usuários já marcados como inativos

                tempo_inativo = horario_atual - ultima_interacao

                if tempo_inativo > TIMEOUT_WARNING and not status.startswith("aviso_enviado"):
                    enviar_aviso_inatividade(contato, status)
                    global_state.status_usuario[contato] = f"aviso_enviado_{status}"

                if tempo_inativo > (TIMEOUT_WARNING + TIMEOUT_FINAL):
                    encerrar_conversa_por_inatividade(contato)

            time.sleep(5)  # Reduz carga no sistema
        except Exception as e:
            print(f"❌ Erro no monitoramento de inatividade: {e}")

def atualizar_ultima_atividade(contato):
    """
    Atualiza o tempo da última atividade do usuário.
    """
    global_state.ultima_interacao_usuario[contato] = time.time()


def enviar_aviso_inatividade(contato, status):
    """
    Envia um aviso de inatividade e repete a última pergunta correta.
    Agora evita menus errados.
    """
    nome_cliente = global_state.informacoes_cliente.get(contato, {}).get("nome_cliente", "Desconhecido")

    mensagens = {
        "aguardando_altura": "Informe a altura em milímetros:",
        "aguardando_largura": "Informe a largura em milímetros:",
        "aguardando_quantidade": "Quantas unidades desse projeto você deseja?",
        "confirmar_finalizacao": "Deseja confirmar o pedido?\n1️⃣ Sim, finalizar\n2️⃣ Não, cancelar",
    }

    if status in mensagens:
        enviar_mensagem(contato, f"⏳ {mensagens[status]} Escolha em breve, caso contrário seu fluxo será encerrado.")
        salvar_mensagem_em_arquivo(contato, nome_cliente, f"Bot: Aviso de inatividade para {status}.")
    else:
        # Se o usuário estava em um menu de seleção, repetir o menu correto
        ultimo_menu = global_state.ultimo_menu_usuario.get(contato, [])
        if ultimo_menu:
            menu_formatado = "\n".join([f"{i + 1}. {opcao}" for i, opcao in enumerate(ultimo_menu)])
            enviar_mensagem(contato, f"⏳ Escolha uma das opções do menu acima, caso contrário seu fluxo será encerrado.")
            enviar_mensagem(contato, menu_formatado)
            salvar_mensagem_em_arquivo(contato, nome_cliente, "Bot: Aviso de inatividade repetindo menu correto.")
        else:
            enviar_mensagem(contato, "⏳ Você está inativo. Seu fluxo será encerrado se não interagir em breve.")
            salvar_mensagem_em_arquivo(contato, nome_cliente, "Bot: Aviso de inatividade enviado, sem menu.")

    # Agora armazenamos o estado antes de definir como inativo
    if not status.startswith("inativo_"):
        global_state.status_usuario[contato] = f"inativo_{status}"


def encerrar_conversa_por_inatividade(contato):
    """
    Encerra a conversa do usuário se o tempo limite de inatividade for atingido.
    """
    if global_state.status_usuario.get(contato) != "conversa_encerrada":
        enviar_mensagem(contato, "❌ Conversa encerrada por inatividade. Para reiniciar, envie qualquer mensagem.")
        nome_cliente = global_state.informacoes_cliente.get(contato, {}).get("nome_cliente", "Desconhecido")
        salvar_mensagem_em_arquivo(contato, nome_cliente, "Bot: Conversa encerrada por inatividade.")

    # Limpar os dados do usuário
    global_state.limpar_dados_usuario(contato)
