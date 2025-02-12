from logger import logger

FORMULAS_PROJETOS = {
    1: {
        "nome": "PEÇA COM MEDIDA FINAL",
        "pecas": [
            {"nome_peca": "Peça Principal", "quantidade": 1, "calculo": lambda altura, largura: (max(altura, 0), max(largura, 0))},
        ]
    },
    2: {
        "nome": "FIXAS no VÃO",
        "pecas": [
            {"nome_peca": "Peça Fixa - Vão", "quantidade": 1, "calculo": lambda altura, largura: (max(altura - 20, 0), max(largura - 20, 0))},
        ]
    },
    3: {
        "nome": "JANELA DE ABRIR 2 FOLHAS [VÃO]",
        "pecas": [
            {"nome_peca": "Peça Fixa", "quantidade": 1, "calculo": lambda altura, largura: (max(altura - 25, 0), max(largura // 2, 0))},
            {"nome_peca": "Peça Móvel", "quantidade": 1, "calculo": lambda altura, largura: (max(altura - 62, 0), max((largura // 2) + 50, 0))},
        ]
    },
    4: {
        "nome": "JANELA DE ABRIR 4 FOLHAS [VÃO]",
        "pecas": [
            {"nome_peca": "Peça Fixa", "quantidade": 2, "calculo": lambda altura, largura: (max(altura - 25, 0), max(largura // 4, 0))},
            {"nome_peca": "Peça Móvel", "quantidade": 2, "calculo": lambda altura, largura: (max(altura - 62, 0), max((largura // 4) + 50, 0))},
        ]
    },
}

def obter_formula_por_id(id_projeto):
    """Retorna a fórmula associada ao ID do projeto, se existir."""
    formula = FORMULAS_PROJETOS.get(id_projeto)
    if not formula:
        logger.warning(f"⚠️ Nenhuma fórmula encontrada para ID {id_projeto}.")
        return None
    return formula

def calcular_pecas(id_formula, altura, largura, quantidade_total=1):
    """Calcula as dimensões das peças do projeto, garantindo valores válidos."""
    if not isinstance(largura, (int, float)) or largura <= 0:
        logger.error(f"❌ Largura inválida para cálculo: {largura}")
        return []

    # Se a altura foi predefinida pelo `processar_projeto`, usá-la diretamente
    if not isinstance(altura, (int, float)) or altura <= 0:
        logger.warning(f"⚠️ Altura não definida corretamente, assumindo 0. Verifique.")
        altura = 0  # Garante que não tenha valores inválidos

    formula = obter_formula_por_id(id_formula)
    if not formula:
        return []

    pecas_calculadas = []
    for peca in formula["pecas"]:
        try:
            nome_peca = peca["nome_peca"]
            quantidade = peca["quantidade"] * quantidade_total
            dimensoes = peca["calculo"](altura, largura)

            if not isinstance(dimensoes, tuple) or len(dimensoes) != 2:
                raise ValueError(f"Cálculo retornou formato inválido: {dimensoes}")

            pecas_calculadas.append({
                "nome_peca": nome_peca,
                "quantidade": quantidade,
                "dimensoes": (max(dimensoes[0], 0), max(dimensoes[1], 0))  # Garante que não tenha valores negativos
            })
        except Exception as e:
            logger.exception(f"❌ Erro ao calcular peça '{nome_peca}': {e}", exc_info=True)

    return pecas_calculadas
