FORMULAS_PROJETOS = {
    1: {  # Fórmula para projetos com ID 1
        "nome": "Formula para peças fixas sem conjunto",
        "fixa": [
            {"quantidade": 1, "calculo": lambda altura, largura: (altura, largura)},
        ]
    },
    2: {  # Fórmula para projetos com ID 1
        "nome": "Formula para peças fixas sem conjunto",
        "fixa": [
            {"quantidade": 1, "calculo": lambda altura, largura: (altura - 20, largura - 20)},
        ]
    },
    3: {  # Fórmula para projetos com ID 2
        "nome": "Fórmula para janela de abrir 4 folhas",
        "fixa": [
            {"quantidade": 2, "calculo": lambda altura, largura: (altura - 25, largura // 4)},
        ],
        "movel": [
            {"quantidade": 2, "calculo": lambda altura, largura: (altura - 62, (largura // 4) + 50)},
        ]
    },
    4: {  # Fórmula para projetos com ID 2
        "nome": "Fórmula para janela de abrir 2 folhas",
        "fixa": [
            {"quantidade": 1, "calculo": lambda altura, largura: (altura - 25, largura // 2)},
        ],
        "movel": [
            {"quantidade": 1, "calculo": lambda altura, largura: (altura - 62, (largura // 2) + 50)},
        ]
    },
}

def obter_formula_por_id(id_projeto):
    """
    Retorna a fórmula associada ao ID do projeto.

    :param id_projeto: ID do projeto
    :return: Dicionário contendo as fórmulas ou None se não encontrado
    """
    return FORMULAS_PROJETOS.get(id_projeto)

