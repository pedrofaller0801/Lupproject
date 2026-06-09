"""
Módulo para gerar embeddings de texto usando a API do Google Gemini.
Modelo: text-embedding-004 (gratuito, 768 dimensões).
"""

import os
import time
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

# Dimensão de saída do modelo text-embedding-004
DIMENSAO_EMBEDDING = 768

# Delay mínimo entre chamadas para respeitar rate limit da API gratuita
_DELAY_ENTRE_CHAMADAS = 0.5  # segundos


def _configurar_cliente() -> None:
    """Configura a API do Gemini com a chave de ambiente."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "Variável de ambiente GEMINI_API_KEY não definida. "
            "Crie um arquivo .env com GEMINI_API_KEY=<sua_chave>."
        )
    genai.configure(api_key=api_key)


def gerar_embedding(texto: str) -> list[float]:
    """
    Gera o embedding de um único trecho de texto.

    Args:
        texto: Texto a ser convertido em vetor.

    Returns:
        Lista de 768 floats representando o embedding.

    Raises:
        EnvironmentError: Se GEMINI_API_KEY não estiver configurada.
        ValueError: Se o texto for vazio.
    """
    if not texto.strip():
        raise ValueError("Não é possível gerar embedding de texto vazio.")

    _configurar_cliente()

    resultado = genai.embed_content(
        model="models/text-embedding-004",
        content=texto,
        task_type="RETRIEVAL_DOCUMENT",  # otimizado para armazenamento em base vetorial
    )
    return resultado["embedding"]


def gerar_embeddings_em_lote(
    textos: list[str],
    verbose: bool = True,
) -> list[list[float]]:
    """
    Gera embeddings para uma lista de textos com controle de rate limit.

    Processa um texto por vez com delay entre chamadas para não exceder
    os limites da API gratuita do Gemini.

    Args:
        textos:  Lista de textos para processar.
        verbose: Se True, imprime o progresso no terminal.

    Returns:
        Lista de embeddings na mesma ordem que os textos de entrada.
    """
    _configurar_cliente()
    embeddings: list[list[float]] = []

    for i, texto in enumerate(textos, start=1):
        if verbose:
            print(f"  Gerando embedding {i}/{len(textos)}...", end="\r")

        embedding = gerar_embedding(texto)
        embeddings.append(embedding)

        # Pausa para respeitar rate limit da API gratuita
        if i < len(textos):
            time.sleep(_DELAY_ENTRE_CHAMADAS)

    if verbose:
        print(f"  {len(embeddings)} embeddings gerados.           ")

    return embeddings
