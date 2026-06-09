"""
Pipeline de ingestão de documentos para a base de contexto.

Uso via CLI:
    python backend/ingestao.py --tipo manual
    python backend/ingestao.py --tipo referencia
"""

import argparse
import sys
import time
from pathlib import Path

import fitz  # PyMuPDF
import google.generativeai as genai
import tiktoken
from supabase import create_client

from config import (
    DIR_MANUAL,
    DIR_PROJETOS,
    GEMINI_API_KEY,
    MIN_CHARS_PAGINA,
    OVERLAP_CHUNK,
    SUPABASE_KEY,
    SUPABASE_URL,
    TAMANHO_CHUNK,
    validar_config,
)
from visao import pdf_para_imagens

# Encoding para contagem de tokens (boa aproximação para português)
_ENCODING = tiktoken.get_encoding("cl100k_base")


# ---------------------------------------------------------------------------
# Funções auxiliares
# ---------------------------------------------------------------------------

def configurar_gemini() -> None:
    """Configura a chave de API do Gemini."""
    genai.configure(api_key=GEMINI_API_KEY)


def gerar_embedding_documento(texto: str) -> list[float]:
    """
    Gera embedding para armazenamento (task_type=RETRIEVAL_DOCUMENT).
    Adiciona delay de 0.7s para respeitar o rate limit gratuito (100 RPM).
    """
    resultado = genai.embed_content(
        model="models/text-embedding-004",
        content=texto,
        task_type="RETRIEVAL_DOCUMENT",
    )
    time.sleep(0.7)  # ~86 RPM — dentro do limite gratuito de 100 RPM
    return resultado["embedding"]


def extrair_texto_paginas(caminho_pdf: Path) -> list[tuple[int, str]]:
    """
    Extrai o texto de cada página de um PDF.

    Retorna lista de (numero_pagina, texto).
    Páginas com menos de MIN_CHARS_PAGINA caracteres são marcadas como gráficas
    e receberão aviso no terminal.
    """
    paginas: list[tuple[int, str]] = []

    with fitz.open(str(caminho_pdf)) as doc:
        for i, pagina in enumerate(doc, start=1):
            texto = pagina.get_text("text").strip()
            if len(texto) < MIN_CHARS_PAGINA:
                print(
                    f"  [AVISO] Página {i}: {len(texto)} chars — "
                    "considerada gráfica, ignorada no chunking de texto."
                )
            paginas.append((i, texto))

    return paginas


def chunk_texto(texto: str) -> list[str]:
    """
    Divide um texto em chunks de TAMANHO_CHUNK tokens com OVERLAP_CHUNK de sobreposição.
    Retorna lista de strings.
    """
    tokens = _ENCODING.encode(texto)
    if not tokens:
        return []

    chunks: list[str] = []
    passo = TAMANHO_CHUNK - OVERLAP_CHUNK

    for inicio in range(0, len(tokens), passo):
        fatia = tokens[inicio : inicio + TAMANHO_CHUNK]
        chunk = _ENCODING.decode(fatia).strip()
        if chunk:
            chunks.append(chunk)

    return chunks


# ---------------------------------------------------------------------------
# Pipeline principal
# ---------------------------------------------------------------------------

def indexar_documento(caminho_pdf: Path, tipo: str) -> int:
    """
    Indexa um único PDF na base de contexto do Supabase.

    Fluxo:
        1. Extrai texto com PyMuPDF
        2. Para referências, converte páginas em imagens JPEG (cache local)
        3. Quebra em chunks de 300 tokens / overlap 50
        4. Gera embeddings com text-embedding-004
        5. Salva no Supabase com tipo e metadados

    Args:
        caminho_pdf: Caminho para o arquivo PDF.
        tipo:        'manual' ou 'referencia'.

    Returns:
        Número de chunks salvos no banco.
    """
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

    print(f"\n{'─'*60}")
    print(f"Indexando: {caminho_pdf.name}  (tipo: {tipo})")
    print(f"{'─'*60}")

    # Etapa 1 — Extração de texto
    paginas = extrair_texto_paginas(caminho_pdf)

    # Etapa 2 — Para referências, gera cache de imagens
    if tipo == "referencia":
        print("  Convertendo páginas em imagens (300 DPI)...")
        imagens_geradas = pdf_para_imagens(caminho_pdf)
        print(f"  {len(imagens_geradas)} imagem(ns) salva(s) em imagens_cache/{caminho_pdf.stem}/")

    # Etapa 3 — Filtra páginas com texto e concatena
    paginas_com_texto = [
        f"[Página {n}]\n{t}"
        for n, t in paginas
        if len(t) >= MIN_CHARS_PAGINA
    ]

    if not paginas_com_texto:
        print("  [AVISO] Nenhuma página com texto suficiente. Pulando chunking.")
        return 0

    texto_total = "\n\n".join(paginas_com_texto)

    # Etapa 4 — Chunking
    chunks = chunk_texto(texto_total)
    print(f"  {len(paginas_com_texto)} página(s) com texto → {len(chunks)} chunk(s).")

    # Etapa 5 — Embeddings e inserção no banco
    print(f"  Gerando embeddings e salvando no Supabase...")
    total_salvos = 0

    for i, chunk in enumerate(chunks):
        embedding = gerar_embedding_documento(chunk)

        supabase.table("documentos").insert({
            "tipo":         tipo,
            "nome_arquivo": caminho_pdf.name,
            "chunk_index":  i,
            "conteudo":     chunk,
            "embedding":    embedding,
        }).execute()

        total_salvos += 1
        print(f"  Chunk {total_salvos}/{len(chunks)} salvo.", end="\r")

    print(f"\n  Concluído: {total_salvos} chunk(s) indexado(s).          ")
    return total_salvos


