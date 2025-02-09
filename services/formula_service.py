from logger import logger

FORMULAS_PROJETOS = {
    1: {
        "nome": "PEÇA COM MEDIDA FINAL",
        "pecas": [
            {"nome_peca": "Peça Principal", "quantidade": 1, "calculo": lambda altura, largura: (altura, largura)},
        ]
    },
    2: {
        "nome": "FIXAS no VÃO",
        "pecas": [
            {"nome_peca": "Peça Fixa - Vão", "quantidade": 1, "calculo": lambda altura, largura: (altura - 20, largura - 20)},
        ]
    },
    3: {
        "nome": "JANELA DE ABRIR 2 FOLHAS [VÃO]",
        "pecas": [
            {"nome_peca": "Peça Fixa", "quantidade": 1, "calculo": lambda altura, largura: (altura - 25, largura // 2)},
            {"nome_peca": "Peça Móvel", "quantidade": 1, "calculo": lambda altura, largura: (altura - 62, (largura // 2) + 50)},
        ]
    },
    4: {
        "nome": "JANELA DE ABRIR 4 FOLHAS [VÃO]",
        "pecas": [
            {"nome_peca": "Peça Fixa", "quantidade": 2, "calculo": lambda altura, largura: (altura - 25, largura // 4)},
            {"nome_peca": "Peça Móvel", "quantidade": 2, "calculo": lambda altura, largura: (altura - 62, (largura // 4) + 50)},
        ]
    },
}

def obter_formula_por_id(id_projeto):
    """Retorna a fórmula associada ao ID do projeto, se existir."""
    return FORMULAS_PROJETOS.get(id_projeto, None)

def calcular_pecas(id_formula, altura, largura, quantidade_total=1):
    """Calcula as dimensões das peças do projeto."""
    if not isinstance(altura, (int, float)) or not isinstance(largura, (int, float)):
        logger.error(f"❌ Valores inválidos para cálculo: altura={altura}, largura={largura}")
        return []

    formula = obter_formula_por_id(id_formula)
    if not formula:
        logger.warning(f"⚠️ Nenhuma fórmula encontrada para ID {id_formula}")
        return []

    pecas_calculadas = []
    for peca in formula["pecas"]:
        try:
            nome_peca = peca["nome_peca"]
            quantidade = peca["quantidade"] * quantidade_total
            dimensoes = peca["calculo"](altura, largura)
            
            if not isinstance(dimensoes, tuple) or len(dimensoes) != 2:
                raise ValueError("Cálculo retornou formato inválido.")

            pecas_calculadas.append({"nome_peca": nome_peca, "quantidade": quantidade, "dimensoes": dimensoes})
        except Exception as e:
            logger.error(f"❌ Erro ao calcular peça '{nome_peca}': {e}")
    
    return pecas_calculadas

