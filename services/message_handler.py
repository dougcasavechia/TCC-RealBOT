import pandas as pd
from services.client_service import buscar_cliente_por_telefone
from services.message_service import enviar_mensagem, salvar_mensagem_em_arquivo
from services.product_service import gerar_menu_inicial, filtrar_projetos_por_escolhas, gerar_menu_por_definicao
from services.state_service import atualizar_ultima_atividade
from services.materials_service import gerar_menu_materia_prima, gerar_menu_por_definicao_mp, carregar_tabela_mp, gerar_menu_por_definicao_mp
from services.formula_service import calcular_pecas
from services.global_state import global_state
from logger import logger


def gerenciar_mensagem_recebida(contato, texto):
    """
    Processa mensagens recebidas e decide o fluxo com base no estado do usuário.
    """
    logger.info(f"📩 Mensagem recebida - contato: {contato}, texto: {texto}")

    # ✅ Atualiza o tempo de atividade do usuário
    atualizar_ultima_atividade(contato)

    # Buscar informações do cliente no estado global
    cliente_info = global_state.informacoes_cliente.get(contato)

    if not cliente_info:
        logger.debug(f"🔍 Buscando cliente no banco para o número: {contato}")
        cliente_info = buscar_cliente_por_telefone(contato)

        if cliente_info and isinstance(cliente_info, dict) and cliente_info.get("nome_cliente"):
            global_state.informacoes_cliente[contato] = cliente_info
        else:
            enviar_mensagem(contato, "❌ Seu número não está cadastrado. Solicite cadastro com um vendedor.")
            salvar_mensagem_em_arquivo(contato, "Desconhecido", "Bot: Número não cadastrado.")
            global_state.limpar_dados_usuario(contato)
            return

    nome_cliente = cliente_info.get("nome_cliente", "Cliente").strip()

    # ✅ Inicializa o estado do usuário, caso ele não tenha um
    if contato not in global_state.status_usuario:
        global_state.status_usuario[contato] = "inicial"

    status = global_state.status_usuario.get(contato, "inicial")

    # ✅ Restaurar estado caso o usuário estivesse inativo
    if status.startswith("inativo_"):
        logger.info(f"⏳ Retomando estado anterior para {contato}.")
        status = status.replace("inativo_", "")  # Remove o prefixo "inativo_"
        global_state.status_usuario[contato] = status

    # ✅ Delegar para o fluxo correto com TODOS os estados
    if status == "inicial":
        perguntar_tipo_medida(contato, nome_cliente)
    elif status == "definindo_medida":
        processar_tipo_medida(contato, texto, nome_cliente)
    elif status == "definicao_1":
        processar_menu_dinamico_produto(contato, texto, nome_cliente, "definicao_1")
    elif status == "definicao_2":
        processar_menu_dinamico_produto(contato, texto, nome_cliente, "definicao_2")
    elif status == "definicao_3":
        processar_menu_dinamico_produto(contato, texto, nome_cliente, "definicao_3")
    elif status == "aguardando_altura":
        processar_altura(contato, texto)
    elif status == "aguardando_largura":
        processar_largura(contato, texto)
    elif status == "cor_materia_prima":
        processar_menu_dinamico_mp(contato, texto, "cor_materia_prima")
    elif status == "espessura_materia_prima":
        processar_menu_dinamico_mp(contato, texto, "espessura_materia_prima")
    elif status == "beneficiamento":
        processar_menu_dinamico_mp(contato, texto, "beneficiamento")
    elif status == "aguardando_quantidade":
        processar_quantidade(contato, texto)
    else:
        repetir_menu(contato, nome_cliente)


