import os
import pandas as pd
import math
from datetime import datetime
from config import OUTPUT_DIR
from logger import logger
from services.global_state import global_state
from services.message_service import enviar_mensagem
from services.materials_service import carregar_tabela_mp
from services.product_service import carregar_tabela_projetos

# Caminho do arquivo de pedidos
PEDIDOS_FILE_PATH = os.path.join(OUTPUT_DIR, "pedidos.xlsx")

# Criar diretório de saída se não existir
os.makedirs(OUTPUT_DIR, exist_ok=True)

def gerar_id_pedido():
    """
    Gera um ID único no formato AAMMDD_0000 para um novo pedido do dia.
    O número 0000 cresce a cada novo pedido do dia.
    """
    hoje = datetime.now().strftime("%y%m%d")  # Formato AAMMDD
    numero_pedido = 1  # Começa do 1 caso não haja pedidos

    if not os.path.exists(PEDIDOS_FILE_PATH):
        return f"{hoje}_0001"

    try:
        df_pedidos = pd.read_excel(PEDIDOS_FILE_PATH, dtype={"id_pedido": str})

        if "id_pedido" not in df_pedidos.columns or df_pedidos.empty:
            return f"{hoje}_0001"

        pedidos_do_dia = df_pedidos[df_pedidos["id_pedido"].astype(str).str.startswith(hoje)]
        if not pedidos_do_dia.empty:
            ultimo_numero = pedidos_do_dia["id_pedido"].astype(str).str[7:11].astype(int).max()
            numero_pedido = ultimo_numero + 1

        return f"{hoje}_{numero_pedido:04d}"
    except Exception as e:
        logger.error(f"❌ Erro ao gerar ID do pedido: {e}", exc_info=True)
        return f"{hoje}_9999"  # Retorna um valor especial em caso de erro


def calcular_valores_pecas(pecas_calculadas, valor_mp_m2):
    """
    Calcula os valores do pedido com base nas peças e no valor do m² da matéria-prima.
    Retorna uma lista com os cálculos individuais das peças e o valor total do pedido.
    """
    total_geral = 0
    pedidos_calculados = []

    for i, peca in enumerate(pecas_calculadas):
        nome_peca = peca["nome_peca"]
        altura_peca, largura_peca = peca["dimensoes"]
        quantidade = peca["quantidade"]

        area_total = (altura_peca / 1000) * (largura_peca / 1000) * quantidade
        area_m2 = math.ceil(area_total / 0.25) * 0.25
        valor_total = area_m2 * valor_mp_m2
        total_geral += valor_total

        pedidos_calculados.append({
            "descricao_peca": nome_peca,
            "quantidade": quantidade,
            "altura_peca": altura_peca,
            "largura_peca": largura_peca,
            "area_m2": area_m2,
            "valor_mp_m2": valor_mp_m2,
            "valor_total": round(valor_total, 2)
        })

    return pedidos_calculados, round(total_geral, 2)


def obter_nome_materia_prima(id_materia_prima):
    """Busca a descrição da matéria-prima pelo ID."""
    df_mp = carregar_tabela_mp()
    materia = df_mp[df_mp["id_materia_prima"] == id_materia_prima]
    return materia["descricao_materia_prima"].values[0] if not materia.empty else "Matéria-prima Desconhecida"

def obter_nome_projeto(id_projeto):
    """Busca a descrição do projeto pelo ID."""
    df_projetos = carregar_tabela_projetos()
    projeto = df_projetos[df_projetos["id_projeto"] == id_projeto]
    return projeto["descricao_projeto"].values[0] if not projeto.empty else "Projeto Desconhecido"


def atualizar_status_pedido(nome_pedido, novo_status):
    """
    Atualiza o status do pedido no Excel (ORÇAMENTO, AUTORIZADO ou CANCELADO).
    """
    try:
        df_pedidos = pd.read_excel(PEDIDOS_FILE_PATH)

        if "status_pedido" not in df_pedidos.columns:
            df_pedidos["status_pedido"] = "ORÇAMENTO"  # Garante a existência da coluna

        # 🔹 Verifica se o pedido existe antes de atualizar
        if nome_pedido not in df_pedidos["nome_pedido"].values:
            logger.warning(f"⚠️ Pedido '{nome_pedido}' não encontrado no Excel. Nenhuma alteração feita.")
            return

        # Atualiza o status corretamente
        df_pedidos.loc[df_pedidos["nome_pedido"] == nome_pedido, "status_pedido"] = novo_status
        df_pedidos.to_excel(PEDIDOS_FILE_PATH, index=False)

        logger.info(f"📌 Status do pedido '{nome_pedido}' atualizado para {novo_status}.")
    except Exception as e:
        logger.error(f"❌ Erro ao atualizar status do pedido '{nome_pedido}': {e}")


