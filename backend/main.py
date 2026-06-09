"""
API FastAPI — endpoints de análise de projetos e gerenciamento da base de contexto.

Execução:
    uvicorn main:app --reload --host 0.0.0.0 --port 8000
"""

import json

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from supabase import create_client

from config import SUPABASE_KEY, SUPABASE_URL, validar_config
from ingestao import configurar_gemini, indexar_bytes
from rag import analisar_projeto
from visao import pdf_bytes_para_imagens

# ---------------------------------------------------------------------------
# Inicialização
# ---------------------------------------------------------------------------

# Valida as variáveis de ambiente antes de qualquer request
validar_config()
configurar_gemini()

app = FastAPI(
    title="Sistema RAG — Revisão de Projetos de Arquitetura",
    version="1.0.0",
)

# Permite chamadas do frontend React em desenvolvimento
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def _supabase():
    """Retorna um cliente Supabase autenticado."""
    return create_client(SUPABASE_URL, SUPABASE_KEY)


# ---------------------------------------------------------------------------
# Endpoints de análise
# ---------------------------------------------------------------------------

@app.post("/analisar")
async def analisar(arquivo: UploadFile = File(...)):
    """
    Recebe um PDF de projeto novo, executa a análise RAG + IA e retorna o relatório.

    Passos internos:
        1. Converte até 10 páginas em imagens JPEG
        2. Gera embedding do texto extraído
        3. Busca contexto no Supabase (manual + referências)
        4. Monta prompt e chama gemini-2.0-flash
        5. Retorna relatório estruturado em JSON
    """
    if not arquivo.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=422, detail="Apenas arquivos PDF são aceitos.")

    conteudo = await arquivo.read()

    if len(conteudo) == 0:
        raise HTTPException(status_code=422, detail="O arquivo enviado está vazio.")

    try:
        imagens = pdf_bytes_para_imagens(conteudo)
        relatorio = analisar_projeto(conteudo, arquivo.filename, imagens)
        return relatorio

    except json.JSONDecodeError:
        raise HTTPException(
            status_code=500,
            detail="O modelo retornou um JSON inválido. Tente novamente.",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na análise: {str(e)}")


# ---------------------------------------------------------------------------
# Endpoints da base de contexto
# ---------------------------------------------------------------------------

@app.post("/base/upload")
async def base_upload(
    arquivo:   UploadFile = File(...),
    tipo:      str        = Form(...),
    relatorio: str | None = Form(default=None),
):
    """
    Adiciona um documento à base de contexto.

    Parâmetros:
        arquivo:   PDF do manual ou projeto de referência.
        tipo:      'manual' ou 'referencia'.
        relatorio: JSON do relatório de revisão (opcional).
                   Quando fornecido junto com tipo='referencia', o relatório
                   é indexado como contexto adicional (Fase 6 — aprovação).
    """
    if not arquivo.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=422, detail="Apenas arquivos PDF são aceitos.")

    if tipo not in ("manual", "referencia"):
        raise HTTPException(
            status_code=422,
            detail="O campo 'tipo' deve ser 'manual' ou 'referencia'.",
        )

    conteudo = await arquivo.read()

    if len(conteudo) == 0:
        raise HTTPException(status_code=422, detail="O arquivo enviado está vazio.")

    try:
        total = indexar_bytes(arquivo.filename, conteudo, tipo, relatorio)
        return {
            "mensagem":     f"{total} chunk(s) indexado(s) com sucesso.",
            "nome_arquivo": arquivo.filename,
            "tipo":         tipo,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na indexação: {str(e)}")


@app.get("/base/listar")
async def base_listar():
    """
    Lista todos os documentos indexados na base, agrupados por arquivo.
    Retorna um documento por linha (não um chunk por linha).
    """
    sb = _supabase()
    resposta = (
        sb.table("documentos")
        .select("id, tipo, nome_arquivo, chunk_index, criado_em")
        .order("criado_em", desc=True)
        .execute()
    )

    # Agrupa por nome_arquivo para exibir um registro por documento
    docs: dict[str, dict] = {}
    for row in resposta.data:
        nome = row["nome_arquivo"]
        if nome not in docs:
            docs[nome] = {
                "id":           row["id"],  # ID do primeiro chunk (usado para deleção)
                "tipo":         row["tipo"],
                "nome_arquivo": nome,
                "total_chunks": 0,
                "criado_em":    row["criado_em"],
            }
        docs[nome]["total_chunks"] += 1

    return {"total": len(docs), "documentos": list(docs.values())}


@app.delete("/base/{documento_id}")
async def base_deletar(documento_id: str):
    """
    Remove todos os chunks de um documento da base.

    O ID passado é o ID de qualquer chunk do documento.
    O endpoint busca o nome_arquivo correspondente e deleta todos os chunks.
    """
    sb = _supabase()

    # Busca o nome_arquivo pelo ID fornecido
    row = sb.table("documentos").select("nome_arquivo").eq("id", documento_id).execute()
    if not row.data:
        raise HTTPException(status_code=404, detail="Documento não encontrado.")

    nome = row.data[0]["nome_arquivo"]
    sb.table("documentos").delete().eq("nome_arquivo", nome).execute()

    return {"mensagem": f"Documento '{nome}' removido da base com sucesso."}


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

@app.get("/health")
async def health():
    """Verifica se o servidor e as conexões externas estão operacionais."""
    supabase_ok = False
    try:
        sb = _supabase()
        sb.table("documentos").select("id").limit(1).execute()
        supabase_ok = True
    except Exception:
        pass

    return {
        "status":   "ok" if supabase_ok else "degradado",
        "supabase": supabase_ok,
    }
