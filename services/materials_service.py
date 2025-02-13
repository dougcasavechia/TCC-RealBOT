import pandas as pd
from config import MATERIAL_FILE_PATH
from logger import logger

def carregar_tabela_mp():
    """Carrega a tabela de matérias-primas do arquivo Excel."""
    try:
        df = pd.read_excel(MATERIAL_FILE_PATH, dtype={"id_materia_prima": str, "codigo_materia_prima": str})
        logger.info("📊 Tabela de matérias-primas carregada com sucesso.")
        return df
    except FileNotFoundError:
        logger.error(f"❌ Arquivo de matérias-primas não encontrado: {MATERIAL_FILE_PATH}")
    except Exception as e:
        logger.exception(f"❌ Erro ao carregar tabela de matérias-primas: {e}", exc_info=True)
    
    return None  # Retorna None se houver erro

def gerar_menu_materia_prima():
    """Gera o menu inicial com base na coluna 'cor_materia_prima' da tabela de matérias-primas."""
    df = carregar_tabela_mp()
    if df is None or df.empty:
        logger.warning("⚠️ A tabela de matérias-primas está vazia ou não foi carregada.")
        return []

    opcoes_iniciais = df["cor_materia_prima"].dropna().unique().tolist()
    logger.info(f"📋 {len(opcoes_iniciais)} opções carregadas para o menu de matéria-prima.")
    
    return opcoes_iniciais

# def filtrar_mp_por_escolhas(cor_materia_prima=None, espessura_materia_prima=None, beneficiamento=None):
#     """Filtra as matérias-primas com base nas escolhas do usuário."""
#     df = carregar_tabela_mp()
#     if df is None or df.empty:
#         logger.warning("⚠️ A tabela de matérias-primas está vazia ou não foi carregada.")
#         return []

#     filtros = []
#     if cor_materia_prima:
#         filtros.append(f'cor_materia_prima == "{cor_materia_prima}"')

#     # ✅ Se for "Peça Padrão", definir automaticamente espessura como 8mm
#     if espessura_materia_prima:
#         filtros.append(f'espessura_materia_prima == "{espessura_materia_prima}"')
#     elif cor_materia_prima and "peca_padrao" in cor_materia_prima.lower():
#         espessura_materia_prima = "08 mm"
#         filtros.append(f'espessura_materia_prima == "08 mm"')
#         logger.info(f"⚙️ Peça padrão detectada. Espessura definida automaticamente como 8mm.")

#     # ✅ Se for fixo, aplicar filtro de beneficiamento
#     if beneficiamento and cor_materia_prima.lower() == "fixo":
#         filtros.append(f'beneficiamento == "{beneficiamento}"')

#     if filtros:
#         try:
#             df = df.query(" and ".join(filtros))
#         except Exception as e:
#             logger.error(f"❌ Erro ao aplicar filtros: {e}", exc_info=True)
#             return []

#     if df.empty:
#         logger.info("⚠️ Nenhum resultado encontrado após filtragem.")
#         return []

#     materias_primas = df.to_dict("records")
#     logger.info(f"📌 {len(materias_primas)} matérias-primas filtradas.")
#     return materias_primas


def buscar_materia_prima(dados_usuario):
    """Busca o ID e o valor da matéria-prima com base nas escolhas do usuário."""
    df_mp = carregar_tabela_mp()
    if df_mp is None or df_mp.empty:
        logger.error("❌ Tabela de matéria-prima está vazia ou não foi encontrada.")
        return None, None

    filtros = {
        "cor_materia_prima": dados_usuario.get("cor_materia_prima"),
        "espessura_materia_prima": dados_usuario.get("espessura_materia_prima"),
        "beneficiamento": dados_usuario.get("beneficiamento"),
    }

    for coluna, valor in filtros.items():
        if valor and coluna in df_mp.columns:
            df_mp = df_mp[df_mp[coluna] == valor]

    if df_mp.empty:
        logger.warning("⚠️ Nenhuma matéria-prima encontrada com os filtros aplicados.")
        return None, None

    # Garante que colunas essenciais existam
    colunas_essenciais = ["id_materia_prima", "valor_materia_prima_m2"]
    if not all(col in df_mp.columns for col in colunas_essenciais):
        logger.error(f"❌ Colunas essenciais ausentes na tabela de matéria-prima: {colunas_essenciais}")
        return None, None

    materia_prima = df_mp.iloc[0]
    id_materia_prima = materia_prima["id_materia_prima"]
    valor_mp_m2 = materia_prima["valor_materia_prima_m2"]

    return id_materia_prima, valor_mp_m2
