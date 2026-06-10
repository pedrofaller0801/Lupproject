"""
Busca vetorial no Supabase e geração do relatório de revisão com Gemini.
"""

import json
import re
import time
from datetime import date

import fitz  # PyMuPDF
from google.genai import types as genai_types
from supabase import create_client

from config import (
    MAX_CHUNKS_MANUAL,
    MAX_CHUNKS_REFERENCIA,
    SUPABASE_KEY,
    SUPABASE_URL,
)
from ingestao import _get_client


_MODELOS_FALLBACK = ["gemini-2.5-flash", "gemini-2.5-flash-lite"]


def _gerar_conteudo_com_retry(
    model:    str,
    contents: list,
    max_tentativas: int = 3,
):
    """
    Chama generate_content com retry automático para erros transitórios.
    Em 429 aguarda o retryDelay indicado pela API.
    Em 503 aguarda 10s entre tentativas.
    Após esgotar tentativas no modelo principal, tenta o fallback.
    """
    modelos = [model] + [m for m in _MODELOS_FALLBACK if m != model]

    for modelo_atual in modelos:
        for tentativa in range(max_tentativas):
            try:
                return _get_client().models.generate_content(
                    model=modelo_atual, contents=contents
                )
            except Exception as e:
                msg = str(e)
                eh_transitorio = any(c in msg for c in ("429", "503", "RESOURCE_EXHAUSTED", "UNAVAILABLE"))
                ultima_tentativa = tentativa == max_tentativas - 1

                if not eh_transitorio or ultima_tentativa:
                    if modelo_atual == modelos[-1]:
                        raise
                    break  # tenta próximo modelo

                if "429" in msg or "RESOURCE_EXHAUSTED" in msg:
                    match = re.search(r"retryDelay.*?(\d+)s", msg)
                    espera = int(match.group(1)) + 2 if match else 35 * (tentativa + 1)
                else:
                    espera = 10 * (tentativa + 1)

                print(f"  [{msg[:3]}] {modelo_atual} indisponível — aguardando {espera}s (tentativa {tentativa + 1}/{max_tentativas})...")
                time.sleep(espera)


# ---------------------------------------------------------------------------
# Embedding de consulta
# ---------------------------------------------------------------------------

def gerar_embedding_consulta(texto: str) -> list[float]:
    """
    Gera embedding para consulta (task_type=RETRIEVAL_QUERY).
    Usado ao analisar um novo projeto — diferente do RETRIEVAL_DOCUMENT da ingestão.
    """
    resultado = _get_client().models.embed_content(
        model="gemini-embedding-001",
        contents=texto,
        config=genai_types.EmbedContentConfig(
            task_type="RETRIEVAL_QUERY",
            output_dimensionality=768,
        ),
    )
    return resultado.embeddings[0].values


# ---------------------------------------------------------------------------
# Busca vetorial
# ---------------------------------------------------------------------------

def buscar_chunks(
    embedding: list[float],
    tipo: str,
    quantidade: int,
) -> list[dict]:
    """
    Busca os chunks mais similares no Supabase para um dado tipo de documento.

    Args:
        embedding:  Vetor de consulta gerado pelo texto do projeto em análise.
        tipo:       'manual' ou 'referencia'.
        quantidade: Número máximo de resultados.

    Returns:
        Lista de dicionários com conteúdo, nome_arquivo, chunk_index e similaridade.
    """
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    resposta = supabase.rpc(
        "buscar_documentos",
        {
            "embedding_consulta": embedding,
            "tipo_filtro":        tipo,
            "quantidade":         quantidade,
        },
    ).execute()
    return resposta.data or []


# ---------------------------------------------------------------------------
# Montagem do prompt
# ---------------------------------------------------------------------------

