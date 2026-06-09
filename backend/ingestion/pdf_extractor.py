"""
Módulo responsável por extrair texto de arquivos PDF usando PyMuPDF (fitz).
Preserva a ordem de leitura e concatena o conteúdo página a página.
"""

from pathlib import Path
import fitz  # PyMuPDF


def extrair_texto_pdf(caminho_pdf: str | Path) -> str:
    """
    Extrai todo o texto de um PDF, página por página.

    Args:
        caminho_pdf: Caminho para o arquivo PDF.

    Returns:
        String com todo o texto do documento separado por quebras de página.

    Raises:
        FileNotFoundError: Se o arquivo não existir.
        ValueError: Se o arquivo não for um PDF válido.
    """
    caminho = Path(caminho_pdf)
    if not caminho.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {caminho}")
    if caminho.suffix.lower() != ".pdf":
        raise ValueError(f"Formato não suportado: {caminho.suffix}. Use PDF.")

    paginas: list[str] = []

    with fitz.open(str(caminho)) as doc:
        for numero_pagina, pagina in enumerate(doc, start=1):
            texto = pagina.get_text("text")
            # Ignora páginas em branco
            if texto.strip():
                paginas.append(f"[Página {numero_pagina}]\n{texto.strip()}")

    if not paginas:
        raise ValueError(f"Nenhum texto extraído de {caminho.name}. O PDF pode conter apenas imagens.")

    return "\n\n".join(paginas)


def extrair_metadata_pdf(caminho_pdf: str | Path) -> dict:
    """
    Extrai metadados básicos do PDF (título, autor, data de criação).

    Args:
        caminho_pdf: Caminho para o arquivo PDF.

    Returns:
        Dicionário com os metadados disponíveis no documento.
    """
    caminho = Path(caminho_pdf)
    with fitz.open(str(caminho)) as doc:
        meta = doc.metadata or {}
        return {
            "titulo":         meta.get("title", ""),
            "autor":          meta.get("author", ""),
            "data_criacao":   meta.get("creationDate", ""),
            "total_paginas":  doc.page_count,
            "nome_arquivo":   caminho.name,
        }