def perguntar_tipo_medida(contato, nome_cliente):
    """
    Pergunta ao usuário se a medida é final ou de vão.
    """
    logger.info(f"🟢 Perguntando tipo de medida para {contato}.")
    
    # Criar o menu de opções
    menu = ["Medida final", "Medida de vão"]
    enviar_mensagem(contato, "Qual o tipo de medida que deseja informar?")
    enviar_mensagem(contato, "\n".join([f"{i + 1}. {opcao}" for i, opcao in enumerate(menu)]))

    # Atualiza o estado e salva o menu no global_state
    global_state.status_usuario[contato] = "definindo_medida"
    global_state.ultimo_menu_usuario[contato] = menu  # Armazena o menu
    salvar_mensagem_em_arquivo(contato, nome_cliente, "Bot: Perguntou sobre tipo de medida.")


def processar_tipo_medida(contato, texto, nome_cliente):
    """
    Processa a escolha do tipo de medida (final ou vão) e inicia o fluxo de seleção.
    """
    try:
        escolha = int(texto)
        if escolha not in [1, 2]:
            raise ValueError("Opção inválida.")

        medida_final = 1 if escolha == 1 else 0
        global_state.informacoes_cliente[contato]["medida_final"] = medida_final

        tipo_medida = "final" if medida_final == 1 else "de vão"
        logger.info(f"✅ {nome_cliente} ({contato}) escolheu medida {tipo_medida}.")
        enviar_mensagem(contato, f"Você escolheu informar a medida {tipo_medida}.")
        salvar_mensagem_em_arquivo(contato, nome_cliente, f"Bot: Usuário escolheu medida {tipo_medida}.")

        # Inicia o menu de produtos filtrado pela medida
        iniciar_conversa(contato, nome_cliente)
    except ValueError:
        logger.warning(f"⚠️ {contato} enviou uma opção inválida para tipo de medida.")
        enviar_mensagem(contato, "Opção inválida. Por favor, escolha entre:\n1. Medida final\n2. Medida de vão")


def iniciar_conversa(contato, nome_cliente):
    """
    Inicia a conversa com o usuário e apresenta o menu inicial.
    """
    logger.info(f"🟢 Iniciando conversa com {contato}.")
    enviar_mensagem(contato, "Vamos começar escolhendo o tipo de produto.")

    # Obtém a medida selecionada
    medida_final = global_state.informacoes_cliente[contato].get("medida_final")

    # Gera o menu inicial a partir da tabela, filtrando pela medida
    opcoes = gerar_menu_inicial(medida_final=medida_final)  # Filtra pelo tipo de medida

    if opcoes:
        # Atualiza o estado e salva o menu no global_state
        global_state.status_usuario[contato] = "definicao_1"
        global_state.ultimo_menu_usuario[contato] = opcoes  # Armazenar como lista
        apresentar_menu(contato, nome_cliente, opcoes, "definicao_1")
    else:
        enviar_mensagem(contato, "❌ Não há opções disponíveis para a medida escolhida. Tente novamente mais tarde.")
        salvar_mensagem_em_arquivo(contato, nome_cliente, "Bot: Menu inicial vazio.")
        finalizar_conversa(contato, nome_cliente)



