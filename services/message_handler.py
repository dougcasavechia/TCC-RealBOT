from services.client_service import buscar_cliente_por_telefone
from services.message_service import enviar_mensagem, salvar_mensagem_em_arquivo
from services.product_service import carregar_tabela_tipo_produto
from services.global_state import status_usuario, ultima_interacao_usuario, ultimo_menu_usuario, informacoes_cliente
from services.formula_service import obter_formula_por_id
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
    elif status == "coletando_quantidade":
        processar_quantidade(contato, texto, nome_cliente)  # Adiciona processamento da quantidade
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


def processar_medida_vao_final(contato, texto, nome_cliente):
    """
    Processa a escolha entre medida final ou medida de vão.
    """
    if texto == "1":  # Medida Final
        enviar_mensagem(contato, "Você escolheu informar a medida final.")
        salvar_mensagem_em_arquivo(contato, nome_cliente, "Bot: Usuário escolheu medida final.")

        # Salvar a escolha no dicionário do cliente
        informacoes_cliente[contato]["medida_final"] = 1  # 1 para medida final

        apresentar_menu_produtos(contato, nome_cliente)
    elif texto == "2":  # Medida de Vão
        enviar_mensagem(contato, "Você escolheu informar a medida de vão.")
        salvar_mensagem_em_arquivo(contato, nome_cliente, "Bot: Usuário escolheu medida de vão.")

        # Salvar a escolha no dicionário do cliente
        informacoes_cliente[contato]["medida_final"] = 0  # 0 para medida de vão

        apresentar_menu_produtos(contato, nome_cliente)
    else:
        enviar_mensagem(contato, "Opção inválida. Por favor, escolha novamente:")
        menu = "1. Medida final\n2. Medida de vão"
        enviar_mensagem(contato, menu)
        ultimo_menu_usuario[contato] = menu



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
    projetos = informacoes_cliente[contato].get("projetos", [])
    if not projetos:
        enviar_mensagem(contato, "Não conseguimos recuperar as opções anteriores. Reiniciaremos sua interação.")
        iniciar_conversa(contato, nome_cliente)
        return

    try:
        escolha = int(texto) - 1
        if 0 <= escolha < len(projetos):
            projeto_selecionado = projetos[escolha]

            # Salvar o ID da fórmula no dicionário do cliente
            informacoes_cliente[contato]["id_formula"] = projeto_selecionado.get("id_formula")
            print(f"[DEBUG] ID da fórmula salvo: {informacoes_cliente[contato]['id_formula']}")  # Adicionado para debug

            enviar_mensagem(contato, f"Você escolheu o projeto: {projeto_selecionado['descricao_projeto']}.")
            salvar_mensagem_em_arquivo(contato, nome_cliente, f"Bot: Projeto escolhido: {projeto_selecionado['descricao_projeto']}.")

            # Solicitar altura como próximo passo
            tipo_medida = "final" if informacoes_cliente[contato].get("medida_final") else "vão"
            solicitar_altura(contato, nome_cliente, tipo_medida)
        else:
            raise ValueError("Opção inválida.")
    except (ValueError, IndexError):
        enviar_mensagem(contato, "Desculpe, opção inválida. Escolha uma das opções abaixo:")
        enviar_mensagem(contato, ultimo_menu_usuario.get(contato, ""))
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
    from services.product_service import filtrar_projetos

    projetos = filtrar_projetos(id_tipo_produto, medida_final)

    if not projetos:
        enviar_mensagem(contato, "Não há projetos disponíveis para sua escolha. Tente novamente mais tarde.")
        salvar_mensagem_em_arquivo(contato, nome_cliente, "Bot: Nenhum projeto disponível.")
        finalizar_conversa(contato, nome_cliente)
        return

    # Criar o menu com apenas as descrições dos projetos
    menu = "\n".join([f"{i + 1}. {projeto['descricao_projeto']}" for i, projeto in enumerate(projetos)])
    enviar_mensagem(contato, "Escolha o projeto desejado:")
    enviar_mensagem(contato, menu)

    # Salvar os projetos filtrados em `informacoes_cliente`
    informacoes_cliente[contato]["projetos"] = projetos
    status_usuario[contato] = "escolhendo_projeto"
    ultimo_menu_usuario[contato] = menu
    salvar_mensagem_em_arquivo(contato, nome_cliente, "Bot: Apresentou menu de projetos.")


