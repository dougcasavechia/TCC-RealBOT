import os
import pandas as pd
import math
from datetime import datetime
from config import OUTPUT_DIR
from logger import logger
# from services.global_state import global_state
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


def salvar_pedido(id_cliente, nome_cliente, id_projeto, id_materia_prima, altura_vao, largura_vao, pecas_calculadas, valor_mp_m2, nome_pedido):
    """
    Salva os pedidos no arquivo pedidos.xlsx consolidando os dados corretamente.
    Agora armazena a descrição do projeto e da matéria-prima em vez dos IDs.
    """
    try:
        id_pedido = gerar_id_pedido()
        pedidos_calculados, total_geral = calcular_valores_pecas(pecas_calculadas, valor_mp_m2)

        # Buscar descrições
        descricao_projeto = obter_nome_projeto(id_projeto)
        descricao_materia_prima = obter_nome_materia_prima(id_materia_prima)

        for i, pedido in enumerate(pedidos_calculados):
            pedido.update({
                "id_pedido": id_pedido,
                "id_peca": f"{id_pedido}_{i + 1:03d}",
                "id_cliente": int(id_cliente),
                "nome_cliente": nome_cliente,
                "id_projeto": int(id_projeto),
                "descricao_projeto": descricao_projeto,  
                "id_materia_prima": int(id_materia_prima),
                "descricao_materia_prima": descricao_materia_prima,
                "altura_vao": altura_vao,
                "largura_vao": largura_vao,
                "nome_pedido": str(nome_pedido)
            })

        df_novos_pedidos = pd.DataFrame(pedidos_calculados)

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


