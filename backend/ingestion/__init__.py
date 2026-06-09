"""Pacote de ingestão — pipeline RAG para projetos de arquitetura."""

from .pipeline import ingerir_projeto
from .pdf_extractor import extrair_texto_pdf
from .text_chunker import dividir_em_chunks
from .supabase_client import buscar_chunks_similares

__all__ = [
    "ingerir_projeto",
    "extrair_texto_pdf",
    "dividir_em_chunks",
    "buscar_chunks_similares",
]
