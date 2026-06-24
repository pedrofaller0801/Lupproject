"""
Envio de feedback dos usuários por e-mail via API HTTP do Resend.

Usa a API HTTP em vez de SMTP porque plataformas como o Railway bloqueiam
conexões SMTP de saída (portas 465/587), o que travava o envio indefinidamente.
"""

import asyncio
from datetime import datetime

import resend

from config import FEEDBACK_EMAIL_DESTINO, RESEND_API_KEY

# Domínio de testes do Resend — funciona sem verificação de domínio próprio
# porque o destinatário é sempre o e-mail cadastrado na conta Resend.
_REMETENTE = "Feedback Revisor de Projetos <onboarding@resend.dev>"


def feedback_configurado() -> bool:
    """Verifica se as credenciais de envio de e-mail estão configuradas."""
    return bool(RESEND_API_KEY and FEEDBACK_EMAIL_DESTINO)


async def enviar_feedback(mensagem: str, nome: str | None = None, contato: str | None = None) -> None:
    """
    Envia o feedback do usuário por e-mail usando a API do Resend.

    Args:
        mensagem: Texto do feedback enviado pelo usuário.
        nome:     Nome de quem enviou (opcional).
        contato:  E-mail de contato de quem enviou, para resposta (opcional).

    Raises:
        EnvironmentError: Se RESEND_API_KEY ou FEEDBACK_EMAIL_DESTINO não estiverem configurados.
        Exception:        Se a API do Resend retornar erro.
    """
    if not feedback_configurado():
        raise EnvironmentError(
            "Envio de feedback não configurado. "
            "Defina RESEND_API_KEY e FEEDBACK_EMAIL_DESTINO no arquivo .env."
        )

    agora = datetime.now().strftime("%d/%m/%Y às %H:%M")

    corpo = (
        f"Novo feedback recebido em {agora}\n\n"
        f"Nome: {nome or 'não informado'}\n"
        f"Contato: {contato or 'não informado'}\n\n"
        f"Mensagem:\n{mensagem}"
    )

    resend.api_key = RESEND_API_KEY

    params: dict = {
        "from":    _REMETENTE,
        "to":      [FEEDBACK_EMAIL_DESTINO],
        "subject": "Novo feedback — Revisor de Projetos",
        "text":    corpo,
    }
    if contato:
        params["reply_to"] = contato

    # resend.Emails.send é uma chamada HTTP bloqueante; roda em thread separada
    # para não travar o event loop do servidor (mesmo padrão usado em ingestao.py).
    await asyncio.to_thread(resend.Emails.send, params)