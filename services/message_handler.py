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
    elif status == "escolhendo_projeto":
        processar_selecao_projeto(contato, texto, nome_cliente)
    elif status == "coletando_altura":
        processar_altura(contato, texto, nome_cliente)  # Adiciona processamento de altura
    elif status == "coletando_largura":
        processar_largura(contato, texto, nome_cliente)  # Adiciona processamento de largura
    else:
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


def processar_selecao_produto(contato, texto, nome_cliente):
    """
    Processa a seleção de produtos pelo usuário.
    """
    produtos = carregar_tabela_tipo_produto()  # Certifique-se de carregar a tabela de tipos de produto
    try:
        escolha = int(texto) - 1
        if 0 <= escolha < len(produtos):
            produto_selecionado = produtos[escolha]
            id_tipo_produto = escolha + 1  # Assumindo que o índice corresponde ao ID
            enviar_mensagem(contato, f"Você escolheu o tipo de produto: {produto_selecionado}.")
            salvar_mensagem_em_arquivo(contato, nome_cliente, f"Bot: Tipo de produto escolhido: {produto_selecionado}.")
            
            # Verificar se o cliente escolheu medida final ou medida de vão
            medida_final = 1 if status_usuario.get(contato) == "escolhendo_medida_vao_ou_final" else 0

            # Chamar o menu de projetos
            apresentar_menu_projetos(contato, nome_cliente, id_tipo_produto, medida_final)
        else:
            raise ValueError("Opção inválida.")
    except (ValueError, IndexError):
        repetir_menu(contato, nome_cliente)

def processar_selecao_projeto(contato, texto, nome_cliente):
    """
    Processa a seleção de projetos pelo usuário.
    """
    ultimo_menu = ultimo_menu_usuario.get(contato)

    if not ultimo_menu:
        enviar_mensagem(contato, "Não conseguimos recuperar as opções anteriores. Reiniciaremos sua interação.")
        iniciar_conversa(contato, nome_cliente)
        return

    opcoes = ultimo_menu.split("\n")

    try:
        escolha = int(texto) - 1
        if 0 <= escolha < len(opcoes):
            projeto_selecionado = opcoes[escolha]
            enviar_mensagem(contato, f"Você escolheu o projeto: {projeto_selecionado}.")
            salvar_mensagem_em_arquivo(contato, nome_cliente, f"Bot: Projeto escolhido: {projeto_selecionado}.")

            # Solicitar altura como próximo passo
            tipo_medida = "final" if informacoes_cliente[contato].get("medida_final") else "vão"
            solicitar_altura(contato, nome_cliente, tipo_medida)
        else:
            raise ValueError("Opção inválida.")
    except (ValueError, IndexError):
        enviar_mensagem(contato, "Desculpe, opção inválida. Escolha uma das opções abaixo:")
        enviar_mensagem(contato, ultimo_menu)
        salvar_mensagem_em_arquivo(contato, nome_cliente, "Bot: Solicitou nova escolha de projeto.")



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


def apresentar_menu_projetos(contato, nome_cliente, id_tipo_produto, medida_final):
    """
    Apresenta o menu de projetos com base no tipo de produto e na medida selecionada.

    :param contato: Contato do cliente
    :param nome_cliente: Nome do cliente
    :param id_tipo_produto: ID do tipo de produto escolhido
    :param medida_final: Booleano (0 para medida de vão, 1 para medida final)
    """
    from services.product_service import filtrar_projetos  # Certifique-se de importar a função aqui

    projetos = filtrar_projetos(id_tipo_produto, medida_final)

    if projetos:
        menu = "\n".join([f"{i + 1}. {projeto}" for i, projeto in enumerate(projetos)])
        enviar_mensagem(contato, "Escolha o projeto desejado:")
        enviar_mensagem(contato, menu)
        status_usuario[contato] = "escolhendo_projeto"
        ultimo_menu_usuario[contato] = menu
        salvar_mensagem_em_arquivo(contato, nome_cliente, "Bot: Apresentou menu de projetos.")
    else:
        enviar_mensagem(contato, "Não há projetos disponíveis para sua escolha. Tente novamente mais tarde.")
        salvar_mensagem_em_arquivo(contato, nome_cliente, "Bot: Nenhum projeto disponível.")
        finalizar_conversa(contato, nome_cliente)


