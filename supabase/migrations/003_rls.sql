-- Ativa o Row Level Security (RLS) na tabela documentos.
--
-- Por que: o backend acessa o Supabase exclusivamente com a chave service_role,
-- que sempre ignora RLS. Nenhuma política de acesso é criada aqui de propósito —
-- o objetivo é bloquear qualquer leitura/escrita feita diretamente via API REST
-- do Supabase usando a chave anon (que é semipública), sem afetar o backend.

alter table documentos enable row level security;
