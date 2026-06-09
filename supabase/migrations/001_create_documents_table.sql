-- Habilita a extensão pgvector para armazenamento de embeddings
create extension if not exists vector;

-- Tabela principal para armazenar os chunks dos projetos corrigidos
create table if not exists project_chunks (
    id          uuid primary key default gen_random_uuid(),
    project_name  text        not null,
    project_date  date,
    project_type  text,                        -- ex: residencial, comercial, institucional
    content       text        not null,         -- texto do chunk
    embedding     vector(768) not null,         -- embedding do Gemini text-embedding-004
    chunk_index   integer     not null,         -- posição do chunk dentro do documento
    total_chunks  integer     not null,         -- total de chunks do documento
    file_name     text,                         -- nome do arquivo original
    created_at    timestamptz default now()
);

-- Índice HNSW para busca vetorial eficiente por similaridade de cosseno
create index if not exists project_chunks_embedding_idx
    on project_chunks
    using hnsw (embedding vector_cosine_ops)
    with (m = 16, ef_construction = 64);

-- Índice para filtros por tipo de projeto
create index if not exists project_chunks_type_idx
    on project_chunks (project_type);

-- Função para busca semântica: retorna os N chunks mais similares ao embedding de consulta
create or replace function buscar_chunks_similares(
    embedding_consulta vector(768),
    quantidade         int     default 5,
    tipo_projeto       text    default null
)
returns table (
    id            uuid,
    project_name  text,
    project_date  date,
    project_type  text,
    content       text,
    chunk_index   integer,
    file_name     text,
    similaridade  float
)
language sql stable
as $$
    select
        pc.id,
        pc.project_name,
        pc.project_date,
        pc.project_type,
        pc.content,
        pc.chunk_index,
        pc.file_name,
        1 - (pc.embedding <=> embedding_consulta) as similaridade
    from project_chunks pc
    where (tipo_projeto is null or pc.project_type = tipo_projeto)
    order by pc.embedding <=> embedding_consulta
    limit quantidade;
$$;
