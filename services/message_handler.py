import time
from services.client_service import buscar_cliente_por_telefone
from services.message_service import enviar_mensagem, salvar_mensagem_em_arquivo
from services.product_service import carregar_tabela_tipo_produto
from services.formula_service import obter_formula_por_id
from services.global_state import global_state
from logger import logger


def gerenciar_mensagem_recebida(contato, texto):
    """
    Processa mensagens recebidas e decide o fluxo com base no estado do usuário.
    """
    logger.info(f"📩 Mensagem recebida - contato: {contato}, texto: {texto}")

    global_state.ultima_interacao_usuario[contato] = time.time()

    # Buscar informações do cliente no estado global
    cliente_info = global_state.informacoes_cliente.get(contato)

    if not cliente_info:
        logger.debug(f"🔍 Buscando cliente no banco para o número: {contato}")
        cliente_info = buscar_cliente_por_telefone(contato)
        logger.debug(f"📌 Dados completos do cliente: {cliente_info}")

        if cliente_info and isinstance(cliente_info, dict) and cliente_info.get("nome_cliente"):
            global_state.informacoes_cliente[contato] = cliente_info
        else:
            enviar_mensagem(contato, "❌ Seu número não está cadastrado. Solicite cadastro com um vendedor.")
            salvar_mensagem_em_arquivo(contato, "Desconhecido", "Bot: Número não cadastrado.")
            global_state.limpar_dados_usuario(contato)
            return

    # 🚨 Garantir que nome_cliente está correto
    nome_cliente = cliente_info.get("nome_cliente", "").strip()

    if not nome_cliente:
        logger.warning(f"⚠️ Nome do cliente não encontrado para {contato}, definindo como 'Cliente'.")
        nome_cliente = "Cliente"

    print(f"#############################")
    print(f"📌 Nome que será passado para iniciar_conversa: {nome_cliente}")
    print(f"#############################")

    logger.debug(f"📌 Nome final utilizado: {nome_cliente}")

    status = global_state.status_usuario.get(contato, "inicial")

    if status.startswith("inativo_"):
        logger.info(f"⏳ Retomando estado anterior para {contato}.")
        global_state.status_usuario[contato] = status.replace("inativo_", "")
        status = global_state.status_usuario[contato]

    handlers = {
        "aguardando_decisao_inicial": processar_decisao_usuario,
        "escolhendo_medida_vao_ou_final": processar_medida_vao_final,
        "escolhendo_tipo_produto": processar_selecao_produto,
        "escolhendo_projeto": processar_selecao_projeto,
        "coletando_altura": processar_altura,
        "coletando_largura": processar_largura,
        "coletando_quantidade": processar_quantidade
    }

    # 🚨 Correção: Tratar `iniciar_conversa()` separadamente para evitar erro de argumentos
    if status == "inicial":
        iniciar_conversa(contato, nome_cliente)  # 🔥 Agora não passamos `texto`
    else:
        handler = handlers.get(status, tratar_estado_desconhecido)
        handler(contato, texto, nome_cliente)  # Apenas os outros handlers recebem `texto`


def tratar_estado_desconhecido(contato, texto, nome_cliente):
    logger.warning(f"⚠️ Estado desconhecido para {contato}: {global_state.status_usuario.get(contato)}")
    enviar_mensagem(contato, "Desculpe, ocorreu um problema. Vamos reiniciar sua interação.")
    iniciar_conversa(contato, nome_cliente)


def iniciar_conversa(contato, nome_cliente, *_):
    """
    Inicia a conversa com o usuário.
    """
    logger.info(f"🟢 Iniciando conversa com {contato}.")
    
    # 🚨 Adicionando log para ver se o nome ainda está correto aqui
    print(f"#############################")
    print(f"📌 Nome dentro de iniciar_conversa: {nome_cliente}")
    print(f"#############################")

    menu = "1. Realizar orçamento\n2. Conferir orçamento"
    enviar_mensagem(contato, f"Olá, {nome_cliente}! Como posso ajudar hoje?")
    enviar_mensagem(contato, menu)

    global_state.status_usuario[contato] = "aguardando_decisao_inicial"
    global_state.ultimo_menu_usuario[contato] = menu
    salvar_mensagem_em_arquivo(contato, nome_cliente, "Bot: Apresentou opções iniciais.")