def processar_menu_dinamico_produto(contato, texto, nome_cliente, estado_atual):
    """
    Processa o menu dinâmico com base no estado atual e na escolha do usuário.
    Trata entradas inválidas e repete o menu se necessário.
    """
    try:
        escolha = int(texto) - 1  # Ajustar índice para 0-based
        opcoes = global_state.ultimo_menu_usuario.get(contato)

        # Verificar se a escolha está dentro do intervalo válido
        if not opcoes or escolha < 0 or escolha >= len(opcoes):
            raise ValueError("Opção inválida.")

        # Capturar a escolha válida
        escolha_usuario = opcoes[escolha]
        salvar_mensagem_em_arquivo(contato, nome_cliente, f"Bot: Opção escolhida: {escolha_usuario}.")

        # Atualizar o estado global com a escolha
        informacoes_cliente = global_state.informacoes_cliente.setdefault(contato, {})
        informacoes_cliente[estado_atual] = escolha_usuario

        # Filtrar os projetos com base nas escolhas atuais
        chaves_relevantes = ["definicao_1", "definicao_2", "definicao_3", "medida_final"]
        dados_para_filtrar = {k: v for k, v in informacoes_cliente.items() if k in chaves_relevantes}
        projetos = filtrar_projetos_por_escolhas(**dados_para_filtrar)

        if not projetos:
            enviar_mensagem(contato, "❌ Nenhum projeto encontrado. Tente novamente mais tarde.")
            finalizar_conversa(contato, nome_cliente)
            return

        # Se só restar UM projeto, significa que é a escolha final
        if len(projetos) == 1:
            projeto_escolhido = projetos[0]
            descricao_projeto = projeto_escolhido.get("descricao_projeto", "Projeto sem descrição.")
            enviar_mensagem(contato, f"✅ Projeto selecionado: {descricao_projeto}.")
            salvar_mensagem_em_arquivo(contato, nome_cliente, f"Bot: Projeto finalizado: {descricao_projeto}.")

            # **INICIAR O PROCESSO DE MEDIÇÃO**
            processar_projeto(contato, nome_cliente, projeto_escolhido)
            return

        # Identificar a próxima definição válida
        definicoes_ordenadas = ["definicao_2", "definicao_3"]
        proxima_definicao = None

        for definicao in definicoes_ordenadas:
            if definicao not in informacoes_cliente and gerar_menu_por_definicao(pd.DataFrame(projetos), definicao):
                proxima_definicao = definicao
                break

        if proxima_definicao:
            # Gera o próximo menu
            opcoes_proxima_definicao = gerar_menu_por_definicao(pd.DataFrame(projetos), proxima_definicao)
            if opcoes_proxima_definicao:
                apresentar_menu(contato, nome_cliente, opcoes_proxima_definicao, proxima_definicao)
                return

        # Se não há mais definições a perguntar, encerrar a conversa
        finalizar_selecao(contato, nome_cliente, projetos)

    except ValueError:
        enviar_mensagem(contato, "Opção inválida. Por favor, escolha uma das opções listadas abaixo:")
        repetir_menu(contato, nome_cliente)


def finalizar_selecao(contato, nome_cliente, projetos):
    """
    Finaliza a seleção e informa ao usuário o projeto escolhido.
    """
    if projetos:
        projeto_escolhido = projetos[0]  # Considera o primeiro projeto como escolhido
        descricao = projeto_escolhido.get("descricao_projeto", "Projeto não descrito.")
        enviar_mensagem(contato, f"✅ Projeto selecionado: {descricao}.")
        salvar_mensagem_em_arquivo(contato, nome_cliente, f"Bot: Projeto finalizado: {descricao}.")
    else:
        enviar_mensagem(contato, "❌ Não foi possível encontrar um projeto válido. Tente novamente.")
        salvar_mensagem_em_arquivo(contato, nome_cliente, "Bot: Finalização sem projeto válido.")

    finalizar_conversa(contato, nome_cliente)


def apresentar_menu(contato, nome_cliente, opcoes, estado):
    """
    Envia o menu ao usuário e atualiza o estado no global_state.
    """
    menu = "\n".join([f"{i + 1}. {opcao}" for i, opcao in enumerate(opcoes)])
    enviar_mensagem(contato, "Escolha uma das opções:")
    enviar_mensagem(contato, menu)

    global_state.status_usuario[contato] = estado
    global_state.ultimo_menu_usuario[contato] = opcoes
    salvar_mensagem_em_arquivo(contato, nome_cliente, f"Bot: Apresentou menu para {estado}.")


def processar_projeto(contato, nome_cliente, projeto):
    """
    Inicia o fluxo solicitando altura e largura do usuário.
    """
    global_state.informacoes_cliente[contato]["projeto_escolhido"] = projeto
    enviar_mensagem(contato, "Informe a altura do vão ou da peça em milímetros:")
    global_state.status_usuario[contato] = "aguardando_altura"


