import os
import pandas as pd
import math
from datetime import datetime
from config import OUTPUT_DIR
from logger import logger
from services.global_state import global_state
from services.message_service import enviar_mensagem

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

    # Se o arquivo não existe ou está vazio, criar uma estrutura inicial
    if not os.path.exists(PEDIDOS_FILE_PATH):
        return f"{hoje}_0001"

    # Carregar os pedidos existentes
    df_pedidos = pd.read_excel(PEDIDOS_FILE_PATH)

    # ✅ Garantir que a coluna 'id_pedido' existe antes de acessá-la
    if "id_pedido" not in df_pedidos.columns or df_pedidos.empty:
        return f"{hoje}_0001"

    # Filtrar pedidos do mesmo dia
    pedidos_do_dia = df_pedidos[df_pedidos["id_pedido"].astype(str).str.startswith(hoje)]
    
    if not pedidos_do_dia.empty:
        ultimo_numero = pedidos_do_dia["id_pedido"].astype(str).str[7:11].astype(int).max()
        numero_pedido = ultimo_numero + 1

    return f"{hoje}_{numero_pedido:04d}"


def gerar_id_peca(id_pedido, quantidade_pecas):
    """
    Gera os IDs para cada peça dentro do pedido.
    O número 000 cresce dentro do mesmo pedido.
    """
    pecas_ids = [f"{id_pedido}_{i+1:03d}" for i in range(quantidade_pecas)]
    return pecas_ids  # Retorna uma lista com os IDs de cada peça

def salvar_pedido(id_cliente, nome_cliente, id_projeto, id_materia_prima, altura_vao, largura_vao, pecas_calculadas, valor_mp_m2, nome_pedido):
    """
    Salva os pedidos no arquivo pedidos.xlsx consolidando os dados corretamente.
    """
    pedidos = []
    id_pedido = gerar_id_pedido()

    for i, peca in enumerate(pecas_calculadas):
        nome_peca = peca["nome_peca"]
        altura_peca, largura_peca = peca["dimensoes"]
        quantidade = peca["quantidade"]

        # Cálculo de área e valor total
        area_total = (altura_peca / 1000) * (largura_peca / 1000) * quantidade
        area_m2 = math.ceil(area_total / 0.25) * 0.25
        valor_total = area_m2 * valor_mp_m2

        # Adicionar ao pedido
        pedidos.append({
            "id_pedido": id_pedido,
            "id_peca": f"{id_pedido}_{i + 1:03d}",
            "id_cliente": id_cliente,  # Sempre usa o ID correto
            "nome_cliente": nome_cliente,  # Garante o nome correto
            "id_projeto": id_projeto,
            "id_materia_prima": int(id_materia_prima),
            "descricao_peca": nome_peca,
            "quantidade": quantidade,
            "altura_vao": altura_vao,
            "largura_vao": largura_vao,
            "altura_peca": altura_peca,
            "largura_peca": largura_peca,
            "area_m2": area_m2,
            "valor_mp_m2": valor_mp_m2,
            "valor_total": round(valor_total, 2),
            "nome_pedido": nome_pedido
        })

    # Salvar no Excel
    df_novos_pedidos = pd.DataFrame(pedidos)
    if not os.path.exists(PEDIDOS_FILE_PATH):
        df_novos_pedidos.to_excel(PEDIDOS_FILE_PATH, index=False)
        return

    df_existente = pd.read_excel(PEDIDOS_FILE_PATH)
    df_final = pd.concat([df_existente, df_novos_pedidos], ignore_index=True)
    df_final.to_excel(PEDIDOS_FILE_PATH, index=False)
