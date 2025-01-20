from services.client_service import buscar_cliente_por_telefone
from services.message_service import enviar_mensagem, salvar_mensagem_em_arquivo
from services.product_service import carregar_tabela_tipo_produto
from services.global_state import status_usuario, ultima_interacao_usuario, ultimo_menu_usuario, informacoes_cliente
import time


def gerenciar_mensagem_recebida(contato, texto):
    """
    Processa mensagens recebidas e decide o fluxo com base no número e estado do usuário.
    """
    print(f"[DEBUG] Mensagem recebida - contato: {contato}, text: {texto}")

    # Atualizar o timestamp da última interação do usuário
    ultima_interacao_usuario[contato] = time.time()


    # Verificar se o número está cadastrado no dicionário de clientes
    if contato not in informacoes_cliente:
        informacoes_dos_clientes = buscar_cliente_por_telefone(contato)
        if not informacoes_dos_clientes:
            # Cliente não cadastrado
            enviar_mensagem(contato, "Seu número não está cadastrado. Solicite cadastro com um vendedor.")
            salvar_mensagem_em_arquivo(contato, "Desconhecido", "Bot: Número não cadastrado.")
            limpar_dados_usuario(contato)
            return
        informacoes_cliente[contato] = informacoes_dos_clientes

    # Obter informações do cliente
    nome_cliente = informacoes_cliente[contato].get("nome_cliente", "Desconhecido")

    # Obter estado atual do usuário
    status = status_usuario.get(contato)

    # Retomar fluxo após inatividade
    if status and status.startswith("inativo_"):
        print(f"[DEBUG] Retomando estado anterior para {contato}.")
        status_usuario[contato] = status.replace("inativo_", "")  # Restaura o estado anterior
        status = status_usuario[contato]  # Atualiza a variável 'status' com o estado restaurado

    # Fluxo para nova conversa ou estado inicial
    if status is None or status == "conversa_encerrada":
        print(f"[DEBUG] Novo estado inicial para {contato}.")
        iniciar_conversa(contato, nome_cliente)
        return

    # Fluxo principal de interação
    if status == "aguardando_decisao_inicial":
        processar_decisao_usuario(contato, texto, nome_cliente)
    elif status == "escolhendo_medida_vao_ou_final":
        processar_medida_vao_final(contato, texto, nome_cliente)
    elif status == "escolhendo_tipo_produto":
        processar_selecao_produto(contato, texto, nome_cliente)
    else:
        # Estado desconhecido ou não tratado
        print(f"[WARNING] Estado desconhecido para {contato}: {status}")
        enviar_mensagem(contato, "Desculpe, ocorreu um problema. Vamos reiniciar sua interação.")
        iniciar_conversa(contato, nome_cliente)


def iniciar_conversa(contato, nome_cliente):
    """
    Inicia a conversa com o usuário, definindo o estado inicial.
    """
    print(f"[DEBUG] Iniciando conversa com {contato}.")
    menu = "1. Realizar orçamento\n2. Conferir orçamento"
    enviar_mensagem(contato, f"Olá, {nome_cliente}! Como posso ajudar hoje?")
    enviar_mensagem(contato, menu)
    status_usuario[contato] = "aguardando_decisao_inicial"
    ultimo_menu_usuario[contato] = menu
    salvar_mensagem_em_arquivo(contato, nome_cliente, "Bot: Apresentou opções iniciais.")


def processar_decisao_usuario(contato, texto, nome_cliente):
    """
    Processa a decisão inicial do usuário.
    """
    if texto == "1":  # Realizar orçamento
        enviar_mensagem(contato, "Você deseja informar:")
        menu = "1. Medida final\n2. Medida de vão"
        enviar_mensagem(contato, menu)
        status_usuario[contato] = "escolhendo_medida_vao_ou_final"
        ultimo_menu_usuario[contato] = menu
        salvar_mensagem_em_arquivo(contato, nome_cliente, "Bot: Perguntou sobre tipo de medida.")
    elif texto == "2":  # Conferir orçamento
        enviar_mensagem(contato, "Opção ainda não implementada. Tente novamente mais tarde.")
        salvar_mensagem_em_arquivo(contato, nome_cliente, "Bot: Opção 'Conferir orçamento' não implementada.")
        finalizar_conversa(contato, nome_cliente)
    else:
        repetir_menu(contato, nome_cliente)