def processar_altura(contato, texto):
    """
    Processa a altura enviada pelo usuário e salva no estado global.
    """
    try:
        altura = int(texto)
        dados_usuario = global_state.informacoes_cliente.get(contato, {})

        # **Salvando altura corretamente no estado global**
        dados_usuario["altura"] = altura
        global_state.informacoes_cliente[contato] = dados_usuario  # Atualiza o estado

        logger.debug(f"📏 Altura salva: {altura}mm para {contato}")

        enviar_mensagem(contato, "Agora informe a largura em milímetros:")
        global_state.status_usuario[contato] = "aguardando_largura"

    except ValueError:
        enviar_mensagem(contato, "❌ Altura inválida! Digite um número inteiro.")


def processar_largura(contato, texto):
    try:
        largura = int(texto)
        dados_usuario = global_state.informacoes_cliente.get(contato, {})

        if "altura" not in dados_usuario:
            logger.error(f"❌ Erro: Altura não encontrada para {contato}. Estado atual: {dados_usuario}")
            enviar_mensagem(contato, "❌ Erro ao recuperar a altura. Informe novamente.")
            return

        dados_usuario["largura"] = largura
        global_state.informacoes_cliente[contato] = dados_usuario  # Atualiza o estado

        logger.debug(f"📏 Largura salva: {largura}mm para {contato}")

        # 📌 **Novo fluxo: Inicia menu de matéria-prima**
        opcoes_mp = gerar_menu_materia_prima()
        if opcoes_mp:
            apresentar_menu_mp(contato, opcoes_mp, "cor_materia_prima")
        else:
            enviar_mensagem(contato, "❌ Nenhuma matéria-prima disponível. Tente novamente mais tarde.")
            return

    except ValueError:
        enviar_mensagem(contato, "❌ Largura inválida! Digite um número inteiro.")


def validar_pecas_calculadas(pecas):
    """
    Valida se a lista de peças está no formato correto.
    Retorna uma lista de peças válidas ou None em caso de erro.
    """
    if not isinstance(pecas, list):
        logger.error(f"❌ Erro: 'pecas' deveria ser uma lista, mas é {type(pecas)}")
        return None

    pecas_validas = []

    for peca in pecas:
        if not isinstance(peca, dict):
            logger.error(f"❌ Tipo inesperado em 'peca': {type(peca)} - Valor: {peca}")
            continue  # Ignora itens inválidos

        if "nome_peca" not in peca or "quantidade" not in peca or "dimensoes" not in peca:
            logger.error(f"❌ Peça inválida: {peca}")
            continue

        pecas_validas.append(peca)

    return pecas_validas if pecas_validas else None

def apresentar_menu_mp(contato, opcoes, estado):
    """
    Envia o menu de matéria-prima ao usuário e atualiza o estado no global_state.
    """
    menu = "\n".join([f"{i + 1}. {opcao}" for i, opcao in enumerate(opcoes)])
    enviar_mensagem(contato, "Escolha uma das opções:")
    enviar_mensagem(contato, menu)

    # Atualizar o estado do usuário e salvar o menu atual
    global_state.status_usuario[contato] = estado
    global_state.ultimo_menu_usuario[contato] = opcoes
    salvar_mensagem_em_arquivo(contato, "Bot", f"Bot: Apresentou menu para o estado '{estado}'.")