def indexar_bytes(nome_arquivo: str, conteudo: bytes, tipo: str, relatorio: str | None = None) -> int:
    """
    Versão do indexar_documento que aceita bytes diretamente (para uso via API).

    Salva o PDF temporariamente, executa o pipeline de ingestão e remove o arquivo.
    Se relatorio (JSON string) for fornecido, indexa também como chunk especial.

    Args:
        nome_arquivo: Nome original do arquivo PDF.
        conteudo:     Bytes do PDF.
        tipo:         'manual' ou 'referencia'.
        relatorio:    JSON do relatório de revisão (opcional, apenas para referências aprovadas).

    Returns:
        Número total de chunks salvos.
    """
    import tempfile
    import os

    # Salva temporariamente para usar o pipeline de ingestão baseado em Path
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False, prefix="rag_") as tmp:
        tmp.write(conteudo)
        tmp_path = Path(tmp.name)

    # Renomeia para preservar o nome original (necessário para o cache de imagens)
    destino = tmp_path.parent / nome_arquivo
    tmp_path.rename(destino)

    try:
        total = indexar_documento(destino, tipo)

        # Se veio com relatório de aprovação, indexa o conteúdo do relatório também
        if relatorio and tipo == "referencia":
            supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
            embedding = gerar_embedding_documento(relatorio[:2000])

            supabase.table("documentos").insert({
                "tipo":         "referencia",
                "nome_arquivo": nome_arquivo,
                "chunk_index":  9999,  # índice especial para identificar o relatório
                "conteudo":     f"[RELATÓRIO DE REVISÃO APROVADO]\n{relatorio[:2000]}",
                "embedding":    embedding,
            }).execute()

            total += 1
            print("  Relatório de aprovação indexado.")

        return total

    finally:
        # Garante remoção do arquivo temporário
        if destino.exists():
            os.unlink(destino)


# ---------------------------------------------------------------------------
# Interface de linha de comando
# ---------------------------------------------------------------------------

def _indexar_diretorio(tipo: str) -> None:
    """Indexa todos os PDFs do diretório correspondente ao tipo."""
    pasta = DIR_MANUAL if tipo == "manual" else DIR_PROJETOS
    pdfs = sorted(pasta.glob("*.pdf"))

    if not pdfs:
        print(f"Nenhum PDF encontrado em: {pasta}")
        print(f"Adicione arquivos PDF nessa pasta e execute novamente.")
        return

    print(f"Encontrados {len(pdfs)} PDF(s) em {pasta.name}/")
    total_geral = 0

    for caminho in pdfs:
        total_geral += indexar_documento(caminho, tipo)

    print(f"\n{'='*60}")
    print(f"Ingestão concluída. Total: {total_geral} chunk(s) no banco.")
    print(f"{'='*60}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Indexa documentos da base de contexto no Supabase.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Exemplos:\n"
            "  python backend/ingestao.py --tipo manual\n"
            "  python backend/ingestao.py --tipo referencia\n"
        ),
    )
    parser.add_argument(
        "--tipo",
        choices=["manual", "referencia"],
        required=True,
        help="Tipo de documento a indexar.",
    )
    args = parser.parse_args()

    try:
        validar_config()
        configurar_gemini()
        _indexar_diretorio(args.tipo)
    except EnvironmentError as e:
        print(f"\nErro de configuração: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nIngestão interrompida pelo usuário.")
        sys.exit(0)
