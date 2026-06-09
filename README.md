# Sistema RAG — Revisão de Projetos de Arquitetura

Sistema web que usa RAG multimodal para revisar projetos de arquitetura automaticamente.
O arquiteto faz upload de um PDF e recebe um relatório de correções baseado no manual do escritório e em projetos anteriores já revisados.

**Stack:** Python · FastAPI · Google Gemini 2.0 Flash · text-embedding-004 · Supabase pgvector · React · Tailwind CSS

---

## Pré-requisitos

- Python 3.10+
- Node.js 18+
- Conta no [Google AI Studio](https://aistudio.google.com/app/apikey) (gratuito)
- Projeto no [Supabase](https://supabase.com) (gratuito)

---

## 1. Configuração do Supabase

No painel do Supabase, abra o **SQL Editor** e execute os dois arquivos em ordem:

```sql
-- Execute primeiro:
supabase/migrations/001_schema.sql

-- Depois:
supabase/migrations/002_functions.sql
```

Isso cria a tabela `documentos`, o índice de busca vetorial e a função `buscar_documentos`.

---

## 2. Variáveis de ambiente

```bash
cp .env.example .env
```

Edite o `.env` com suas credenciais:

```env
GEMINI_API_KEY=sua_chave_aqui
SUPABASE_URL=https://xxxx.supabase.co
SUPABASE_KEY=sua_service_role_key_aqui
```

---

## 3. Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Iniciar o servidor

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

API disponível em `http://localhost:8000`.  
Documentação automática: `http://localhost:8000/docs`

---

## 4. Indexar a base de contexto (fazer uma vez)

### Manual de critérios

Coloque os PDFs do manual em `documentos/manual/` e execute:

```bash
python backend/ingestao.py --tipo manual
```

### Projetos anteriores revisados

Coloque os PDFs em `documentos/projetos/` e execute:

```bash
python backend/ingestao.py --tipo referencia
```

> **Tempo estimado:** ~45 segundos por projeto de 10 páginas (limitado pelo rate limit gratuito do Gemini).

---

## 5. Frontend

```bash
cd frontend
npm install
npm run dev
```

Interface disponível em `http://localhost:5173`.

---

## Uso do sistema

### Fluxo diário (Novo Projeto)
1. Acesse a aba **Novo Projeto**
2. Arraste ou selecione o PDF do projeto a revisar
3. Clique em **Analisar projeto** e aguarde (~1-2 minutos)
4. Leia o relatório organizado por categoria
5. Clique em **Aprovar e salvar na base** para adicionar o projeto como referência futura

### Gerenciar a base (Base de Contexto)
- Adicione novos manuais ou projetos de referência a qualquer momento
- Remova documentos desatualizados da base

---

## Estrutura do projeto

```
backend/
  config.py      ← variáveis de ambiente e constantes
  visao.py       ← conversão de PDF em imagens (300 DPI)
  ingestao.py    ← pipeline de indexação + CLI
  rag.py         ← busca vetorial + análise com Gemini
  main.py        ← API FastAPI com todos os endpoints
frontend/
  src/
    App.jsx
    components/
      Upload.jsx        ← área de upload com drag & drop
      Relatorio.jsx     ← exibição do relatório por categoria
      Apontamento.jsx   ← card individual de cada problema
      BaseContexto.jsx  ← gerenciamento da base
documentos/
  manual/         ← coloque os PDFs do manual aqui
  projetos/       ← coloque os projetos anteriores aqui
  imagens_cache/  ← gerado automaticamente
supabase/
  migrations/     ← SQL para criar a tabela e a função de busca
```

---

## Endpoints da API

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| `POST` | `/analisar` | Analisa um PDF e retorna o relatório JSON |
| `POST` | `/base/upload` | Adiciona um documento à base |
| `GET`  | `/base/listar` | Lista todos os documentos indexados |
| `DELETE` | `/base/{id}` | Remove um documento da base |
| `GET`  | `/health` | Verifica o status do sistema |

---

## Formato do relatório

```json
{
  "projeto": "nome_do_arquivo.pdf",
  "data_analise": "2026-06-09",
  "resumo": "Texto resumido da análise.",
  "total_apontamentos": 3,
  "apontamentos": [
    {
      "categoria": "Técnico",
      "descricao": "Ausência de indicação de norte na planta baixa.",
      "severidade": "alta",
      "origem": "visual",
      "pagina_referencia": 2,
      "criterio_manual": "Item 4.2 do manual: toda planta deve conter indicação de norte.",
      "projeto_referencia": "residencial_aprovado.pdf"
    }
  ]
}
```