def montar_prompt(
    nome_projeto:   str,
    texto_projeto:  str,
    chunks_manual:  list[dict],
    chunks_ref:     list[dict],
    tipo_projeto:   str = "arquitetonico",
) -> str:
    """
    Monta o prompt completo para o Gemini combinar contexto textual com as imagens.

    O prompt inclui:
    - Critérios extraídos do manual do escritório
    - Exemplos de projetos anteriores revisados
    - Texto extraído do projeto em análise
    - Instrução para retornar JSON estrito
    """
    # Formata critérios do manual
    if chunks_manual:
        bloco_manual = "\n\n---\n".join(
            f"[Critério {i + 1}]\n{c['conteudo']}"
            for i, c in enumerate(chunks_manual)
        )
    else:
        bloco_manual = "Nenhum critério disponível na base. Utilize seu conhecimento técnico em arquitetura."

    # Formata exemplos de referência
    if chunks_ref:
        bloco_ref = "\n\n---\n".join(
            f"[Referência: {c['nome_arquivo']} — trecho {c['chunk_index']}]\n{c['conteudo']}"
            for i, c in enumerate(chunks_ref)
        )
    else:
        bloco_ref = "Nenhuma referência disponível na base ainda."

    hoje = date.today().isoformat()
    tipo_label = "interiores" if tipo_projeto == "interiores" else "arquitetura"

    return f"""Você é um arquiteto revisor experiente especializado em projetos de {tipo_label}. \
Analise o projeto de {tipo_label} fornecido (texto extraído + imagens das pranchas) \
e gere um relatório de revisão detalhado.

## CRITÉRIOS DO MANUAL DO ESCRITÓRIO
{bloco_manual}

## PROJETOS ANTERIORES REVISADOS (exemplos do padrão correto)
{bloco_ref}

## PROJETO EM ANÁLISE: {nome_projeto}
{texto_projeto if texto_projeto.strip() else "(Projeto predominantemente visual — ver imagens das pranchas abaixo.)"}

---

## INSTRUÇÃO
Com base nos critérios do manual, nos exemplos de referência e nas imagens das pranchas,
identifique os problemas concretos do projeto. Não invente problemas sem evidência.

### Verificação obrigatória — Consistência de áreas e medidas
Esta é uma das análises mais importantes. Para cada ambiente do projeto:
1. Leia as cotas (medidas em metros) indicadas nas pranchas.
2. Calcule a área resultante (largura × comprimento) e compare com a área informada na legenda ou no quadro de áreas.
3. Se houver divergência (ex: cota indica 3,00 × 4,00 = 12,00 m² mas a legenda diz 14,00 m²), registre como apontamento de severidade alta.
4. Verifique também se a soma das áreas dos ambientes é coerente com a área total do pavimento.
5. Aplique este critério tanto para projetos arquitetônicos (área útil, área de construção) quanto para projetos de interiores (layout, circulação mínima, proporção dos móveis em relação ao ambiente).

Retorne EXCLUSIVAMENTE o JSON abaixo, sem nenhum texto antes ou depois:

{{
  "projeto": "{nome_projeto}",
  "data_analise": "{hoje}",
  "resumo": "Breve resumo geral da qualidade do projeto (2-3 frases).",
  "total_apontamentos": 0,
  "apontamentos": [
    {{
      "categoria": "Técnico",
      "descricao": "Descrição clara e objetiva do problema identificado.",
      "severidade": "alta",
      "origem": "visual",
      "pagina_referencia": 1,
      "criterio_manual": "Trecho do manual que fundamenta esta correção, ou null.",
      "projeto_referencia": "nome_do_projeto_referencia.pdf ou null."
    }}
  ]
}}

Regras para preenchimento:
- categoria: "Técnico" | "Normativo" | "Estético" | "Funcional"
- severidade: "alta" (problemas críticos) | "média" (correções importantes) | "baixa" (sugestões)
- origem: "visual" (detectado nas imagens) | "textual" (detectado no texto extraído)
- Se não houver apontamentos em alguma categoria, simplesmente não inclua.
- O campo total_apontamentos deve refletir o tamanho real do array apontamentos.
"""


# ---------------------------------------------------------------------------
# Pipeline de análise completo
# ---------------------------------------------------------------------------

def analisar_projeto(
    pdf_bytes:    bytes,
    nome_arquivo: str,
    imagens:      list[bytes],
    tipo_projeto: str = "arquitetonico",
) -> dict:
    """
    Pipeline completo de análise RAG + Gemini Vision.

    Etapas:
        1. Extrai texto do PDF
        2. Gera embedding de consulta
        3. Busca 4 chunks do manual + 3 chunks de referências
        4. Monta prompt combinado
        5. Chama gemini-2.0-flash com texto + imagens
        6. Retorna relatório JSON validado

    Args:
        pdf_bytes:    Bytes do PDF enviado pelo usuário.
        nome_arquivo: Nome original do arquivo (usado no relatório).
        imagens:      Lista de bytes JPEG das pranchas (máx. 10).

    Returns:
        Dicionário com o relatório estruturado.

    Raises:
        json.JSONDecodeError: Se o modelo retornar JSON malformado.
        Exception:            Se a chamada à API Gemini falhar.
    """
    # Etapa 1 — Extração de texto do PDF
    texto_paginas: list[str] = []
    with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
        for i, pagina in enumerate(doc, start=1):
            texto = pagina.get_text("text").strip()
            if texto:
                texto_paginas.append(f"[Página {i}]\n{texto}")

    # Trunca para o limite do modelo de embedding (~8 000 chars ≈ 2 000 tokens)
    texto_projeto = "\n\n".join(texto_paginas)[:8000]

    # Etapa 2 — Embedding de consulta
    texto_para_embedding = texto_projeto if texto_projeto.strip() else nome_arquivo
    embedding = gerar_embedding_consulta(texto_para_embedding)

    # Etapa 3 — Busca vetorial no banco
    chunks_manual = buscar_chunks(embedding, "manual",    MAX_CHUNKS_MANUAL)
    chunks_ref    = buscar_chunks(embedding, "referencia", MAX_CHUNKS_REFERENCIA)

    # Etapa 4 — Montagem do prompt
    prompt = montar_prompt(nome_arquivo, texto_projeto, chunks_manual, chunks_ref, tipo_projeto)

    # Etapa 5 — Chamada ao Gemini com texto + imagens
    conteudo: list[genai_types.Part] = [genai_types.Part.from_text(text=prompt)]
    for img_bytes in imagens:
        conteudo.append(genai_types.Part.from_bytes(data=img_bytes, mime_type="image/jpeg"))

    resposta = _gerar_conteudo_com_retry(
        model="gemini-2.5-flash",
        contents=conteudo,
    )
    texto_resposta = resposta.text.strip()

    # Remove bloco Markdown ```json ... ``` caso o modelo o adicione
    if texto_resposta.startswith("```"):
        linhas = texto_resposta.splitlines()
        texto_resposta = "\n".join(linhas[1:-1]).strip()

    # Etapa 6 — Parse e correção do total_apontamentos
    relatorio = json.loads(texto_resposta)
    relatorio["total_apontamentos"] = len(relatorio.get("apontamentos", []))
    relatorio["tipo_projeto"] = tipo_projeto

    return relatorio
