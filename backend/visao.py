"""
Conversão de PDFs em imagens JPEG para análise visual das pranchas.
Usa PyMuPDF (fitz) para renderização e Pillow para exportação JPEG.
"""

import io
from pathlib import Path

import fitz  # PyMuPDF
from PIL import Image

from config import DPI_IMAGEM, DIR_IMAGENS, MAX_PAGINAS_ANALISE


def pdf_para_imagens(caminho_pdf: Path, dpi: int = DPI_IMAGEM) -> list[Path]:
    """
    Converte todas as páginas de um PDF em arquivos JPEG e salva em cache.

    Cria a pasta /documentos/imagens_cache/{nome_sem_extensao}/
    e salva cada página como page_001.jpg, page_002.jpg, etc.

    Args:
        caminho_pdf: Caminho para o arquivo PDF.
        dpi: Resolução de renderização (padrão: 300 DPI).

    Returns:
        Lista de caminhos para as imagens geradas.
    """
    pasta_saida = DIR_IMAGENS / caminho_pdf.stem
    pasta_saida.mkdir(parents=True, exist_ok=True)

    caminhos: list[Path] = []
    matrix = fitz.Matrix(dpi / 72, dpi / 72)

    with fitz.open(str(caminho_pdf)) as doc:
        for i, pagina in enumerate(doc):
            pixmap = pagina.get_pixmap(matrix=matrix)

            # Converte para PIL para salvar como JPEG com controle de qualidade
            img = Image.frombytes("RGB", [pixmap.width, pixmap.height], pixmap.samples)
            caminho_img = pasta_saida / f"page_{i + 1:03d}.jpg"
            img.save(caminho_img, "JPEG", quality=90)
            caminhos.append(caminho_img)

    return caminhos


def pdf_bytes_para_imagens(
    pdf_bytes: bytes,
    max_paginas: int = MAX_PAGINAS_ANALISE,
    dpi: int = DPI_IMAGEM,
) -> list[bytes]:
    """
    Converte um PDF (em bytes) em imagens JPEG (em bytes), sem salvar em disco.
    Usado durante a análise de um projeto novo enviado via upload.

    Se o PDF tiver mais páginas do que max_paginas, prioriza as primeiras.

    Args:
        pdf_bytes:   Conteúdo do PDF como bytes.
        max_paginas: Número máximo de páginas a converter.
        dpi:         Resolução de renderização.

    Returns:
        Lista de bytes JPEG, uma por página.
    """
    imagens: list[bytes] = []
    matrix = fitz.Matrix(dpi / 72, dpi / 72)

    with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
        total = min(len(doc), max_paginas)

        for i in range(total):
            pixmap = doc[i].get_pixmap(matrix=matrix)
            img = Image.frombytes("RGB", [pixmap.width, pixmap.height], pixmap.samples)

            buffer = io.BytesIO()
            img.save(buffer, "JPEG", quality=90)
            imagens.append(buffer.getvalue())

    return imagens


def carregar_cache(nome_arquivo: str) -> list[bytes]:
    """
    Carrega as imagens já armazenadas no cache de um projeto de referência.

    Args:
        nome_arquivo: Nome do arquivo PDF original (ex: "projeto_x.pdf").

    Returns:
        Lista de bytes JPEG em ordem de página, ou lista vazia se não houver cache.
    """
    pasta = DIR_IMAGENS / Path(nome_arquivo).stem

    if not pasta.exists():
        return []

    imagens = []
    for caminho in sorted(pasta.glob("page_*.jpg")):
        imagens.append(caminho.read_bytes())

    return imagens