def processar_medida_vao_final(contato, texto, nome_cliente):
    """
    Processa a escolha do usuário entre medida final ou medida de vão.
    """
    if texto == "1":  # Medida Final
        enviar_mensagem(contato, "Você escolheu informar a medida FINAL.")
        salvar_mensagem_em_arquivo(contato, nome_cliente, "Bot: Usuário escolheu medida final.")
        global_state.informacoes_cliente[contato]["medida_final"] = 1  # 1 representa medida final
        apresentar_menu_produtos(contato, nome_cliente)

    elif texto == "2":  # Medida de Vão
        enviar_mensagem(contato, "Você escolheu informar a medida de VÃO.")
        salvar_mensagem_em_arquivo(contato, nome_cliente, "Bot: Usuário escolheu medida de vão.")
        global_state.informacoes_cliente[contato]["medida_final"] = 0  # 0 representa medida de vão
        apresentar_menu_produtos(contato, nome_cliente)

    else:
        enviar_mensagem(contato, "Opção inválida. Por favor, escolha entre:")
        menu = "1. Medida final\n2. Medida de vão"
        enviar_mensagem(contato, menu)
        global_state.ultimo_menu_usuario[contato] = menu


def processar_decisao_usuario(contato, texto, nome_cliente):
    """
    Processa a decisão inicial do usuário.

    :param contato: Número do cliente
    :param texto: Escolha do usuário
    :param nome_cliente: Nome do cliente
    """
    if texto == "1":
        enviar_mensagem(contato, "Você deseja informar:")
        menu = "1. Medida final\n2. Medida de vão"
        enviar_mensagem(contato, menu)

        global_state.status_usuario[contato] = "escolhendo_medida_vao_ou_final"
        global_state.ultimo_menu_usuario[contato] = menu
        salvar_mensagem_em_arquivo(contato, nome_cliente, "Bot: Perguntou sobre tipo de medida.")

    elif texto == "2":
        enviar_mensagem(contato, "⚠️ Opção 'Conferir orçamento' ainda não está disponível. Tente novamente mais tarde.")
        salvar_mensagem_em_arquivo(contato, nome_cliente, "Bot: Opção 'Conferir orçamento' não implementada.")
        finalizar_conversa(contato, nome_cliente)

    else:
        repetir_menu(contato, nome_cliente)