def repetir_menu(contato, nome_cliente):
    """
    Reenvia a solicitação ou o menu apropriado com base no estado atual do usuário.
    """
    status = status_usuario.get(contato)
    print(f"[DEBUG] Estado atual: {status}")

    if status == "coletando_altura":
        tipo_medida = "final" if informacoes_cliente[contato].get("medida_final") else "vão"
        enviar_mensagem(contato, f"Você está inativo. Por favor, informe a medida da altura em milímetros (mm) ({tipo_medida}):")
        salvar_mensagem_em_arquivo(contato, nome_cliente, "Bot: Repetiu solicitação de altura.")
    elif status == "coletando_largura":
        tipo_medida = "final" if informacoes_cliente[contato].get("medida_final") else "vão"
        altura = informacoes_cliente[contato].get("altura", "não registrada")
        enviar_mensagem(contato, f"Você está inativo. Altura registrada: {altura} mm. Informe a medida da largura em milímetros (mm) ({tipo_medida}):")
        salvar_mensagem_em_arquivo(contato, nome_cliente, "Bot: Repetiu solicitação de largura.")
    elif status == "coletando_quantidade":
        enviar_mensagem(contato, "Você está inativo. Quantas unidades você deseja para este projeto?")
        salvar_mensagem_em_arquivo(contato, nome_cliente, "Bot: Repetiu solicitação de quantidade de unidades.")
    else:
        # Caso o estado não seja altura, largura ou quantidade, reenvia o último menu
        ultimo_menu = ultimo_menu_usuario.get(contato)
        if ultimo_menu:
            enviar_mensagem(contato, "Você está inativo. Escolha uma das opções abaixo:")
            enviar_mensagem(contato, ultimo_menu)
            salvar_mensagem_em_arquivo(contato, nome_cliente, "Bot: Repetiu o menu apropriado.")
        else:
            # Reinicia a interação se não houver estado conhecido
            enviar_mensagem(contato, "Conversa encerrada por inatividade. Para reiniciar, envie qualquer mensagem.")
            salvar_mensagem_em_arquivo(contato, nome_cliente, "Bot: Conversa encerrada por inatividade.")
            limpar_dados_usuario(contato)




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
    # Determinar o tipo de medida baseado no valor salvo
    tipo_medida = "final" if informacoes_cliente[contato].get("medida_final") == 1 else "vão"

    enviar_mensagem(contato, f"Por favor, informe a medida da altura em milímetros (mm) ({tipo_medida}):")
    status_usuario[contato] = "coletando_altura"
    salvar_mensagem_em_arquivo(contato, nome_cliente, f"Bot: Solicitou medida da altura ({tipo_medida}).")



def solicitar_largura(contato, nome_cliente, tipo_medida, altura):
    """
    Solicita ao cliente a medida da largura.
    """
    enviar_mensagem(contato, f"Altura registrada: {altura} mm.")
    enviar_mensagem(contato, f"Agora, informe a medida da largura em milímetros (mm) ({tipo_medida}):")
    status_usuario[contato] = "coletando_largura"
    salvar_mensagem_em_arquivo(contato, nome_cliente, f"Bot: Solicitou medida da largura ({tipo_medida}).")


