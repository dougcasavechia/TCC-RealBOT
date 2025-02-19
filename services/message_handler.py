import pandas as pd
import os
from logger import logger
from services.client_service import ClienteCache
from services.message_service import enviar_mensagem, salvar_mensagem_em_arquivo
from services.product_service import gerar_menu_inicial, filtrar_projetos_por_escolhas, gerar_menu_por_definicao, carregar_tabela_projetos
from services.state_service import atualizar_ultima_atividade
from services.materials_service import gerar_menu_materia_prima, buscar_materia_prima, carregar_tabela_mp
# from services.materials_service import filtrar_mp_por_escolhas
from services.formula_service import calcular_pecas
from services.pedidos_service import calcular_valores_pecas, obter_nome_projeto, obter_nome_materia_prima, salvar_pedido, atualizar_status_pedido, visualizar_orcamentos
from services.global_state import global_state
from config import OUTPUT_DIR

df_clientes = ClienteCache.carregar_clientes()
df_projetos = carregar_tabela_projetos()
df_mp = carregar_tabela_mp()

PEDIDOS_FILE_PATH = os.path.join(OUTPUT_DIR, "pedidos.xlsx")

def gerenciar_mensagem_recebida(contato, texto):
    """
    Processa mensagens recebidas e decide o fluxo com base no estado do usuário.
    """
    logger.info(f"📩 Mensagem recebida - contato: {contato}, texto: {texto}")

    # ✅ Verificar se o número está cadastrado
    cliente_info = ClienteCache.buscar_cliente_por_telefone(contato)
    
    if not cliente_info:
        logger.warning(f"❌ Número {contato} não cadastrado. Encerrando fluxo.")
        enviar_mensagem(contato, "⚠️ Olá! Para continuar, é necessário realizar o cadastro. Procure um vendedor para se cadastrar. 📞")
        return  # Encerra o fluxo imediatamente

    nome_cliente = cliente_info["nome_cliente"]  # Obtendo nome do cliente
    atualizar_ultima_atividade(contato)

    # ✅ Restaurar estado caso o usuário estivesse inativo
    status = global_state.status_usuario.get(contato, "inicial")
    if status.startswith("inativo_") or status.startswith("aviso_enviado_"):
        logger.info(f"⏳ Retomando estado anterior para {contato}. Estado original: {status}")
        status = status.replace("inativo_", "").replace("aviso_enviado_", "")
        global_state.status_usuario[contato] = status  

    # ✅ Se o usuário estiver no estado "inicial", exibe o menu inicial
    if status == "inicial":
        mostrar_menu_inicial(contato, nome_cliente)
    elif status == "menu_inicial":
        processar_menu_inicial(contato, texto, nome_cliente)
    elif status == "aguardando_confirmacao_pedido":
        processar_confirmacao_pedido(contato, texto)
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
    elif status == "aguardando_autorizacao":
        processar_resposta_autorizacao(contato, texto)
    elif status == "escolhendo_orcamento":
        processar_escolha_orcamento(contato, texto)
    elif status == "gerenciando_orcamento":
        processar_resposta_autorizacao(contato, texto)  # Reutilizando a mesma lógica
    else:
        repetir_menu(contato, nome_cliente)


def mostrar_menu_inicial(contato, nome_cliente):
    """
    Apresenta o menu inicial para o usuário escolher entre fazer um orçamento ou visualizar orçamentos existentes.
    """
    menu = ["Fazer orçamento", "Visualizar orçamentos"]
    enviar_mensagem(contato, f"Olá {nome_cliente}, o que deseja?")
    enviar_mensagem(contato, "\n".join([f"{i + 1}. {opcao}" for i, opcao in enumerate(menu)]))

    global_state.status_usuario[contato] = "menu_inicial"
    global_state.ultimo_menu_usuario[contato] = menu


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

def processar_menu_inicial(contato, texto, nome_cliente):
    """
    Processa a escolha do usuário no menu inicial.
    """
    try:
        escolha = int(texto)
        if escolha == 1:
            # Usuário quer fazer um orçamento (segue fluxo normal)
            perguntar_tipo_medida(contato, nome_cliente)
        elif escolha == 2:
            # Usuário quer visualizar orçamentos
            visualizar_orcamentos(contato, nome_cliente)
        else:
            raise ValueError("Opção inválida.")
    except ValueError:
        enviar_mensagem(contato, "❌ Opção inválida. Escolha entre:\n1️⃣ Fazer orçamento\n2️⃣ Visualizar orçamentos")


