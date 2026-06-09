"""
Pipeline principal de ingestão de projetos de arquitetura corrigidos.

Uso via linha de comando:
    python -m ingestion.pipeline \
        --arquivo   projetos/residencial_corrigido.pdf \
        --nome      "Residencial Vila Nova" \
        --tipo      residencial \
        --data      2024-03-15
"""

import argparse
import sys
from datetime import date
from pathlib import Path

from .pdf_extractor import extrair_texto_pdf, extrair_metadata_pdf
from .text_chunker import dividir_em_chunks
from .embedding_generator import gerar_embeddings_em_lote
from .supabase_client import DadosChunk, salvar_chunks, verificar_conexao


TIPOS_VALIDOS = ["residencial", "comercial", "institucional", "industrial", "misto", "outro"]


def ingerir_projeto(
    caminho_pdf: str | Path,
    nome_projeto: str,
    tipo_projeto: str,
    data_projeto: date | None = None,
    tamanho_chunk: int = 500,
    overlap: int = 50,
    verbose: bool = True,
) -> int:
    """
    Executa o pipeline completo de ingestão para um único documento PDF.

    Etapas:
        1. Extrai o texto do PDF com PyMuPDF.
        2. Divide o texto em chunks de tokens com sobreposição.
        3. Gera embeddings para cada chunk via Gemini text-embedding-004.
        4. Salva todos os chunks e embeddings no Supabase/pgvector.

    Args:
        caminho_pdf:    Caminho para o arquivo PDF do projeto já corrigido.
        nome_projeto:   Nome identificador do projeto (ex: "Residencial Vila Nova").
        tipo_projeto:   Categoria do projeto (residencial, comercial, etc.).
        data_projeto:   Data do projeto; usa data atual se não informada.
        tamanho_chunk:  Tokens por chunk (padrão: 500).
        overlap:        Tokens de sobreposição entre chunks (padrão: 50).
        verbose:        Se True, imprime progresso detalhado.

    Returns:
        Número de chunks inseridos com sucesso no banco.

    Raises:
        FileNotFoundError: Se o PDF não existir.
        EnvironmentError:  Se as variáveis de ambiente não estiverem configuradas.
        ConnectionError:   Se não conseguir conectar ao Supabase.
    """
    caminho = Path(caminho_pdf)
    data_efetiva = data_projeto or date.today()

    if verbose:
        print(f"\n{'='*60}")
        print(f"Iniciando ingestão: {caminho.name}")
        print(f"Projeto : {nome_projeto}")
        print(f"Tipo    : {tipo_projeto}")
        print(f"Data    : {data_efetiva}")
        print(f"{'='*60}")

    # Etapa 1 — Verificar conexão com o banco
    if verbose:
        print("\n[1/4] Verificando conexão com Supabase...")
    if not verificar_conexao():
        raise ConnectionError(
            "Não foi possível conectar ao Supabase. "
            "Verifique SUPABASE_URL e SUPABASE_SERVICE_KEY no .env."
        )
    if verbose:
        print("      Conexão OK.")

    # Etapa 2 — Extrair texto do PDF
    if verbose:
        print("\n[2/4] Extraindo texto do PDF...")
    meta = extrair_metadata_pdf(caminho)
    texto = extrair_texto_pdf(caminho)
    if verbose:
        print(f"      {meta['total_paginas']} página(s) extraídas. {len(texto):,} caracteres.")

    # Etapa 3 — Dividir em chunks
    if verbose:
        print(f"\n[3/4] Dividindo em chunks ({tamanho_chunk} tokens, overlap {overlap})...")
    chunks_texto = dividir_em_chunks(texto, tamanho_chunk, overlap)
    total_chunks = len(chunks_texto)
    if verbose:
        print(f"      {total_chunks} chunk(s) gerados.")

    # Etapa 4 — Gerar embeddings
    if verbose:
        print("\n[4/4] Gerando embeddings com Gemini text-embedding-004...")
    embeddings = gerar_embeddings_em_lote(chunks_texto, verbose=verbose)

    # Montar objetos DadosChunk
    dados_chunks = [
        DadosChunk(
            project_name=nome_projeto,
            project_type=tipo_projeto,
            content=texto_chunk,
            embedding=embedding,
            chunk_index=idx,
            total_chunks=total_chunks,
            file_name=caminho.name,
            project_date=data_efetiva,
        )
        for idx, (texto_chunk, embedding) in enumerate(zip(chunks_texto, embeddings))
    ]

    # Salvar no Supabase
    if verbose:
        print("\n     Salvando no Supabase...")
    inseridos = salvar_chunks(dados_chunks)

    if verbose:
        print(f"\n{'='*60}")
        print(f"Ingestão concluída: {len(inseridos)} chunk(s) armazenados.")
        print(f"{'='*60}\n")

    return len(inseridos)


# ──────────────────────────────────────────────────────────────────────────────
# Interface de linha de comando
# ──────────────────────────────────────────────────────────────────────────────

def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Ingere um PDF de projeto corrigido na base vetorial.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--arquivo",  required=True, help="Caminho para o arquivo PDF.")
    parser.add_argument("--nome",     required=True, help="Nome do projeto.")
    parser.add_argument(
        "--tipo",
        required=True,
        choices=TIPOS_VALIDOS,
        help=f"Tipo do projeto: {', '.join(TIPOS_VALIDOS)}.",
    )
    parser.add_argument(
        "--data",
        default=None,
        help="Data do projeto no formato AAAA-MM-DD (padrão: hoje).",
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=500,
        help="Tamanho dos chunks em tokens (padrão: 500).",
    )
    parser.add_argument(
        "--overlap",
        type=int,
        default=50,
        help="Overlap entre chunks em tokens (padrão: 50).",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()

    data_projeto = None
    if args.data:
        try:
            data_projeto = date.fromisoformat(args.data)
        except ValueError:
            print(f"Erro: data inválida '{args.data}'. Use o formato AAAA-MM-DD.")
            sys.exit(1)

    try:
        total = ingerir_projeto(
            caminho_pdf=args.arquivo,
            nome_projeto=args.nome,
            tipo_projeto=args.tipo,
            data_projeto=data_projeto,
            tamanho_chunk=args.chunk_size,
            overlap=args.overlap,
        )
        sys.exit(0)
    except (FileNotFoundError, EnvironmentError, ConnectionError, ValueError) as exc:
        print(f"\nErro: {exc}")
        sys.exit(1)