def repetir_menu(contato, nome_cliente):
    """
    Reenvia a solicitação ou o menu apropriado com base no estado atual do usuário.
    """
    status = status_usuario.get(contato)
    print("####################################")
    print(f"################## O status está em {status} ##################")
    print("####################################")

    if status == "coletando_altura":
        tipo_medida = "final" if informacoes_cliente[contato].get("medida_final") else "vão"
        enviar_mensagem(contato, f"Você está inativo. Por favor, informe a medida da altura em milímetros (mm) ({tipo_medida}):")
        salvar_mensagem_em_arquivo(contato, nome_cliente, "Bot: Repetiu solicitação de altura.")
    elif status == "coletando_largura":
        tipo_medida = "final" if informacoes_cliente[contato].get("medida_final") else "vão"
        altura = informacoes_cliente[contato].get("altura", "não registrada")
        enviar_mensagem(contato, f"Você está inativo. Altura registrada: {altura} mm. Informe a medida da largura em milímetros (mm) ({tipo_medida}):")
        salvar_mensagem_em_arquivo(contato, nome_cliente, "Bot: Repetiu solicitação de largura.")
    else:
        # Caso o estado não seja altura ou largura, reenvia o último menu
        ultimo_menu = ultimo_menu_usuario.get(contato)
        if ultimo_menu:
            enviar_mensagem(contato, "Você está inativo. Escolha uma das opções abaixo:")
            enviar_mensagem(contato, ultimo_menu)
            salvar_mensagem_em_arquivo(contato, nome_cliente, "Bot: Repetiu o menu apropriado.")
        else:
            # Reinicia a interação se não houver estado conhecido
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


def solicitar_altura(contato, nome_cliente, tipo_medida):
    """
    Solicita ao cliente a medida da altura.
    """
    enviar_mensagem(contato, f"Por favor, informe a medida da altura em milímetros (mm) ({tipo_medida}):")
    status_usuario[contato] = "coletando_altura"
    salvar_mensagem_em_arquivo(contato, nome_cliente, "Bot: Solicitou medida da altura (mm).")


def solicitar_largura(contato, nome_cliente, tipo_medida, altura):
    """
    Solicita ao cliente a medida da largura.
    """
    enviar_mensagem(contato, f"Altura registrada: {altura} mm.")
    enviar_mensagem(contato, f"Agora, informe a medida da largura em milímetros (mm) ({tipo_medida}):")
    status_usuario[contato] = "coletando_largura"
    salvar_mensagem_em_arquivo(contato, nome_cliente, f"Bot: Solicitou medida da largura (mm) (Altura: {altura} mm).")


def encerrar_fluxo(contato, nome_cliente, altura, largura):
    """
    Finaliza o fluxo após coletar as medidas.
    """
    enviar_mensagem(contato, f"Medidas registradas:\nAltura: {altura} mm\nLargura: {largura} mm.")
    enviar_mensagem(contato, "Obrigado! Seu fluxo foi encerrado. Caso precise de algo, estamos à disposição!")
    salvar_mensagem_em_arquivo(contato, nome_cliente, f"Bot: Fluxo encerrado com medidas (Altura: {altura} mm, Largura: {largura} mm).")
    limpar_dados_usuario(contato)



def processar_altura(contato, texto, nome_cliente):
    """
    Processa a medida da altura fornecida pelo cliente.
    """
    try:
        altura = int(texto)  # Tentar converter a entrada para inteiro
        if altura <= 0:
            raise ValueError("A medida deve ser um número positivo.")

        # Salvar a altura e solicitar a largura
        informacoes_cliente[contato]["altura"] = altura
        tipo_medida = "final" if informacoes_cliente[contato].get("medida_final") else "vão"
        solicitar_largura(contato, nome_cliente, tipo_medida, altura)
    except ValueError:
        enviar_mensagem(contato, "Altura inválida. Por favor, informe a medida da altura como um número inteiro positivo em milímetros (mm).")



def processar_largura(contato, texto, nome_cliente):
    """
    Processa a medida da largura fornecida pelo cliente e encerra o fluxo.
    """
    try:
        largura = int(texto)  # Tentar converter a entrada para inteiro
        if largura <= 0:
            raise ValueError("A medida deve ser um número positivo.")

        # Salvar a largura e encerrar o fluxo
        informacoes_cliente[contato]["largura"] = largura
        altura = informacoes_cliente[contato]["altura"]
        encerrar_fluxo(contato, nome_cliente, altura, largura)
    except ValueError:
        enviar_mensagem(contato, "Largura inválida. Por favor, informe a medida da largura como um número inteiro positivo em milímetros (mm).")