def processar_medida_vao_final(contato, text, nome_cliente):
    """
    Processa a escolha entre medida final ou medida de vão.
    """
    if text == "1":  # Medida Final
        enviar_mensagem(contato, "Você escolheu informar a medida final.")
        salvar_mensagem_em_arquivo(contato, nome_cliente, "Bot: Usuário escolheu medida final.")
        apresentar_menu_produtos(contato, nome_cliente)
    elif text == "2":  # Medida de Vão
        enviar_mensagem(contato, "Você escolheu informar a medida de vão.")
        salvar_mensagem_em_arquivo(contato, nome_cliente, "Bot: Usuário escolheu medida de vão.")
        apresentar_menu_produtos(contato, nome_cliente)
    else:
        repetir_menu(contato, nome_cliente)


def processar_selecao_produto(contato, text, nome_cliente):
    """
    Processa a seleção de produtos pelo usuário.
    """
    products = carregar_tabela_tipo_produto()
    try:
        choice = int(text) - 1
        if 0 <= choice < len(products):
            selected_product = products[choice]
            enviar_mensagem(contato, f"Você escolheu o produto: {selected_product}. Estamos processando sua solicitação.")
            salvar_mensagem_em_arquivo(contato, nome_cliente, f"Bot: Produto escolhido: {selected_product}.")
            finalizar_conversa(contato, nome_cliente)
        else:
            raise ValueError("Opção inválida.")
    except (ValueError, IndexError):
        repetir_menu(contato, nome_cliente)


def apresentar_menu_produtos(contato, nome_cliente):
    """
    Apresenta o menu de produtos após a escolha de medida.
    """
    products = carregar_tabela_tipo_produto()
    if products:
        menu = "\n".join([f"{i + 1}. {prod}" for i, prod in enumerate(products)])
        enviar_mensagem(contato, "Escolha o tipo de produto:")
        enviar_mensagem(contato, menu)
        status_usuario[contato] = "escolhendo_tipo_produto"
        ultimo_menu_usuario[contato] = menu
        salvar_mensagem_em_arquivo(contato, nome_cliente, "Bot: Apresentou menu de produtos.")
    else:
        enviar_mensagem(contato, "Não há produtos disponíveis no momento. Tente novamente mais tarde.")
        salvar_mensagem_em_arquivo(contato, nome_cliente, "Bot: Nenhum produto disponível.")
        finalizar_conversa(contato, nome_cliente)


def repetir_menu(contato, nome_cliente):
    """
    Reenvia o último menu exibido ao usuário com base no estado atual.
    """
    ultimo_menu = ultimo_menu_usuario.get(contato)
    if ultimo_menu:
        enviar_mensagem(contato, "Desculpe, não entendi. Escolha uma das opções:")
        enviar_mensagem(contato, ultimo_menu)
        salvar_mensagem_em_arquivo(contato, nome_cliente, "Bot: Repetiu o menu apropriado.")
    else:
        # Caso o menu não esteja salvo, envia o menu inicial como fallback
        iniciar_conversa(contato, nome_cliente)


def finalizar_conversa(contato, nome_cliente):
    """
    Finaliza a conversa com o usuário e limpa os dados.
    """
    enviar_mensagem(contato, "Obrigado! Qualquer coisa, é só chamar a gente novamente!")
    salvar_mensagem_em_arquivo(contato, nome_cliente, "Bot: Conversa encerrada.")
    limpar_dados_usuario(contato)


def limpar_dados_usuario(contato):
    """
    Remove os dados do usuário dos dicionários globais.
    """
    status_usuario.pop(contato, None)
    ultima_interacao_usuario.pop(contato, None)
    ultimo_menu_usuario.pop(contato, None)
