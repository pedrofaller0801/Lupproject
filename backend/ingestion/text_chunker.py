"""
Módulo para dividir textos longos em chunks menores com overlap.
Usa tiktoken (cl100k_base) para contar tokens de forma precisa.
"""

import tiktoken


# Encoding compatível com modelos modernos; boa aproximação para português
_ENCODING = tiktoken.get_encoding("cl100k_base")


def tokenizar(texto: str) -> list[int]:
    """Converte texto em lista de IDs de tokens."""
    return _ENCODING.encode(texto)


def detokenizar(tokens: list[int]) -> str:
    """Converte lista de IDs de tokens de volta para texto."""
    return _ENCODING.decode(tokens)


def dividir_em_chunks(
    texto: str,
    tamanho_chunk: int = 500,
    overlap: int = 50,
) -> list[str]:
    """
    Divide um texto em chunks de tamanho fixo (em tokens) com sobreposição.

    O overlap garante que informações no limite entre chunks não sejam perdidas
    durante a recuperação semântica.

    Args:
        texto:          Texto completo a ser dividido.
        tamanho_chunk:  Número máximo de tokens por chunk (padrão: 500).
        overlap:        Número de tokens sobrepostos entre chunks consecutivos (padrão: 50).

    Returns:
        Lista de strings, cada uma representando um chunk do texto original.

    Raises:
        ValueError: Se overlap for maior ou igual ao tamanho do chunk.
    """
    if overlap >= tamanho_chunk:
        raise ValueError(
            f"Overlap ({overlap}) deve ser menor que tamanho_chunk ({tamanho_chunk})."
        )

    tokens = tokenizar(texto)
    if not tokens:
        return []

    chunks: list[str] = []
    passo = tamanho_chunk - overlap
    inicio = 0

    while inicio < len(tokens):
        fim = inicio + tamanho_chunk
        fatia = tokens[inicio:fim]
        chunk_texto = detokenizar(fatia).strip()
        if chunk_texto:
            chunks.append(chunk_texto)
        inicio += passo

    return chunks
