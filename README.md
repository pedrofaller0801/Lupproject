# Sistema RAG — Revisão Automática de Projetos de Arquitetura

Sistema de revisão automatizada de projetos de arquitetura usando Retrieval-Augmented Generation (RAG). Recebe um PDF de projeto novo, busca projetos similares já corrigidos na base e gera um relatório estruturado de apontamentos.

## Arquitetura

```
frontend/          ← React + Tailwind (Parte 3)
backend/
  ingestion/       ← Pipeline de ingestão de projetos corrigidos (Parte 1)
  api/             ← FastAPI — revisão de novos projetos (Parte 2)
  requirements.txt
  .env.example
supabase/
  migrations/      ← SQL para criar tabela e índice pgvector
```

## Stack

| Componente | Tecnologia |
|---|---|
| LLM | Google Gemini 2.0 Flash |
| Embeddings | Gemini text-embedding-004 (768 dims) |
| Banco vetorial | Supabase + pgvector |
| Extração PDF | PyMuPDF (fitz) |
| Backend API | FastAPI |
| Frontend | React + Tailwind |

---

## Parte 1 — Pipeline de Ingestão

### Pré-requisitos

- Python 3.11+
- Conta no [Google AI Studio](https://aistudio.google.com/app/apikey) (gratuito)
- Projeto no [Supabase](https://supabase.com) com extensão `pgvector`

### Setup

**1. Clone o repositório e instale as dependências:**

```bash
cd backend
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

**2. Configure as variáveis de ambiente:**

```bash
cp .env.example .env
# Edite .env com suas chaves de API
```

**3. Execute a migração no Supabase:**

No painel do Supabase, vá em **SQL Editor** e execute o conteúdo de:

```
supabase/migrations/001_create_documents_table.sql
```

Isso cria a tabela `project_chunks`, o índice HNSW e a função RPC de busca vetorial.

### Ingestão de um projeto corrigido

```bash
# A partir da pasta backend/
python -m ingestion.pipeline \
    --arquivo   /caminho/para/projeto_corrigido.pdf \
    --nome      "Residencial Jardim Europa" \
    --tipo      residencial \
    --data      2024-06-01
```

**Tipos disponíveis:** `residencial`, `comercial`, `institucional`, `industrial`, `misto`, `outro`

**Parâmetros opcionais:**

| Parâmetro | Padrão | Descrição |
|---|---|---|
| `--chunk-size` | 500 | Tokens por chunk |
| `--overlap` | 50 | Tokens de sobreposição entre chunks |

### Exemplo de uso programático

```python
from ingestion.pipeline import ingerir_projeto
from datetime import date

total = ingerir_projeto(
    caminho_pdf="projetos/residencial.pdf",
    nome_projeto="Residencial Parque Sul",
    tipo_projeto="residencial",
    data_projeto=date(2024, 8, 20),
)
print(f"{total} chunks armazenados.")
```

---

## Formato do Relatório de Saída (Parte 2)

```json
{
  "projeto_analisado": "nome_do_arquivo.pdf",
  "data_analise": "2024-11-01",
  "apontamentos": [
    {
      "categoria": "técnico",
      "apontamento": "Espessura de laje especificada (10cm) abaixo do mínimo normativo.",
      "severidade": "alta",
      "referencia_projeto": "Residencial Jardim Europa"
    },
    {
      "categoria": "normativo",
      "apontamento": "Ausência de símbolo de norte na planta de situação.",
      "severidade": "média",
      "referencia_projeto": "Comercial Centro Novo"
    }
  ]
}
```

**Categorias:** `técnico`, `normativo`, `estético`, `funcional`  
**Severidades:** `alta`, `média`, `baixa`

---

## Variáveis de Ambiente

| Variável | Descrição |
|---|---|
| `GEMINI_API_KEY` | Chave da API do Google Gemini |
| `SUPABASE_URL` | URL do projeto Supabase |
| `SUPABASE_SERVICE_KEY` | Chave `service_role` do Supabase |
| `API_HOST` | Host do servidor FastAPI (padrão: `0.0.0.0`) |
| `API_PORT` | Porta do servidor FastAPI (padrão: `8000`) |

---

## Roadmap

- [x] **Parte 1** — Pipeline de ingestão (PDF → chunks → embeddings → Supabase)
- [ ] **Parte 2** — API FastAPI de revisão (upload → busca vetorial → relatório Gemini)
- [ ] **Parte 3** — Interface React + Tailwind (upload, análise, exibição do relatório)
