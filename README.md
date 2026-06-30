# Revisor de Projetos — RAG de Revisão de Projetos de Arquitetura

Sistema web que usa RAG multimodal para revisar projetos de arquitetura automaticamente.
O arquiteto faz upload de um PDF e recebe um relatório de correções baseado no manual do escritório e em projetos anteriores já revisados, com acesso protegido por senha e canal de feedback embutido na interface.

**Stack:** Python · FastAPI · Google Gemini 2.5 Flash (com fallback `gemini-2.5-flash-lite`) · `gemini-embedding-001` · Supabase pgvector · React · Tailwind CSS · Docker

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

Crie um arquivo `.env` na raiz do projeto:

```env
# Obrigatórias
GEMINI_API_KEY=sua_chave_aqui
SUPABASE_URL=https://xxxx.supabase.co
SUPABASE_KEY=sua_service_role_key_aqui

# Opcional — protege as rotas de API com senha de acesso.
# Se não definida, qualquer senha é aceita (modo dev).
ACESSO_SENHA=

# Opcional — necessário apenas para o botão de feedback funcionar.
# Usa a API HTTP do Resend (em vez de SMTP, que costuma ser bloqueado em
# plataformas como o Railway).
RESEND_API_KEY=
FEEDBACK_EMAIL_DESTINO=
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
> Para análises sob demanda (rota `/analisar`), o tempo pode chegar a alguns minutos em PDFs grandes/complexos, já que o backend faz retry automático em caso de erro 429/503 do Gemini (timeout do frontend: 300s).

---

## 5. Frontend

```bash
cd frontend
npm install
npm run dev
```

Interface disponível em `http://localhost:5173`.

---

## Deploy (Docker)

O `Dockerfile` na raiz compila o frontend e empacota o backend em uma única imagem, servindo a SPA estaticamente a partir do FastAPI:

```bash
docker build -t revisor-de-projetos .
docker run -p 8000:8000 --env-file .env revisor-de-projetos
```

Em produção (ex: Railway), configure as mesmas variáveis de ambiente do passo 2 no painel da plataforma.

---

## Uso do sistema

### Login
Se `ACESSO_SENHA` estiver configurada, a interface exige login antes de liberar o acesso às rotas de análise, base de contexto e feedback.

### Fluxo diário (Novo Projeto)
1. Acesse a aba **Novo Projeto**
2. Arraste ou selecione o PDF do projeto a revisar
3. Escolha o tipo de projeto (ex: arquitetônico)
4. Clique em **Analisar projeto** e aguarde — PDFs grandes/complexos podem levar alguns minutos
5. Leia o relatório organizado por categoria
6. Clique em **Aprovar e salvar na base** para adicionar o projeto como referência futura

### Gerenciar a base (Base de Contexto)
- Adicione novos manuais ou projetos de referência a qualquer momento, opcionalmente agrupados (campo `grupo`)
- Remova documentos individuais ou grupos inteiros da base

### Feedback
Um botão de feedback na interface permite enviar sugestões/problemas diretamente para o e-mail configurado em `FEEDBACK_EMAIL_DESTINO` (requer `RESEND_API_KEY`).

---

## Estrutura do projeto

```
backend/
  config.py      ← variáveis de ambiente e constantes
  visao.py       ← conversão de PDF em imagens (150 DPI)
  ingestao.py    ← pipeline de indexação + CLI
  rag.py         ← busca vetorial + análise com Gemini (com fallback de modelo e retry)
  feedback.py    ← envio de feedback por e-mail via API do Resend
  main.py        ← API FastAPI com todos os endpoints (inclui auth por senha)
frontend/
  src/
    App.jsx
    components/
      Login.jsx         ← tela de autenticação por senha
      Upload.jsx        ← área de upload com drag & drop + tipo de projeto
      Relatorio.jsx     ← exibição do relatório por categoria
      Apontamento.jsx   ← card individual de cada problema
      BaseContexto.jsx  ← gerenciamento da base
      Feedback.jsx      ← formulário de envio de feedback
documentos/
  manual/         ← coloque os PDFs do manual aqui
  projetos/       ← coloque os projetos anteriores aqui
  imagens_cache/  ← gerado automaticamente
supabase/
  migrations/     ← SQL para criar a tabela e a função de busca
Dockerfile        ← build único (frontend + backend) para deploy (ex: Railway)
```

---

## Endpoints da API

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| `POST` | `/auth` | Autentica com a senha de acesso e retorna um token de sessão |
| `POST` | `/analisar` | Analisa um PDF e retorna o relatório JSON |
| `POST` | `/base/upload` | Adiciona um documento à base |
| `GET`  | `/base/listar` | Lista todos os documentos indexados |
| `DELETE` | `/base/{id}` | Remove um documento da base |
| `DELETE` | `/base/grupo/{nome_grupo}` | Remove todos os documentos de um grupo |
| `POST` | `/feedback` | Envia uma mensagem de feedback por e-mail |
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