def encerrar_fluxo(contato, nome_cliente, altura, largura):
    """
    Finaliza o fluxo após coletar as medidas.
    """
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

        # Salvar a altura no dicionário do cliente
        informacoes_cliente[contato]["altura"] = altura

        # Obter o tipo de medida (final ou vão) para exibir ao cliente
        tipo_medida = "final" if informacoes_cliente[contato].get("medida_final") else "vão"

        # Solicitar a largura
        solicitar_largura(contato, nome_cliente, tipo_medida, altura)

    except ValueError:
        enviar_mensagem(contato, "Altura inválida. Por favor, informe a medida da altura como um número inteiro positivo em milímetros (mm).")


def processar_largura(contato, texto, nome_cliente):
    """
    Processa a medida da largura fornecida pelo cliente.
    """
    try:
        largura = int(texto)  # Tentar converter a entrada para inteiro
        if largura <= 0:
            raise ValueError("A medida deve ser um número positivo.")

        # Salvar a largura no dicionário do cliente
        informacoes_cliente[contato]["largura"] = largura

        # Verificar se a altura já está registrada
        altura = informacoes_cliente[contato].get("altura")
        if not altura:
            enviar_mensagem(contato, "Erro: Altura não encontrada. Reiniciaremos sua interação.")
            iniciar_conversa(contato, nome_cliente)
            return

        # Ambas as medidas estão disponíveis; prosseguir com os cálculos
        processar_dimensoes_projeto(contato, nome_cliente)
    except ValueError:
        enviar_mensagem(contato, "Largura inválida. Por favor, informe a medida da largura como um número inteiro positivo em milímetros (mm).")


def processar_dimensoes_projeto(contato, nome_cliente):
    """
    Processa as dimensões do projeto (altura e largura) e realiza os cálculos.
    """
    altura = informacoes_cliente[contato]["altura"]
    largura = informacoes_cliente[contato]["largura"]

    # Obter o ID da fórmula associado
    id_formula = informacoes_cliente[contato].get("id_formula")
    print("#############################")
    print(id_formula)
    print("#############################")
    if not id_formula:
        enviar_mensagem(contato, "Erro: Nenhuma fórmula associada ao projeto. Reiniciaremos sua interação.")
        iniciar_conversa(contato, nome_cliente)
        return

    # Obter as fórmulas associadas ao ID
    formulas = obter_formula_por_id(id_formula)
    print("#############################")
    print(formulas)
    print("#############################")

    if not formulas:
        enviar_mensagem(contato, f"Erro: Fórmulas para o ID '{id_formula}' não encontradas. Reiniciaremos sua interação.")
        iniciar_conversa(contato, nome_cliente)
        return

    # Debug: Verificar fórmulas retornadas
    print(f"[DEBUG] Fórmulas retornadas para ID {id_formula}: {formulas}")

    # Obter o tipo de medida (medida_final ou medida_vão)
    medida_final = informacoes_cliente[contato].get("medida_final", 1)  # Default: 1 (medida final)

    # Garantir que as chaves 'fixa' e 'movel' existam
    dimensoes_fixas = formulas.get("fixa", [])
    dimensoes_moveis = formulas.get("movel", [])

    # Debug: Verificar dimensões fixas e móveis
    print(f"[DEBUG] Dimensões fixas: {dimensoes_fixas}")
    print(f"[DEBUG] Dimensões móveis: {dimensoes_moveis}")

    try:
        if medida_final == 1:  # Medida Final
            dimensoes_fixas_calculadas = [
                {"quantidade": item["quantidade"], "dimensao": item["calculo"](altura, largura)}
                for item in dimensoes_fixas
            ]

            dimensoes_moveis_calculadas = [
                {"quantidade": item["quantidade"], "dimensao": item["calculo"](altura, largura)}
                for item in dimensoes_moveis
            ]
        else:  # Medida de Vão
            dimensoes_fixas_calculadas = [
                {"quantidade": item["quantidade"], "dimensao": item["calculo"](altura, largura)}
                for item in dimensoes_fixas
            ]

            dimensoes_moveis_calculadas = [
                {"quantidade": item["quantidade"], "dimensao": item["calculo"](altura, largura)}
                for item in dimensoes_moveis
            ]

    except KeyError as e:
        print(f"[ERROR] Chave ausente durante o cálculo: {e}")
        enviar_mensagem(contato, "Erro interno: Uma fórmula necessária está ausente. Reiniciaremos sua interação.")
        iniciar_conversa(contato, nome_cliente)
        return
    except Exception as e:
        print(f"[ERROR] Erro durante o cálculo: {e}")
        enviar_mensagem(contato, "Erro ao calcular as dimensões do projeto. Reiniciaremos sua interação.")
        iniciar_conversa(contato, nome_cliente)
        return

    # Debug: Verificar dimensões calculadas
    print(f"[DEBUG] Dimensões fixas calculadas: {dimensoes_fixas_calculadas}")
    print(f"[DEBUG] Dimensões móveis calculadas: {dimensoes_moveis_calculadas}")

    # Salvar dimensões no dicionário do cliente
    informacoes_cliente[contato]["dimensoes"] = {
        "fixa": dimensoes_fixas_calculadas,
        "movel": dimensoes_moveis_calculadas
    }

    # Exibir os cálculos ao usuário
    enviar_mensagem(contato, f"Projeto: {formulas['nome']}")
    enviar_mensagem(contato, f"Tamanho vão: {largura}x{altura}")

    if dimensoes_fixas_calculadas:
        for item in dimensoes_fixas_calculadas:
            enviar_mensagem(contato, f"{item['quantidade']} und (fixa) - {item['dimensao'][0]} x {item['dimensao'][1]}")
    else:
        enviar_mensagem(contato, "Nenhuma peça fixa encontrada para este projeto.")

    if dimensoes_moveis_calculadas:
        for item in dimensoes_moveis_calculadas:
            enviar_mensagem(contato, f"{item['quantidade']} und (móvel) - {item['dimensao'][0]} x {item['dimensao'][1]}")
    else:
        enviar_mensagem(contato, "Nenhuma peça móvel encontrada para este projeto.")

    # Perguntar a quantidade de unidades
    solicitar_quantidade(contato, nome_cliente)


