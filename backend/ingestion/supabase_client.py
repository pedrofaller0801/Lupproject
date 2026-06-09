"""
Módulo de conexão com o Supabase e operações na tabela project_chunks.
"""

import os
from datetime import date
from dataclasses import dataclass

from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()


@dataclass
class DadosChunk:
    """Representa um chunk pronto para ser inserido no banco."""
    project_name:  str
    project_type:  str
    content:       str
    embedding:     list[float]
    chunk_index:   int
    total_chunks:  int
    file_name:     str
    project_date:  date | None = None


def _obter_cliente() -> Client:
    """
    Cria e retorna um cliente Supabase autenticado.

    Raises:
        EnvironmentError: Se SUPABASE_URL ou SUPABASE_SERVICE_KEY não estiver configurado.
    """
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_KEY")  # service_role ignora RLS para ingestão

    if not url or not key:
        raise EnvironmentError(
            "Configure SUPABASE_URL e SUPABASE_SERVICE_KEY no arquivo .env."
        )
    return create_client(url, key)


def salvar_chunks(chunks: list[DadosChunk]) -> list[dict]:
    """
    Insere uma lista de chunks (com seus embeddings) na tabela project_chunks.

    Args:
        chunks: Lista de DadosChunk prontos para inserção.

    Returns:
        Lista de registros inseridos retornados pelo Supabase.
    """
    cliente = _obter_cliente()

    registros = [
        {
            "project_name":  c.project_name,
            "project_type":  c.project_type,
            "content":       c.content,
            "embedding":     c.embedding,
            "chunk_index":   c.chunk_index,
            "total_chunks":  c.total_chunks,
            "file_name":     c.file_name,
            "project_date":  c.project_date.isoformat() if c.project_date else None,
        }
        for c in chunks
    ]

    resposta = cliente.table("project_chunks").insert(registros).execute()
    return resposta.data


def buscar_chunks_similares(
    embedding_consulta: list[float],
    quantidade: int = 5,
    tipo_projeto: str | None = None,
) -> list[dict]:
    """
    Executa a busca vetorial por similaridade de cosseno via RPC do Supabase.

    Args:
        embedding_consulta: Embedding gerado a partir do documento a ser revisado.
        quantidade:         Número de chunks mais similares a retornar.
        tipo_projeto:       Filtro opcional por tipo de projeto.

    Returns:
        Lista de dicionários com content, project_name, similaridade, etc.
    """
    cliente = _obter_cliente()

    params: dict = {
        "embedding_consulta": embedding_consulta,
        "quantidade":         quantidade,
    }
    if tipo_projeto:
        params["tipo_projeto"] = tipo_projeto

    resposta = cliente.rpc("buscar_chunks_similares", params).execute()
    return resposta.data


def verificar_conexao() -> bool:
    """Testa a conexão com o Supabase. Retorna True se bem-sucedida."""
    try:
        cliente = _obter_cliente()
        cliente.table("project_chunks").select("id").limit(1).execute()
        return True
    except Exception:
        return False