def apresentar_menu_produtos(contato, nome_cliente):
    """
    Apresenta o menu de produtos disponíveis após a escolha da medida.
    """
    produtos = carregar_tabela_tipo_produto()

    if produtos:
        menu = "\n".join([f"{i + 1}. {produto}" for i, produto in enumerate(produtos)])
        enviar_mensagem(contato, "Escolha o tipo de produto:")
        enviar_mensagem(contato, menu)

        global_state.status_usuario[contato] = "escolhendo_tipo_produto"
        global_state.ultimo_menu_usuario[contato] = menu
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
    :param medida_final: 1 para medida final, 0 para medida de vão
    """
    from services.product_service import filtrar_projetos

    projetos = filtrar_projetos(id_tipo_produto, medida_final)

    if not projetos:
        enviar_mensagem(contato, "Não há projetos disponíveis para sua escolha no momento. Tente novamente mais tarde.")
        salvar_mensagem_em_arquivo(contato, nome_cliente, "Bot: Nenhum projeto disponível.")
        finalizar_conversa(contato, nome_cliente)
        return

    # Criar o menu com as opções de projetos disponíveis
    menu = "\n".join([f"{i + 1}. {projeto['descricao_projeto']}" for i, projeto in enumerate(projetos)])
    enviar_mensagem(contato, "Escolha um dos projetos disponíveis:")
    enviar_mensagem(contato, menu)

    # Salvar os projetos filtrados para referência futura
    global_state.informacoes_cliente[contato]["projetos"] = projetos
    global_state.status_usuario[contato] = "escolhendo_projeto"
    global_state.ultimo_menu_usuario[contato] = menu
    salvar_mensagem_em_arquivo(contato, nome_cliente, "Bot: Apresentou menu de projetos.")


def processar_selecao_produto(contato, texto, nome_cliente):
    produtos = carregar_tabela_tipo_produto()
    try:
        escolha = int(texto) - 1
        if 0 <= escolha < len(produtos):
            produto_selecionado = produtos[escolha]
            id_tipo_produto = escolha + 1  
            enviar_mensagem(contato, f"Você escolheu o tipo de produto: {produto_selecionado}.")
            salvar_mensagem_em_arquivo(contato, nome_cliente, f"Bot: Produto escolhido: {produto_selecionado}.")
            medida_final = global_state.informacoes_cliente[contato].get("medida_final", 0)
            apresentar_menu_projetos(contato, nome_cliente, id_tipo_produto, medida_final)
        else:
            raise ValueError("Opção inválida.")
    except (ValueError, IndexError):
        repetir_menu(contato, nome_cliente)


def processar_selecao_projeto(contato, texto, nome_cliente):
    projetos = global_state.informacoes_cliente[contato].get("projetos", [])
    if not projetos:
        enviar_mensagem(contato, "Erro ao recuperar os projetos. Reiniciaremos sua interação.")
        iniciar_conversa(contato, nome_cliente)
        return

    try:
        escolha = int(texto) - 1
        if 0 <= escolha < len(projetos):
            projeto_selecionado = projetos[escolha]
            global_state.informacoes_cliente[contato]["id_formula"] = projeto_selecionado.get("id_formula")
            enviar_mensagem(contato, f"Você escolheu o projeto: {projeto_selecionado['descricao_projeto']}.")
            salvar_mensagem_em_arquivo(contato, nome_cliente, f"Bot: Projeto escolhido: {projeto_selecionado['descricao_projeto']}.")
            tipo_medida = "final" if global_state.informacoes_cliente[contato].get("medida_final") else "vão"
            solicitar_altura(contato, nome_cliente, tipo_medida)
        else:
            raise ValueError("Opção inválida.")
    except (ValueError, IndexError):
        repetir_menu(contato, nome_cliente)


def solicitar_altura(contato, nome_cliente, tipo_medida):
    """
    Solicita ao cliente a medida da altura.

    :param contato: Número do cliente
    :param nome_cliente: Nome do cliente
    :param tipo_medida: Tipo de medida ('final' ou 'vão')
    """
    enviar_mensagem(contato, f"📏 Informe a medida da altura em milímetros (mm) ({tipo_medida}):")
    global_state.status_usuario[contato] = "coletando_altura"
    salvar_mensagem_em_arquivo(contato, nome_cliente, f"Bot: Solicitou medida da altura ({tipo_medida}).")


def processar_altura(contato, texto, nome_cliente):
    try:
        altura = int(texto)
        if altura <= 0:
            raise ValueError("A medida deve ser positiva.")
        global_state.informacoes_cliente[contato]["altura"] = altura
        tipo_medida = "final" if global_state.informacoes_cliente[contato].get("medida_final") else "vão"
        solicitar_largura(contato, nome_cliente, tipo_medida, altura)
    except ValueError:
        enviar_mensagem(contato, "Altura inválida. Informe um número inteiro positivo.")


def solicitar_largura(contato, nome_cliente, tipo_medida, altura):
    """
    Solicita ao cliente a medida da largura após a altura ter sido registrada.

    :param contato: Número do cliente
    :param nome_cliente: Nome do cliente
    :param tipo_medida: Tipo de medida ('final' ou 'vão')
    :param altura: Altura previamente informada pelo cliente
    """
    enviar_mensagem(contato, f"📏 Altura registrada: {altura} mm.")
    enviar_mensagem(contato, f"Agora, informe a medida da largura em milímetros (mm) ({tipo_medida}):")

    global_state.status_usuario[contato] = "coletando_largura"
    salvar_mensagem_em_arquivo(contato, nome_cliente, f"Bot: Solicitou medida da largura ({tipo_medida}).")


def processar_largura(contato, texto, nome_cliente):
    try:
        largura = int(texto)
        if largura <= 0:
            raise ValueError("A medida deve ser positiva.")
        global_state.informacoes_cliente[contato]["largura"] = largura
        altura = global_state.informacoes_cliente[contato].get("altura")
        if not altura:
            enviar_mensagem(contato, "Erro: Altura não registrada. Reiniciaremos sua interação.")
            iniciar_conversa(contato, nome_cliente)
            return
        processar_dimensoes_projeto(contato, nome_cliente)
    except ValueError:
        enviar_mensagem(contato, "Largura inválida. Informe um número inteiro positivo.")


def processar_dimensoes_projeto(contato, nome_cliente):
    """
    Processa as dimensões do projeto (altura e largura) e realiza os cálculos.

    :param contato: Número do cliente
    :param nome_cliente: Nome do cliente
    """
    altura = global_state.informacoes_cliente[contato].get("altura")
    largura = global_state.informacoes_cliente[contato].get("largura")

    if not altura or not largura:
        enviar_mensagem(contato, "Erro: Altura ou largura não registrada. Reiniciaremos sua interação.")
        iniciar_conversa(contato, nome_cliente)
        return

    id_formula = global_state.informacoes_cliente[contato].get("id_formula")
    if not id_formula:
        enviar_mensagem(contato, "Erro: Nenhuma fórmula associada ao projeto. Reiniciaremos sua interação.")
        iniciar_conversa(contato, nome_cliente)
        return

    formulas = obter_formula_por_id(id_formula)
    if not formulas:
        enviar_mensagem(contato, f"Erro: Fórmulas para o ID '{id_formula}' não encontradas. Reiniciaremos sua interação.")
        iniciar_conversa(contato, nome_cliente)
        return

    medida_final = global_state.informacoes_cliente[contato].get("medida_final", 1)

    try:
        dimensoes_fixas_calculadas = [
            {"quantidade": item["quantidade"], "dimensao": item["calculo"](altura, largura)}
            for item in formulas.get("fixa", [])
        ]

        dimensoes_moveis_calculadas = [
            {"quantidade": item["quantidade"], "dimensao": item["calculo"](altura, largura)}
            for item in formulas.get("movel", [])
        ]

    except Exception as e:
        logger.error(f"Erro ao calcular dimensões do projeto: {e}")
        enviar_mensagem(contato, "Erro ao calcular as dimensões do projeto. Reiniciaremos sua interação.")
        iniciar_conversa(contato, nome_cliente)
        return

    global_state.informacoes_cliente[contato]["dimensoes"] = {
        "fixa": dimensoes_fixas_calculadas,
        "movel": dimensoes_moveis_calculadas
    }

    enviar_mensagem(contato, f"📐 Projeto: {formulas['nome']}")
    enviar_mensagem(contato, f"Tamanho vão: {largura} x {altura} mm")

    if dimensoes_fixas_calculadas:
        for item in dimensoes_fixas_calculadas:
            enviar_mensagem(contato, f"{item['quantidade']} und (fixa) - {item['dimensao'][0]} x {item['dimensao'][1]} mm")
    else:
        enviar_mensagem(contato, "Nenhuma peça fixa encontrada para este projeto.")

    if dimensoes_moveis_calculadas:
        for item in dimensoes_moveis_calculadas:
            enviar_mensagem(contato, f"{item['quantidade']} und (móvel) - {item['dimensao'][0]} x {item['dimensao'][1]} mm")
    else:
        enviar_mensagem(contato, "Nenhuma peça móvel encontrada para este projeto.")

    solicitar_quantidade(contato, nome_cliente)


def solicitar_quantidade(contato, nome_cliente):
    """
    Pergunta ao usuário quantas unidades do projeto ele deseja.

    :param contato: Número do cliente
    :param nome_cliente: Nome do cliente
    """
    enviar_mensagem(contato, "📦 Quantas unidades você deseja para este projeto?")
    
    global_state.status_usuario[contato] = "coletando_quantidade"
    salvar_mensagem_em_arquivo(contato, nome_cliente, "Bot: Solicitou quantidade de unidades.")



def processar_quantidade(contato, texto, nome_cliente):
    try:
        quantidade = int(texto)
        if quantidade <= 0:
            raise ValueError("A quantidade deve ser positiva.")
        dimensoes = global_state.informacoes_cliente[contato].get("dimensoes")
        if not dimensoes:
            enviar_mensagem(contato, "Erro: Dimensões não calculadas. Reiniciaremos sua interação.")
            iniciar_conversa(contato, nome_cliente)
            return
        enviar_mensagem(contato, "Orçamento finalizado!")
        encerrar_fluxo(contato, nome_cliente)
    except ValueError:
        enviar_mensagem(contato, "Quantidade inválida. Informe um número inteiro positivo.")


def repetir_menu(contato, nome_cliente):
    """
    Reenvia a solicitação ou o menu apropriado com base no estado atual do usuário.
    """
    status = global_state.status_usuario.get(contato)
    logger.debug(f"🔄 Repetindo menu para {contato}, estado atual: {status}")

    if status == "coletando_altura":
        tipo_medida = "final" if global_state.informacoes_cliente[contato].get("medida_final") else "vão"
        enviar_mensagem(contato, f"Por favor, informe a medida da altura em milímetros (mm) ({tipo_medida}):")
        salvar_mensagem_em_arquivo(contato, nome_cliente, "Bot: Repetiu solicitação de altura.")

    elif status == "coletando_largura":
        tipo_medida = "final" if global_state.informacoes_cliente[contato].get("medida_final") else "vão"
        altura = global_state.informacoes_cliente[contato].get("altura", "não registrada")
        enviar_mensagem(contato, f"Altura registrada: {altura} mm. Informe a largura em milímetros (mm) ({tipo_medida}):")
        salvar_mensagem_em_arquivo(contato, nome_cliente, "Bot: Repetiu solicitação de largura.")

    elif status == "coletando_quantidade":
        enviar_mensagem(contato, "Quantas unidades você deseja para este projeto?")
        salvar_mensagem_em_arquivo(contato, nome_cliente, "Bot: Repetiu solicitação de quantidade.")

    else:
        # Se não for altura, largura ou quantidade, reenvia o último menu enviado
        ultimo_menu = global_state.ultimo_menu_usuario.get(contato)
        if ultimo_menu:
            enviar_mensagem(contato, "Escolha uma das opções abaixo:")
            enviar_mensagem(contato, ultimo_menu)
            salvar_mensagem_em_arquivo(contato, nome_cliente, "Bot: Repetiu o menu.")
        else:
            # Se não houver menu disponível, encerra a conversa por inatividade
            enviar_mensagem(contato, "Conversa encerrada por inatividade. Para reiniciar, envie qualquer mensagem.")
            salvar_mensagem_em_arquivo(contato, nome_cliente, "Bot: Conversa encerrada por inatividade.")
            global_state.limpar_dados_usuario(contato)


def finalizar_conversa(contato, nome_cliente):
    """
    Finaliza a conversa e limpa os dados do usuário do estado global.
    """
    enviar_mensagem(contato, "Obrigado! Qualquer coisa, é só chamar a gente novamente! 😊")
    salvar_mensagem_em_arquivo(contato, nome_cliente, "Bot: Conversa encerrada.")

    # Remover os dados do usuário do estado global
    global_state.limpar_dados_usuario(contato)


def encerrar_fluxo(contato, nome_cliente, altura=None, largura=None):
    """
    Finaliza o fluxo após coletar as medidas e limpa os dados do usuário.

    :param contato: Número do cliente
    :param nome_cliente: Nome do cliente
    :param altura: Altura registrada do projeto (opcional)
    :param largura: Largura registrada do projeto (opcional)
    """
    if altura is None or largura is None:
        altura = global_state.informacoes_cliente[contato].get("altura", "N/A")
        largura = global_state.informacoes_cliente[contato].get("largura", "N/A")

    enviar_mensagem(contato, "✅ Seu orçamento foi concluído! Caso precise de algo, estamos à disposição. 😊")
    salvar_mensagem_em_arquivo(contato, nome_cliente, f"Bot: Fluxo encerrado com medidas (Altura: {altura} mm, Largura: {largura} mm).")

    # Remover os dados do usuário do estado global
    global_state.limpar_dados_usuario(contato)


