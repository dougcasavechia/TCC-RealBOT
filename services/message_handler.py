import pandas as pd
from logger import logger
from services.client_service import ClienteCache
from services.message_service import enviar_mensagem, salvar_mensagem_em_arquivo
from services.product_service import gerar_menu_inicial, filtrar_projetos_por_escolhas, gerar_menu_por_definicao
from services.state_service import atualizar_ultima_atividade
from services.materials_service import gerar_menu_materia_prima, buscar_materia_prima, filtrar_mp_por_escolhas, carregar_tabela_mp
from services.formula_service import calcular_pecas
from services.pedidos_service import salvar_pedido
from services.global_state import global_state

df_clientes = ClienteCache.carregar_clientes()

def gerenciar_mensagem_recebida(contato, texto):
    """
    Processa mensagens recebidas e decide o fluxo com base no estado do usuário.
    """
    logger.info(f"📩 Mensagem recebida - contato: {contato}, texto: {texto}")

    # ✅ Atualiza o tempo de atividade do usuário
    atualizar_ultima_atividade(contato)

    # ✅ Restaurar estado caso o usuário estivesse inativo
    status = global_state.status_usuario.get(contato, "inicial")
    if status.startswith("inativo_") or status.startswith("aviso_enviado_"):
        logger.info(f"⏳ Retomando estado anterior para {contato}. Estado original: {status}")
        status = status.replace("inativo_", "").replace("aviso_enviado_", "")  # Remove ambos os prefixos
        global_state.status_usuario[contato] = status  # ✅ Corrigido para atualizar corretamente

    nome_cliente = global_state.informacoes_cliente.get(contato, {}).get("nome_cliente", "Cliente").strip()

    # ✅ Fluxo baseado no status atualizado
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
    elif status == "definicao_4":
        processar_menu_dinamico_produto(contato, texto, nome_cliente, "definicao_4")
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
    elif status == "aguardando_resposta_adicionar":
        processar_resposta_adicionar_pecas(contato, texto)
    elif status == "aguardando_nome_pedido":  
        processar_resposta_finalizou(contato, texto)
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
        chaves_relevantes = ["definicao_1", "definicao_2", "definicao_3", "definicao_4", "medida_final"]
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

        # **🔹 Adicionando `definicao_4` na lista de verificações**
        definicoes_ordenadas = ["definicao_2", "definicao_3", "definicao_4"]
        proxima_definicao = None

        for definicao in definicoes_ordenadas:
            if definicao not in informacoes_cliente:
                # Passar o DataFrame e os filtros corretamente
                opcoes_proxima_definicao = gerar_menu_por_definicao(pd.DataFrame(projetos), definicao, dados_para_filtrar)
                if opcoes_proxima_definicao:
                    proxima_definicao = definicao
                    break

        if proxima_definicao:
            # Gera o próximo menu
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
    Se houver mais de um projeto ainda disponível, apresentar um menu final para seleção.
    """
    if not projetos:
        enviar_mensagem(contato, "❌ Não foi possível encontrar um projeto válido. Tente novamente.")
        salvar_mensagem_em_arquivo(contato, nome_cliente, "Bot: Finalização sem projeto válido.")
        finalizar_conversa(contato, nome_cliente)
        return

    if len(projetos) == 1:
        # ✅ Apenas um projeto disponível → Selecionar automaticamente
        projeto_escolhido = projetos[0]
        descricao = projeto_escolhido.get("descricao_projeto", "Projeto não descrito.")

        enviar_mensagem(contato, f"✅ Projeto selecionado automaticamente: {descricao}.")
        salvar_mensagem_em_arquivo(contato, nome_cliente, f"Bot: Projeto finalizado automaticamente: {descricao}.")

        processar_projeto(contato, nome_cliente, projeto_escolhido)
    else:
        # ✅ Mais de um projeto disponível → Perguntar ao usuário qual deseja
        opcoes_projetos = [p["descricao_projeto"] for p in projetos]
        apresentar_menu(contato, nome_cliente, opcoes_projetos, "escolha_final_projeto")


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
    - Garante que a espessura seja definida antes de seguir.
    - Se o projeto for "fixo", pergunta o beneficiamento.
    - Se o projeto for qualquer outro, o beneficiamento é automaticamente "TEMPERADO".
    """
    try:
        escolha = int(texto) - 1  # Ajustar índice para 0-based
        opcoes = global_state.ultimo_menu_usuario.get(contato)

        if not opcoes or escolha < 0 or escolha >= len(opcoes):
            raise ValueError("Opção inválida.")

        # Captura a escolha do usuário
        escolha_usuario = opcoes[escolha]
        salvar_mensagem_em_arquivo(contato, "Bot", f"Bot: Usuário escolheu: {escolha_usuario}.")
        informacoes_cliente = global_state.informacoes_cliente.setdefault(contato, {})
        informacoes_cliente[estado_atual] = escolha_usuario

        # ✅ Se a escolha foi o beneficiamento, FINALIZA a seleção e segue o fluxo
        if estado_atual == "beneficiamento":
            informacoes_cliente["beneficiamento"] = escolha_usuario
            logger.info(f"✅ Beneficiamento escolhido: {escolha_usuario}")
            finalizar_selecao_mp(contato, informacoes_cliente)
            return

        # ✅ Garantir que a espessura foi escolhida antes de prosseguir
        cor_mp = informacoes_cliente.get("cor_materia_prima")
        espessura_mp = informacoes_cliente.get("espessura_materia_prima")

        if not espessura_mp:
            df_mp = carregar_tabela_mp()
            opcoes_espessura = df_mp[df_mp["cor_materia_prima"] == cor_mp]["espessura_materia_prima"].dropna().unique().tolist()

            if opcoes_espessura:
                apresentar_menu_mp(contato, opcoes_espessura, "espessura_materia_prima")
                global_state.status_usuario[contato] = "espessura_materia_prima"
                return

        # 🔹 Verifica se o projeto é "fixo" para perguntar beneficiamento
        projeto = informacoes_cliente.get("projeto_escolhido", {})
        nome_projeto = projeto.get("descricao_projeto", "").strip().lower()

        logger.debug(f"🔎 Nome do projeto registrado: {nome_projeto}")

        if "fixo" in nome_projeto:
            # Se for "fixo", perguntar beneficiamento
            df_mp = carregar_tabela_mp()
            beneficiamentos_disponiveis = (
                df_mp[
                    (df_mp["cor_materia_prima"] == cor_mp) &
                    (df_mp["espessura_materia_prima"] == espessura_mp)
                ]["beneficiamento"]
                .dropna()
                .unique()
                .tolist()
            )

            logger.debug(f"📋 Beneficiamentos disponíveis: {beneficiamentos_disponiveis}")

            if beneficiamentos_disponiveis:
                apresentar_menu_mp(contato, beneficiamentos_disponiveis, "beneficiamento")
                global_state.status_usuario[contato] = "beneficiamento"
                return

        # 🚀 Se NÃO for fixo, define beneficiamento automaticamente como "TEMPERADO"
        informacoes_cliente["beneficiamento"] = "TEMPERADO"
        logger.info(f"⚙️ Beneficiamento definido automaticamente como TEMPERADO para {contato}")

        # Finaliza a seleção de matéria-prima e segue o fluxo
        finalizar_selecao_mp(contato, informacoes_cliente)

    except ValueError:
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
    Processa a quantidade informada e ajusta as peças calculadas.
    """
    try:
        quantidade = int(texto)
        dados_usuario = global_state.informacoes_cliente.get(contato, {})
        projeto = dados_usuario["projeto_escolhido"]
        descricao_projeto = projeto.get("descricao_projeto", "Projeto sem descrição.")
        id_formula = projeto.get("id_formula", 0)

        if id_formula == 0:
            enviar_mensagem(contato, "❌ Erro interno: Fórmula não encontrada para este projeto.")
            return

        # Recuperar peças calculadas com base na fórmula
        altura = dados_usuario.get("altura", 0)
        largura = dados_usuario.get("largura", 0)
        pecas = calcular_pecas(id_formula, altura, largura)

        if not pecas:
            enviar_mensagem(contato, "❌ Erro ao calcular as peças. Tente novamente.")
            return

        # Ajustar a quantidade de cada peça multiplicando pelo valor informado
        pecas_multiplicadas = []
        for peca in pecas:
            pecas_multiplicadas.append({
                "nome_peca": peca["nome_peca"],
                "quantidade": peca["quantidade"] * quantidade,  # Multiplica pela quantidade total
                "dimensoes": peca["dimensoes"]
            })

        # Salvar no estado global
        dados_usuario["pecas"] = pecas_multiplicadas
        dados_usuario["quantidade_total"] = quantidade  # Salva a quantidade total no estado global
        global_state.informacoes_cliente[contato] = dados_usuario

        # Exibir resumo das peças calculadas
        msg_pecas = f"📦 Para {quantidade} unidades do item {descricao_projeto}, você precisará de:\n"
        for peca in pecas_multiplicadas:
            msg_pecas += f"\n{peca['quantidade']}x {peca['nome_peca']}: {peca['dimensoes'][0]}mm x {peca['dimensoes'][1]}mm"

        enviar_mensagem(contato, msg_pecas)
        salvar_mensagem_em_arquivo(contato, descricao_projeto, msg_pecas)

        # Passa para salvar as peças no pedido
        adicionar_pecas_pedido(contato, dados_usuario.get("nome_cliente", "Cliente"))

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


def adicionar_pecas_pedido(contato, nome_cliente):
    """
    Acumula os pedidos no estado global e garante que o id_cliente seja correto.
    """
    dados_usuario = global_state.informacoes_cliente.get(contato, {})

    # Buscar o cliente pelo telefone
    cliente_info = ClienteCache.buscar_cliente_por_telefone(contato)
    if not cliente_info:
        logger.error(f"❌ Cliente não encontrado para o número {contato}.")
        enviar_mensagem(contato, "❌ Erro interno: Cliente não encontrado. Tente novamente.")
        return

    id_cliente = cliente_info["id_cliente"]
    nome_cliente = cliente_info["nome_cliente"]

    # Atualizar o estado do cliente com as informações corretas
    dados_usuario["id_cliente"] = id_cliente
    dados_usuario["nome_cliente"] = nome_cliente

    # Continuar o processamento normalmente
    pedidos_acumulados = dados_usuario.get("pedidos", [])
    id_materia_prima, valor_mp_m2 = buscar_materia_prima(dados_usuario)

    if not id_materia_prima or not valor_mp_m2:
        enviar_mensagem(contato, "❌ Erro: Não foi possível identificar a matéria-prima. Tente novamente.")
        return

    pecas_calculadas = dados_usuario.get("pecas", [])
    novo_pedido = {
        "id_cliente": id_cliente,
        "nome_cliente": nome_cliente,  # Nome atualizado
        "id_projeto": dados_usuario.get("projeto_escolhido", {}).get("id_projeto"),
        "id_materia_prima": id_materia_prima,
        "valor_mp_m2": valor_mp_m2,
        "pecas": pecas_calculadas,
        "altura_vao": dados_usuario.get("altura"),
        "largura_vao": dados_usuario.get("largura"),
    }

    pedidos_acumulados.append(novo_pedido)
    dados_usuario["pedidos"] = pedidos_acumulados
    global_state.informacoes_cliente[contato] = dados_usuario

    perguntar_se_finalizou(contato)


def processar_resposta_adicionar_pecas(contato, texto):
    """
    Processa a resposta do usuário sobre adicionar mais peças ou finalizar o pedido.
    Agora mantém os pedidos acumulados corretamente.
    """
    texto = texto.strip()

    if texto == "1":  # Cliente quer adicionar mais peças
        enviar_mensagem(contato, "🔄 Redirecionando para adicionar mais peças...")

        # ✅ Manter os pedidos já feitos e limpar apenas as informações do novo projeto
        dados_usuario = global_state.informacoes_cliente.get(contato, {})
        pedidos_acumulados = dados_usuario.get("pedidos", [])

        global_state.informacoes_cliente[contato] = {"pedidos": pedidos_acumulados}  # Mantém os pedidos
        perguntar_tipo_medida(contato, global_state.informacoes_cliente[contato].get("nome_cliente", "Cliente"))

    elif texto == "2":  # Cliente quer finalizar o pedido
        enviar_mensagem(contato, "✅ Antes de finalizar, qual nome deseja dar para este pedido?")
        global_state.status_usuario[contato] = "aguardando_nome_pedido"

    else:
        enviar_mensagem(contato, "❌ Opção inválida. Escolha:\n1️⃣ Adicionar mais peças\n2️⃣ Finalizar pedido.")


def perguntar_se_finalizou(contato):
    """
    Pergunta ao usuário se deseja continuar adicionando mais peças ou finalizar o pedido.
    """
    enviar_mensagem(contato, "Deseja adicionar mais peças ao pedido?")
    enviar_mensagem(contato, "1️⃣ Sim\n2️⃣ Não, finalizar pedido.")

    # Atualiza o estado do usuário para esperar a resposta
    global_state.status_usuario[contato] = "aguardando_resposta_adicionar"

def processar_resposta_finalizou(contato, texto):
    """
    Finaliza o pedido e salva TODOS os projetos adicionados na tabela.
    """
    # Obter o estado do usuário
    dados_usuario = global_state.informacoes_cliente.get(contato, {})
    nome_pedido = str(texto.strip())

    if not nome_pedido:
        enviar_mensagem(contato, "❌ Nome inválido. Por favor, digite um nome para o pedido.")
        return

    # Verificar se há pedidos acumulados
    pedidos_acumulados = dados_usuario.get("pedidos", [])
    if not pedidos_acumulados:
        enviar_mensagem(contato, "❌ Nenhum pedido encontrado para salvar. Reinicie o processo.")
        return

    # Garantir que todos os pedidos usem o mesmo id_cliente
    id_cliente = dados_usuario.get("id_cliente")  # Sempre pegue do estado global
    if not id_cliente:
        logger.error(f"❌ ID do cliente ausente no estado global para {contato}.")
        enviar_mensagem(contato, "❌ Erro interno: ID do cliente não encontrado.")
        return

    # Salvar todos os pedidos acumulados na planilha
    for pedido in pedidos_acumulados:
        salvar_pedido(
            id_cliente=id_cliente,
            nome_cliente=pedido.get("nome_cliente", "Cliente Desconhecido"),
            id_projeto=pedido.get("id_projeto"),
            id_materia_prima=pedido.get("id_materia_prima"),
            altura_vao=pedido.get("altura_vao"),
            largura_vao=pedido.get("largura_vao"),
            pecas_calculadas=pedido.get("pecas", []),
            valor_mp_m2=pedido.get("valor_mp_m2", 0.0),
            nome_pedido=nome_pedido
        )

    # Notificar o cliente e registrar no log
    enviar_mensagem(contato, f"✅ Pedido **{nome_pedido}** finalizado com sucesso! Obrigado pela compra. 😊")
    salvar_mensagem_em_arquivo(contato, "Bot", f"Pedido {nome_pedido} finalizado pelo usuário.")

    # Limpar os dados do usuário após salvar os pedidos
    global_state.limpar_dados_usuario(contato)


def finalizar_conversa(contato, nome_cliente):
    """
    Finaliza a conversa e limpa os dados do usuário do estado global.
    """
    enviar_mensagem(contato, "Obrigado! Caso precise de algo, estamos à disposição! 😊")
    salvar_mensagem_em_arquivo(contato, nome_cliente, "Bot: Conversa encerrada.")
    global_state.limpar_dados_usuario(contato)
    