-- Função RPC para busca vetorial por similaridade de cosseno
-- Chamada via supabase.rpc("buscar_documentos", {...}) no backend Python
create or replace function buscar_documentos(
  embedding_consulta  vector(768),
  tipo_filtro         text,
  quantidade          int default 5
)
returns table (
  id           uuid,
  tipo         text,
  nome_arquivo text,
  chunk_index  integer,
  conteudo     text,
  similaridade float
)
language sql stable
as $$
  select
    d.id,
    d.tipo,
    d.nome_arquivo,
    d.chunk_index,
    d.conteudo,
    1 - (d.embedding <=> embedding_consulta) as similaridade
  from documentos d
  where d.tipo = tipo_filtro
  order by d.embedding <=> embedding_consulta
  limit quantidade;
$$;
