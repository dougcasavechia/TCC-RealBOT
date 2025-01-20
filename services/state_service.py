import time
from services.message_service import enviar_mensagem, salvar_mensagem_em_arquivo
from config import TIMEOUT_WARNING, TIMEOUT_FINAL
from services.global_state import status_usuario, ultima_interacao_usuario, ultimo_menu_usuario, informacoes_cliente

def monitor_inactivity():
    """
    Monitora inatividade dos usuários e envia aviso/encerra conversa.
    """
    while True:
        horario_atual = time.time()

        for contato in list(ultima_interacao_usuario.keys()):
            ultima_interacao = ultima_interacao_usuario[contato]
            status = status_usuario.get(contato)

            # Envia aviso de inatividade se o tempo exceder o limite e ainda não tiver marcado como inativo
            if horario_atual - ultima_interacao > TIMEOUT_WARNING and not (status and status.startswith("inativo_")):
                print(f"[Monitor] Enviando aviso de inatividade para {contato}")
                enviar_mensagem(contato, "Você está inativo. Essa conversa será encerrada em breve se você não optar por uma das opções abaixo:")
                ultimo_menu = ultimo_menu_usuario.get(contato, "Ainda não há opções disponíveis.")
                enviar_mensagem(contato, ultimo_menu)
                salvar_mensagem_em_arquivo(contato, informacoes_cliente.get(contato, {}).get("nome_cliente", "Desconhecido"), "Bot: Aviso de inatividade.")
                status_usuario[contato] = f"inativo_{status}"  # Marca o estado atual como inativo

            # Encerra a conversa se o tempo total de inatividade for excedido
            elif horario_atual - ultima_interacao > TIMEOUT_WARNING + TIMEOUT_FINAL:
                if status != "conversa_encerrada":
                    print(f"[Monitor] Encerrando conversa com {contato} por inatividade.")
                    enviar_mensagem(contato, "Conversa encerrada por inatividade. Para reiniciar, envie qualquer mensagem.")
                    salvar_mensagem_em_arquivo(contato, informacoes_cliente.get(contato, {}).get("nome_cliente", "Desconhecido"), "Bot: Conversa encerrada por inatividade.")
                limpar_dados_usuario(contato)

        time.sleep(5)


def limpar_dados_usuario(contato):
    """
    Remove os dados do usuário dos dicionários globais.
    """
    status_usuario.pop(contato, None)
    ultima_interacao_usuario.pop(contato, None)
    ultimo_menu_usuario.pop(contato, None)