def processar_escolha_orcamento(contato, texto):
    """
    Exibe o resumo do orçamento escolhido antes de oferecer as opções de autorizar produção, manter orçamento ou cancelar.
    """
    try:
        opcoes = global_state.ultimo_menu_usuario.get(contato, [])
        escolha = int(texto) - 1

        if escolha < 0 or escolha >= len(opcoes):
            raise ValueError("Opção inválida.")

        id_pedido, nome_pedido = opcoes[escolha]

        # 🔹 Carregar todas as peças do pedido selecionado
        df_pedidos = pd.read_excel(PEDIDOS_FILE_PATH)
        df_pedido = df_pedidos[df_pedidos["id_pedido"] == id_pedido]

        if df_pedido.empty:
            enviar_mensagem(contato, "❌ Erro ao carregar o pedido. Tente novamente.")
            return

        # 🔹 Construir resumo do pedido
        resumo_pedido = f"📝 *Resumo do Pedido: {nome_pedido}*\n"
        total_geral = 0
        total_m2 = 0
        total_pecas = 0

        for _, peca in df_pedido.iterrows():
            resumo_pedido += f"*►►►►►►►►►◄◄◄◄◄◄◄◄◄*\n"
            resumo_pedido += f"📌 *Projeto:* {peca['descricao_projeto']}\n"
            resumo_pedido += f"🔹 *Matéria-prima:* {peca['descricao_materia_prima']}\n"
            resumo_pedido += f"💰 *Valor por m²:* R${peca['valor_mp_m2']:.2f}\n"
            resumo_pedido += f"🏢 *Quantidade de Projetos:* {df_pedido['id_pedido'].nunique()}\n\n"
            resumo_pedido += f"🔸 {peca['quantidade']}x {peca['descricao_peca']} - {peca['altura_peca']}mm x {peca['largura_peca']}mm\n"
            resumo_pedido += f"📏 Área: {peca['area_m2']}m² | 💰 Valor: R${peca['valor_total']:.2f}\n"
            total_m2 += peca["area_m2"]
            total_pecas += peca["quantidade"]
            total_geral += peca["valor_total"]

        resumo_pedido += f"*=========================*\n"
        resumo_pedido += f"📏 *Área total:* {total_m2:.2f}m²\n"
        resumo_pedido += f"🏢 *Quantidade total de peças:* {total_pecas}\n"
        resumo_pedido += f"💰 *Valor total do pedido:* R${total_geral:.2f}\n"
        resumo_pedido += f"*=========================*\n"

        enviar_mensagem(contato, resumo_pedido)

        # 🔹 Perguntar se deseja autorizar produção, manter orçamento ou cancelar
        enviar_mensagem(contato, "📌 O que deseja fazer com esse orçamento?")
        enviar_mensagem(contato, "1️⃣ Sim, autorizar produção\n2️⃣ Não, manter como orçamento\n3️⃣ Cancelar pedido")

        global_state.status_usuario[contato] = "gerenciando_orcamento"
        global_state.informacoes_cliente[contato]["id_pedido"] = id_pedido
        global_state.informacoes_cliente[contato]["nome_pedido"] = nome_pedido

    except (ValueError, IndexError):
        enviar_mensagem(contato, "❌ Opção inválida. Escolha um número da lista.")


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
    Define altura e largura automaticamente para peças padrão.
    Se for um projeto que requer entrada do usuário, pergunta normalmente.
    """
    global_state.informacoes_cliente[contato]["projeto_escolhido"] = projeto

    descricao_projeto = projeto.get("descricao_projeto", "").lower()
    
    # Definir altura automaticamente apenas para PEÇAS PADRÃO
    if "box padrão" in descricao_projeto:
        altura = 1845 if "fixo" in descricao_projeto else 1880
    elif "janela padrão" in descricao_projeto:
        altura = 938 if "fixo" in descricao_projeto else 975
    else:
        altura = None  # Outros tipos de projetos NÃO têm altura automática

    # Definir largura automática apenas se for PEÇA PADRÃO
    largura = None
    if "box padrão" in descricao_projeto or "janela padrão" in descricao_projeto:
        largura_opcao = global_state.informacoes_cliente[contato].get("definicao_3")  # A largura vem dessa definição
        if largura_opcao and isinstance(largura_opcao, str):
            numeros_encontrados = [int(s) for s in largura_opcao.split() if s.isdigit()]
            if numeros_encontrados:
                largura = numeros_encontrados[0]  # Pegamos o primeiro número encontrado

    if altura is not None and largura is not None:
        global_state.informacoes_cliente[contato]["altura"] = altura
        global_state.informacoes_cliente[contato]["largura"] = largura

        enviar_mensagem(contato, f"✅ Medidas definidas automaticamente:\n📏 Altura: {altura} mm\n📐 Largura: {largura} mm")

        # Segue direto para a seleção de matéria-prima
        opcoes_mp = gerar_menu_materia_prima()
        if opcoes_mp:
            apresentar_menu_mp(contato, opcoes_mp, "cor_materia_prima")
        else:
            enviar_mensagem(contato, "❌ Nenhuma matéria-prima disponível. Tente novamente mais tarde.")
    else:
        # 🚀 Se for um projeto que exige entrada de medidas, perguntar normalmente
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
    - Se for "Peça Padrão", define automaticamente espessura 08 mm e beneficiamento TEMPERADO.
    - Se for "Fixo", "Janela" ou qualquer outro projeto que precise de espessura, primeiro pergunta a espessura.
    - Se não for "Padrão" nem "Fixo", define beneficiamento TEMPERADO e avança.
    """
    try:
        escolha = int(texto) - 1  
        opcoes = global_state.ultimo_menu_usuario.get(contato)

        if not opcoes or escolha < 0 or escolha >= len(opcoes):
            raise ValueError("Opção inválida.")

        escolha_usuario = opcoes[escolha]
        salvar_mensagem_em_arquivo(contato, "Bot", f"Bot: Usuário escolheu: {escolha_usuario}.")
        informacoes_cliente = global_state.informacoes_cliente.setdefault(contato, {})
        informacoes_cliente[estado_atual] = escolha_usuario

        cor_mp = informacoes_cliente.get("cor_materia_prima")

        # 🔹 Verifica o tipo do projeto escolhido
        projeto = informacoes_cliente.get("projeto_escolhido", {})
        definicao_1 = projeto.get("definicao_1", "").strip().lower()

        # ✅ Se for "Peça Padrão", definir automaticamente espessura e beneficiamento
        if "padrão" in definicao_1:
            informacoes_cliente["espessura_materia_prima"] = "08 mm"
            informacoes_cliente["beneficiamento"] = "TEMPERADO"
            logger.info(f"⚙️ Peça Padrão detectada. Espessura: {informacoes_cliente['espessura_materia_prima']}, Beneficiamento: {informacoes_cliente['beneficiamento']}.")

            finalizar_selecao_mp(contato, informacoes_cliente)
            return

        # ✅ Para "Fixo", "Janela" ou outros projetos, primeiro perguntar a espessura
        df_mp = carregar_tabela_mp()
        df_mp["espessura_materia_prima"] = df_mp["espessura_materia_prima"].str.strip()

        opcoes_espessura = (
            df_mp[df_mp["cor_materia_prima"].str.strip() == cor_mp]["espessura_materia_prima"]
            .dropna()
            .unique()
            .tolist()
        )

        logger.debug(f"📏 Opções de espessura para {cor_mp}: {opcoes_espessura}")

        if estado_atual == "cor_materia_prima" and opcoes_espessura:
            apresentar_menu_mp(contato, opcoes_espessura, "espessura_materia_prima")
            global_state.status_usuario[contato] = "espessura_materia_prima"
            return

        # ✅ Se a espessura já foi escolhida e for "Fixo", perguntar beneficiamento
        if "fixo" in definicao_1:
            beneficiamentos_disponiveis = (
                df_mp[
                    (df_mp["cor_materia_prima"].str.strip() == cor_mp) &
                    (df_mp["espessura_materia_prima"].str.strip() == informacoes_cliente.get("espessura_materia_prima", ""))
                ]["beneficiamento"]
                .dropna()
                .unique()
                .tolist()
            )

            logger.debug(f"📋 Beneficiamentos disponíveis para fixo: {beneficiamentos_disponiveis}")

            if estado_atual == "espessura_materia_prima" and beneficiamentos_disponiveis:
                apresentar_menu_mp(contato, beneficiamentos_disponiveis, "beneficiamento")
                global_state.status_usuario[contato] = "beneficiamento"
                return

        # ✅ Para qualquer outro projeto, definir beneficiamento TEMPERADO e avançar
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
    Antes de finalizar, gera um resumo do pedido e pede autorização para produção.
    Se o cliente confirmar, o pedido será salvo corretamente com status 'AUTORIZADO'.
    Caso contrário, será mantido como 'ORÇAMENTO' ou 'CANCELADO'.
    """
    dados_usuario = global_state.informacoes_cliente.get(contato, {})
    nome_pedido = str(texto.strip())

    if not nome_pedido:
        enviar_mensagem(contato, "❌ Nome inválido. Por favor, digite um nome para o pedido.")
        return

    pedidos_acumulados = dados_usuario.get("pedidos", [])
    if not pedidos_acumulados:
        enviar_mensagem(contato, "❌ Nenhum pedido encontrado para salvar. Reinicie o processo.")
        return

    id_cliente = dados_usuario.get("id_cliente")
    if not id_cliente:
        enviar_mensagem(contato, "❌ Erro interno: ID do cliente não encontrado.")
        return

    resumo_pedido = f"📝 *Resumo do Pedido: {nome_pedido}*\n"
    total_geral = 0
    total_m2 = 0
    total_pecas = 0

    for pedido in pedidos_acumulados:
        nome_projeto = obter_nome_projeto(pedido["id_projeto"])
        nome_mp = obter_nome_materia_prima(pedido["id_materia_prima"])
        pecas_calculadas, valor_total = calcular_valores_pecas(pedido["pecas"], pedido["valor_mp_m2"])
        total_geral += valor_total

        resumo_pedido += f"*►►►►►►►►►◄◄◄◄◄◄◄◄◄*\n"
        resumo_pedido += f"📌 *Projeto:* {nome_projeto}\n"
        resumo_pedido += f"🔹 *Matéria-prima:* {nome_mp}\n"
        resumo_pedido += f"💰 *Valor por m²:* R${pedido['valor_mp_m2']:.2f}\n"
        resumo_pedido += f"🏢 *Quantidade de Projetos:* {dados_usuario.get('quantidade_total', 1)}\n\n"

        for peca in pecas_calculadas:
            resumo_pedido += f"🔸 {peca['quantidade']}x {peca['descricao_peca']} - {peca['altura_peca']}mm x {peca['largura_peca']}mm\n"
            resumo_pedido += f"📏 Área: {peca['area_m2']}m² | 💰 Valor: R${peca['valor_total']:.2f}\n"
            total_m2 += peca["area_m2"]
            total_pecas += peca["quantidade"]

    resumo_pedido += f"*=========================*\n"
    resumo_pedido += f"📏 *Área total:* {total_m2:.2f}m²\n"
    resumo_pedido += f"🏢 *Quantidade total de peças:* {total_pecas}\n"
    resumo_pedido += f"💰 *Valor total do pedido:* R${total_geral:.2f}\n"
    resumo_pedido += f"*=========================*\n"

    # 🔹 NOVO: Perguntar sobre autorização corretamente
    enviar_mensagem(contato, resumo_pedido)
    enviar_mensagem(contato, "📌 Pedido salvo como ORÇAMENTO.")
    enviar_mensagem(contato, "Autoriza a produção do pedido acima?")
    enviar_mensagem(contato, "1️⃣ Sim, autorizar produção\n2️⃣ Não, manter como orçamento\n3️⃣ Cancelar pedido")

    # Atualiza o estado para aguardar a decisão final do usuário
    global_state.status_usuario[contato] = "aguardando_autorizacao"
    global_state.informacoes_cliente[contato]["nome_pedido"] = nome_pedido

    # Atualiza o estado para aguardar a decisão final do usuário
    global_state.status_usuario[contato] = "aguardando_confirmacao_pedido"
    global_state.informacoes_cliente[contato]["nome_pedido"] = nome_pedido


def processar_resposta_autorizacao(contato, texto):
    """
    Processa a resposta do usuário sobre autorizar, manter como orçamento ou cancelar.
    """
    dados_usuario = global_state.informacoes_cliente.get(contato, {})
    id_pedido = dados_usuario.get("id_pedido", "")
    nome_pedido = dados_usuario.get("nome_pedido", "")

    if not nome_pedido or not id_pedido:
        enviar_mensagem(contato, "❌ Erro interno: Pedido não encontrado.")
        return

    if texto == "1":
        atualizar_status_pedido(nome_pedido, "AUTORIZADO")
        mensagem_final = f"✅ Pedido **{nome_pedido}** foi AUTORIZADO para produção! 🏭"
    elif texto == "2":
        atualizar_status_pedido(nome_pedido, "ORÇAMENTO")
        mensagem_final = f"📋 Pedido **{nome_pedido}** foi mantido como ORÇAMENTO. Você pode acessá-lo depois."
    elif texto == "3":
        atualizar_status_pedido(nome_pedido, "CANCELADO")
        mensagem_final = f"🚫 Pedido **{nome_pedido}** foi CANCELADO."
    else:
        enviar_mensagem(contato, "❌ Opção inválida. Escolha uma das opções do menu.")
        return

    enviar_mensagem(contato, mensagem_final)
    global_state.limpar_dados_usuario(contato)



def processar_confirmacao_pedido(contato, texto):
    """
    Processa a confirmação do usuário após exibir o resumo do pedido.
    Se for autorizado ou mantido como orçamento, salva as peças corretamente.
    """
    texto = texto.strip()

    if texto not in ["1", "2", "3"]:
        enviar_mensagem(contato, "❌ Opção inválida. Escolha:\n1️⃣ Sim, autorizar produção\n2️⃣ Não, manter como orçamento\n3️⃣ Cancelar pedido")
        return

    dados_usuario = global_state.informacoes_cliente.get(contato, {})
    nome_pedido = dados_usuario.get("nome_pedido")

    if not nome_pedido:
        enviar_mensagem(contato, "❌ Erro interno: Nome do pedido não encontrado.")
        return

    pedidos_acumulados = dados_usuario.get("pedidos", [])
    if not pedidos_acumulados:
        enviar_mensagem(contato, "❌ Nenhum pedido encontrado para salvar.")
        return

    id_cliente = dados_usuario.get("id_cliente")
    if not id_cliente:
        enviar_mensagem(contato, "❌ Erro interno: ID do cliente não encontrado.")
        return

    if texto in ["1", "2"]:  # Autorizar produção ou manter como orçamento
        status_final = "AUTORIZADO" if texto == "1" else "ORÇAMENTO"

        for pedido in pedidos_acumulados:
            logger.debug(f"📝 Salvando pedido: {pedido}")  
            logger.debug(f"📦 Peças recebidas para salvar: {pedido.get('pecas', [])}")

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

        atualizar_status_pedido(nome_pedido, status_final)

        if texto == "1":
            mensagem_final = f"✅ Pedido **{nome_pedido}** foi AUTORIZADO para produção! 🏭"
        else:
            mensagem_final = f"📋 Pedido **{nome_pedido}** foi mantido como ORÇAMENTO. Você pode acessá-lo depois."

    elif texto == "3":  # Cliente cancela o pedido
        atualizar_status_pedido(nome_pedido, "CANCELADO")
        mensagem_final = f"🚫 Pedido **{nome_pedido}** foi CANCELADO. Caso precise, pode criar um novo orçamento."

    enviar_mensagem(contato, mensagem_final)

    # Limpar os dados do usuário após o processamento
    global_state.limpar_dados_usuario(contato)


def finalizar_conversa(contato, nome_cliente):
    """
    Finaliza a conversa e limpa os dados do usuário do estado global.
    """
    enviar_mensagem(contato, "Obrigado! Caso precise de algo, estamos à disposição! 😊")
    salvar_mensagem_em_arquivo(contato, nome_cliente, "Bot: Conversa encerrada.")
    global_state.limpar_dados_usuario(contato)
    