def salvar_pedido(id_cliente, nome_cliente, id_projeto, id_materia_prima, altura_vao, largura_vao, pecas_calculadas, valor_mp_m2, nome_pedido, regiao):
    """Salva os pedidos no arquivo pedidos.xlsx, garantindo que todas as peças sejam registradas corretamente."""
    try:
        id_pedido = gerar_id_pedido()

        if not pecas_calculadas:
            logger.error(f"❌ Nenhuma peça recebida para salvar no pedido {id_pedido}!")

        pedidos_calculados, total_geral = calcular_valores_pecas(pecas_calculadas, valor_mp_m2)

        descricao_projeto = obter_nome_projeto(id_projeto)
        descricao_materia_prima = obter_nome_materia_prima(id_materia_prima)

        pedidos_completos = []

        for i, pedido in enumerate(pedidos_calculados):
            pedido.update({
                "id_pedido": id_pedido,
                "id_peca": f"{id_pedido}_{i + 1:03d}",
                "id_cliente": int(id_cliente),
                "nome_cliente": nome_cliente,
                "regiao": regiao,  # ✅ Salva a região no pedido final
                "id_projeto": int(id_projeto),
                "descricao_projeto": descricao_projeto,
                "id_materia_prima": int(id_materia_prima),
                "descricao_materia_prima": descricao_materia_prima,
                "altura_vao": altura_vao,
                "largura_vao": largura_vao,
                "nome_pedido": str(nome_pedido),
                "status_pedido": "ORÇAMENTO"
            })

            pedidos_completos.append(pedido)

        df_novos_pedidos = pd.DataFrame(pedidos_completos)

        if os.path.exists(PEDIDOS_FILE_PATH):
            df_existente = pd.read_excel(PEDIDOS_FILE_PATH, dtype={"id_pedido": str})
            df_final = pd.concat([df_existente, df_novos_pedidos], ignore_index=True)
        else:
            df_final = df_novos_pedidos

        df_final.to_excel(PEDIDOS_FILE_PATH, index=False)
        logger.info(f"💾 Pedido {id_pedido} salvo com sucesso! Valor total: R${total_geral:.2f}")

    except Exception as e:
        logger.error(f"❌ Erro ao salvar pedido: {e}", exc_info=True)
        enviar_mensagem(id_cliente, "❌ Erro ao salvar seu pedido. Tente novamente mais tarde.")


# def processar_resposta_autorizacao(contato, texto):
#     """
#     Processa a resposta do usuário sobre autorizar ou manter o orçamento.
#     """
#     dados_usuario = global_state.informacoes_cliente.get(contato, {})
#     nome_pedido = dados_usuario.get("nome_pedido", "")

#     if not nome_pedido:
#         enviar_mensagem(contato, "❌ Erro interno: Nome do pedido não encontrado.")
#         return

#     if texto == "1":
#         atualizar_status_pedido(nome_pedido, "AUTORIZADO")
#         mensagem_final = f"✅ Pedido **{nome_pedido}** foi AUTORIZADO para produção! 🏭"
#     elif texto == "2":
#         atualizar_status_pedido(nome_pedido, "ORÇAMENTO")
#         mensagem_final = f"📋 Pedido **{nome_pedido}** foi mantido como ORÇAMENTO. Você pode acessá-lo depois."
#     elif texto == "3":
#         atualizar_status_pedido(nome_pedido, "CANCELADO")
#         mensagem_final = f"🚫 Pedido **{nome_pedido}** foi CANCELADO. Caso precise, pode criar um novo orçamento."
#     else:
#         enviar_mensagem(contato, "❌ Opção inválida. Escolha:\n1️⃣ Autorizar produção\n2️⃣ Manter como orçamento\n3️⃣ Cancelar pedido")
#         return

#     enviar_mensagem(contato, mensagem_final)
#     global_state.limpar_dados_usuario(contato)


def visualizar_orcamentos(contato, nome_cliente):
    """
    Exibe a lista de pedidos pendentes do cliente (com status 'ORÇAMENTO').
    Mostra apenas um resumo por pedido, removendo duplicatas.
    """
    try:
        df_pedidos = pd.read_excel(PEDIDOS_FILE_PATH)

        if "status_pedido" not in df_pedidos.columns:
            enviar_mensagem(contato, "⚠️ Não foi possível carregar seus orçamentos.")
            return

        # 🔹 Filtrar pedidos do cliente que ainda estão como ORÇAMENTO
        print("###########################")
        print(contato)
        print("###########################")
        df_pedidos = df_pedidos[(df_pedidos["nome_cliente"] == nome_cliente) & (df_pedidos["status_pedido"] == "ORÇAMENTO")]

        if df_pedidos.empty:
            enviar_mensagem(contato, "📋 Você não tem orçamentos pendentes.")
            return

        # 🔹 Remover duplicatas (exibir apenas um por id_pedido)
        df_pedidos = df_pedidos.drop_duplicates(subset=["id_pedido"])

        menu_pedidos = ["📜 *Lista de Orçamentos:*"]
        opcoes_menu = []  # Armazena os IDs e nomes para controle

        for _, pedido in df_pedidos.iterrows():
            id_pedido = pedido["id_pedido"]
            nome_pedido = pedido["nome_pedido"]
            menu_pedidos.append(f"{len(opcoes_menu) + 1}. {id_pedido} - {nome_pedido}")
            opcoes_menu.append((id_pedido, nome_pedido))

        menu_pedidos.append("\nEscolha um orçamento para gerenciar:")
        enviar_mensagem(contato, "\n".join(menu_pedidos))

        # 🔹 Salvar as opções para o usuário escolher depois
        global_state.status_usuario[contato] = "escolhendo_orcamento"
        global_state.ultimo_menu_usuario[contato] = opcoes_menu

    except Exception as e:
        logger.error(f"❌ Erro ao carregar orçamentos: {e}")
        enviar_mensagem(contato, "❌ Ocorreu um erro ao buscar seus orçamentos. Tente novamente mais tarde.")

