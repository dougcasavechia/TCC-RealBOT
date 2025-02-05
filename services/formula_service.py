FORMULAS_PROJETOS = {
    1: {
        "nome": "Fórmula para peças sem conjunto",
        "pecas": [
            {"nome_peca": "Peça Principal", "quantidade": 1, "calculo": lambda altura, largura: (altura, largura)},
        ]
    },
    2: {
        "nome": "Fórmula para peças sem conjunto ajustadas",
        "pecas": [
            {"nome_peca": "Peça Fixa - Vão", "quantidade": 1, "calculo": lambda altura, largura: (altura - 20, largura - 20)},
        ]
    },
    3: {
        "nome": "Fórmula para janela de abrir 4 folhas",
        "pecas": [
            {"nome_peca": "Peça Fixa", "quantidade": 2, "calculo": lambda altura, largura: (altura - 25, largura // 4)},
            {"nome_peca": "Peça Móvel", "quantidade": 2, "calculo": lambda altura, largura: (altura - 62, (largura // 4) + 50)},
        ]
    },
    4: {
        "nome": "Fórmula para janela de abrir 2 folhas",
        "pecas": [
            {"nome_peca": "Peça Fixa", "quantidade": 1, "calculo": lambda altura, largura: (altura - 25, largura // 2)},
            {"nome_peca": "Peça Móvel", "quantidade": 1, "calculo": lambda altura, largura: (altura - 62, (largura // 2) + 50)},
        ]
    },
}

def obter_formula_por_id(id_projeto):
    """
    Retorna a fórmula associada ao ID do projeto.
    """
    return FORMULAS_PROJETOS.get(id_projeto)

def calcular_pecas(id_formula, altura, largura):
    """
    Calcula as dimensões das peças com base na fórmula do projeto.
    """
    formula = obter_formula_por_id(id_formula)
    
    if not formula:
        return []  # Retorna uma lista vazia se a fórmula não existir

    pecas_calculadas = []
    
    for peca in formula.get("pecas", []):
        nome_peca = peca.get("nome_peca", "Peça")
        quantidade = peca.get("quantidade", 1)
        dimensoes = peca["calculo"](altura, largura)
        
        pecas_calculadas.append({
            "nome_peca": nome_peca,
            "quantidade": quantidade,
            "dimensoes": dimensoes
        })
    
    return pecas_calculadas  # Agora sempre retorna uma lista