def processar_menu_dinamico_mp(contato, texto, estado_atual):
    """
    Processa a escolha do usuário no menu dinâmico de matéria-prima.
    """
    try:
        escolha = int(texto) - 1  # Ajustar índice para 0-based
        opcoes = global_state.ultimo_menu_usuario.get(contato)

        # Verificar se a escolha é válida
        if not opcoes or escolha < 0 or escolha >= len(opcoes):
            raise ValueError("Opção inválida.")

        # Registrar a escolha feita pelo usuário
        escolha_usuario = opcoes[escolha]
        salvar_mensagem_em_arquivo(contato, "Bot", f"Bot: Usuário escolheu: {escolha_usuario}.")
        informacoes_cliente = global_state.informacoes_cliente.setdefault(contato, {})
        informacoes_cliente[estado_atual] = escolha_usuario

        # Carregar a tabela de matéria-prima e aplicar filtros dinamicamente
        df_mp = carregar_tabela_mp()

        # Mapeamento das colunas reais no DataFrame
        colunas_reais = {
            "cor_materia_prima": "cor_materia_prima",
            "espessura_materia_prima": "espessura_materia_prima",
            "beneficiamento": "beneficiamento",
        }

        # Aplicar filtros com base nas escolhas feitas
        for chave_estado, coluna_real in colunas_reais.items():
            valor = informacoes_cliente.get(chave_estado)
            if valor:
                df_mp = df_mp[df_mp[coluna_real] == valor]

        # Determinar a próxima definição a ser exibida
        definicoes_ordenadas = ["espessura_materia_prima", "beneficiamento"]
        proxima_definicao = None
        for definicao in definicoes_ordenadas:
            # Verifica se já processou essa definição ou se há opções disponíveis
            if definicao not in informacoes_cliente:
                opcoes_proxima_definicao = gerar_menu_por_definicao_mp(df_mp, colunas_reais[definicao])
                if opcoes_proxima_definicao:  # Gera o próximo menu somente se houver opções válidas
                    proxima_definicao = definicao
                    break

        if proxima_definicao:
            # Gerar e apresentar o menu para a próxima definição
            apresentar_menu_mp(contato, opcoes_proxima_definicao, proxima_definicao)
            global_state.status_usuario[contato] = proxima_definicao
        else:
            # Se não houver mais definições, finalizar a seleção
            finalizar_selecao_mp(contato, informacoes_cliente)

    except ValueError:
        # Repetir o menu caso o valor seja inválido
        enviar_mensagem(contato, "Opção inválida. Por favor, escolha uma das opções listadas abaixo:")
        repetir_menu(contato, "Bot")

def finalizar_selecao_mp(contato, informacoes_cliente):
    """
    Finaliza a seleção de matéria-prima e continua para a próxima etapa.
    """
    materia_prima = informacoes_cliente.get("cor_materia_prima", "Matéria-prima não definida")
    espessura = informacoes_cliente.get("espessura_materia_prima", "Espessura não definida")
    beneficiamento = informacoes_cliente.get("beneficiamento", "Beneficiamento não definido")
    altura = informacoes_cliente.get("altura")
    largura = informacoes_cliente.get("largura")

    if not altura or not largura:
        enviar_mensagem(contato, "❌ Erro interno: Altura ou largura não definida. Reinicie o processo.")
        return

    # Obter a fórmula do projeto escolhido
    projeto = informacoes_cliente.get("projeto_escolhido", {})
    id_formula = projeto.get("id_formula")

    if not id_formula:
        enviar_mensagem(contato, "❌ Erro interno: Fórmula do projeto não encontrada. Reinicie o processo.")
        return

    # **Usar calcular_pecas do formula_service.py**
    pecas = calcular_pecas(id_formula, altura, largura)

    if not pecas:
        enviar_mensagem(contato, "❌ Erro ao calcular as peças. Tente novamente.")
        return

    # **Salvar as peças calculadas**
    informacoes_cliente["pecas"] = pecas
    global_state.informacoes_cliente[contato] = informacoes_cliente

    # Exibir o resumo da seleção
    enviar_mensagem(
        contato,
        f"✅ Matéria-prima escolhida: {materia_prima}, {espessura}, {beneficiamento}."
    )

    # Exibir as peças calculadas
    msg_pecas = "📏 Peças calculadas:\n"
    for peca in pecas:
        msg_pecas += f"{peca['quantidade']}x {peca['nome_peca']}: {peca['dimensoes'][0]}mm x {peca['dimensoes'][1]}mm\n"

    enviar_mensagem(contato, msg_pecas)

    # Pedir a quantidade ao usuário
    enviar_mensagem(contato, "Quantas unidades desse projeto você deseja?")
    global_state.status_usuario[contato] = "aguardando_quantidade"



