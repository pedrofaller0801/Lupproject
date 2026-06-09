-- Habilita a extensão pgvector para armazenamento e busca de embeddings
create extension if not exists vector;

-- Tabela única que armazena todos os chunks indexados
-- Tanto o manual de critérios quanto os projetos anteriores revisados
create table if not exists documentos (
  id          uuid    primary key default gen_random_uuid(),
  tipo        text    not null,         -- 'manual' ou 'referencia'
  nome_arquivo text   not null,
  chunk_index integer,
  conteudo    text    not null,
  embedding   vector(768),              -- dimensão do text-embedding-004
  criado_em   timestamp default now()
);

-- Índice IVFFlat para busca por similaridade de cosseno
-- Nota: com menos de ~300 vetores, o índice faz pouco efeito mas não prejudica
create index if not exists documentos_embedding_idx
  on documentos
  using ivfflat (embedding vector_cosine_ops)
  with (lists = 100);

-- Índice auxiliar para filtros por tipo
create index if not exists documentos_tipo_idx
  on documentos (tipo);

-- Índice auxiliar para listagem por arquivo
create index if not exists documentos_arquivo_idx
  on documentos (nome_arquivo, chunk_index);
