"""
Configurações centrais do sistema.
Carrega variáveis de ambiente e define constantes de processamento.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Diretórios
# ---------------------------------------------------------------------------

# Raiz do projeto (uma pasta acima de /backend)
RAIZ = Path(__file__).parent.parent

DIR_MANUAL    = RAIZ / "documentos" / "manual"
DIR_PROJETOS  = RAIZ / "documentos" / "projetos"
DIR_IMAGENS   = RAIZ / "documentos" / "imagens_cache"

# Garante que os diretórios existam ao importar o módulo
for _d in (DIR_MANUAL, DIR_PROJETOS, DIR_IMAGENS):
    _d.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Chaves de API
# ---------------------------------------------------------------------------

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
SUPABASE_URL   = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY   = os.getenv("SUPABASE_KEY", "")

# Envio de feedback por e-mail (opcional — só necessário para o botão de feedback)
# Usa a API HTTP do Resend em vez de SMTP, porque plataformas como o Railway
# bloqueiam conexões SMTP de saída (portas 465/587).
RESEND_API_KEY         = os.getenv("RESEND_API_KEY", "")
FEEDBACK_EMAIL_DESTINO = os.getenv("FEEDBACK_EMAIL_DESTINO", "")

# ---------------------------------------------------------------------------
# Parâmetros de processamento
# ---------------------------------------------------------------------------

DPI_IMAGEM            = 150    # resolução das imagens para análise (150 suficiente para Gemini Vision)
TAMANHO_CHUNK         = 300    # tokens por chunk
OVERLAP_CHUNK         = 50     # overlap entre chunks consecutivos
MIN_CHARS_PAGINA      = 100    # páginas com menos chars são consideradas gráficas
MAX_PAGINAS_ANALISE   = 7      # limite de pranchas enviadas ao Gemini por análise
MAX_CHUNKS_MANUAL     = 8      # chunks do manual recuperados por consulta
MAX_CHUNKS_REFERENCIA = 5      # chunks de referência recuperados por consulta

# ---------------------------------------------------------------------------
# Análise assíncrona para arquivos grandes
# ---------------------------------------------------------------------------

# PDFs acima deste tamanho são processados em segundo plano (job + polling),
# evitando que a requisição HTTP fique presa esperando a análise inteira e
# estoure o tempo limite do navegador ou do proxy da plataforma. Arquivos
# menores continuam no fluxo síncrono tradicional (resposta imediata).
LIMITE_ARQUIVO_GRANDE = 8 * 1024 * 1024   # 8 MB

# Orçamento máximo de espera (backoff) acumulada nas retentativas ao Gemini.
# Impede que sucessivos erros 429/503 façam a análise dormir indefinidamente
# e estourar o tempo limite. O fluxo assíncrono tolera esperas maiores porque
# nenhuma requisição HTTP fica bloqueada aguardando o resultado.
ORCAMENTO_BACKOFF_SYNC  = 90    # segundos — arquivos pequenos (fluxo síncrono)
ORCAMENTO_BACKOFF_ASYNC = 240   # segundos — arquivos grandes (fluxo assíncrono)


# ---------------------------------------------------------------------------
# Validação
# ---------------------------------------------------------------------------

def validar_config() -> None:
    """Lança EnvironmentError se alguma variável obrigatória estiver ausente."""
    faltando = [
        nome for nome, valor in {
            "GEMINI_API_KEY": GEMINI_API_KEY,
            "SUPABASE_URL":   SUPABASE_URL,
            "SUPABASE_KEY":   SUPABASE_KEY,
        }.items()
        if not valor
    ]
    if faltando:
        raise EnvironmentError(
            f"Variáveis de ambiente não definidas: {', '.join(faltando)}. "
            "Configure o arquivo .env na raiz do projeto."
        )
