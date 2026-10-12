import re


def dividir_mensagem(texto: str, limite: int) -> list[str]:
    """Divide o texto em mensagens de até `limite` caracteres, sem partir uma oferta no meio."""
    blocos = re.split(r"\n(?=\d+\. )", texto)  # cabeçalho + um bloco por oferta
    partes: list[str] = []
    atual = ""

    for bloco in blocos:
        bloco = bloco.strip("\n")
        while len(bloco) > limite:  # bloco gigante: corta no limite
            if atual:
                partes.append(atual)
                atual = ""
            partes.append(bloco[:limite])
            bloco = bloco[limite:]
        if not atual:
            atual = bloco
        elif len(atual) + 1 + len(bloco) <= limite:
            atual += "\n" + bloco
        else:
            partes.append(atual)
            atual = bloco

    if atual:
        partes.append(atual)
    return partes or [texto[:limite]]