def processar_quantidade(contato, texto):
    """
    Processa a quantidade informada e exibe as dimensões corretas para medida final ou medida de vão.
    """
    try:
        quantidade = int(texto)
        dados_usuario = global_state.informacoes_cliente[contato]
        projeto = dados_usuario["projeto_escolhido"]
        descricao_projeto = projeto.get("descricao_projeto", "Projeto sem descrição.")
        id_formula = projeto.get("id_formula", 0)
        medida_final = dados_usuario.get("medida_final")  # Se for 1, significa que o usuário escolheu medida final

        logger.debug(f"📊 ID Fórmula: {id_formula}, Medida Final: {medida_final}, Quantidade: {quantidade}")
        
        # Se for medida final, usamos os valores informados diretamente
        if medida_final and id_formula == 1:
            altura = dados_usuario["altura"]
            largura = dados_usuario["largura"]

            msg_final = f"📦 Você solicitou {quantidade} unidades do item {descricao_projeto} de {altura}mm x {largura}mm."
        
        else:
            # Se for medida de vão, aplicamos as fórmulas para calcular as peças
            pecas = dados_usuario.get("pecas", [])

            logger.debug(f"📌 Conteúdo de 'pecas' antes da multiplicação: {pecas}")

            if not isinstance(pecas, list) or len(pecas) == 0:
                logger.error("❌ Erro: 'pecas' está vazio ou não é uma lista válida.")
                enviar_mensagem(contato, "❌ Erro interno ao calcular as peças. Tente novamente.")
                return

            pecas_multiplicadas = []

            for peca in pecas:
                if not isinstance(peca, dict):
                    logger.error(f"❌ Tipo inesperado em 'peca': {type(peca)} - Valor: {peca}")
                    continue  # Ignora valores inválidos

                pecas_multiplicadas.append({
                    "nome_peca": peca.get("nome_peca", "Peça"),
                    "quantidade": peca.get("quantidade", 1) * quantidade,
                    "dimensoes": peca.get("dimensoes", (0, 0))
                })

            logger.debug(f"📌 Pecas multiplicadas: {pecas_multiplicadas}")

            msg_final = f"📦 Para {quantidade} unidades do item {descricao_projeto}, você precisará de:\n"
            for peca in pecas_multiplicadas:
                msg_final += f"{peca['quantidade']}x {peca['nome_peca']}: {peca['dimensoes'][0]}mm x {peca['dimensoes'][1]}mm\n"

        enviar_mensagem(contato, msg_final)
        salvar_mensagem_em_arquivo(contato, descricao_projeto, msg_final)
        finalizar_conversa(contato, "Pedido finalizado.")

    except ValueError:
        enviar_mensagem(contato, "❌ Quantidade inválida! Digite um número inteiro.")


def repetir_menu(contato, nome_cliente):
    """
    Reenvia o menu apropriado com base no estado atual do usuário.
    """
    status = global_state.status_usuario.get(contato)
    ultimo_menu = global_state.ultimo_menu_usuario.get(contato)

    if ultimo_menu:
        enviar_mensagem(contato, "Por favor, escolha uma das opções listadas abaixo:")
        enviar_mensagem(contato, "\n".join([f"{i + 1}. {opcao}" for i, opcao in enumerate(ultimo_menu)]))
        salvar_mensagem_em_arquivo(contato, nome_cliente, f"Bot: Repetiu o menu para o estado '{status}'.")
    else:
        enviar_mensagem(contato, "Conversa encerrada por inatividade. Para reiniciar, envie qualquer mensagem.")
        salvar_mensagem_em_arquivo(contato, nome_cliente, "Bot: Conversa encerrada por inatividade.")
        global_state.limpar_dados_usuario(contato)


def finalizar_conversa(contato, nome_cliente):
    """
    Finaliza a conversa e limpa os dados do usuário do estado global.
    """
    enviar_mensagem(contato, "Obrigado! Caso precise de algo, estamos à disposição! 😊")
    salvar_mensagem_em_arquivo(contato, nome_cliente, "Bot: Conversa encerrada.")
    global_state.limpar_dados_usuario(contato)
    