def solicitar_quantidade(contato, nome_cliente):
    """
    Pergunta ao usuário quantas unidades do projeto ele deseja.
    """
    enviar_mensagem(contato, "Quantas unidades você deseja para este projeto?")
    status_usuario[contato] = "coletando_quantidade"
    salvar_mensagem_em_arquivo(contato, nome_cliente, "Bot: Solicitou quantidade de unidades.")


def processar_quantidade(contato, texto, nome_cliente):
    """
    Processa o número de unidades fornecido pelo cliente e finaliza o fluxo.
    """
    try:
        quantidade = int(texto)
        if quantidade <= 0:
            raise ValueError("A quantidade deve ser um número positivo.")

        dimensoes = informacoes_cliente[contato].get("dimensoes")
        if not dimensoes:
            enviar_mensagem(contato, "Erro: Dimensões não calculadas. Reiniciaremos sua interação.")
            iniciar_conversa(contato, nome_cliente)
            return

        enviar_mensagem(contato, f"Resumo do projeto:")
        enviar_mensagem(contato, f"Tamanho vão: {informacoes_cliente[contato]['largura']}x{informacoes_cliente[contato]['altura']}")

        for i, item in enumerate(dimensoes["fixa"], start=1):
            enviar_mensagem(contato, f"{item['quantidade'] * quantidade} und (fixa) - {item['dimensao'][0]} x {item['dimensao'][1]}")

        for i, item in enumerate(dimensoes["movel"], start=1):
            enviar_mensagem(contato, f"{item['quantidade'] * quantidade} und (móvel) - {item['dimensao'][0]} x {item['dimensao'][1]}")

        # Finalizar o fluxo
        encerrar_fluxo(contato, nome_cliente, informacoes_cliente[contato]["altura"], informacoes_cliente[contato]["largura"])
    except ValueError:
        enviar_mensagem(contato, "Quantidade inválida. Por favor, informe um número inteiro positivo.")


