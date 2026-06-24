"""
Envio de feedback dos usuários por e-mail via Gmail SMTP.
"""

import smtplib
from datetime import datetime
from email.mime.text import MIMEText

from config import FEEDBACK_EMAIL_DESTINO, GMAIL_APP_PASSWORD, GMAIL_USER


def feedback_configurado() -> bool:
    """Verifica se as credenciais de envio de e-mail estão configuradas."""
    return bool(GMAIL_USER and GMAIL_APP_PASSWORD)


def enviar_feedback(mensagem: str, nome: str | None = None, contato: str | None = None) -> None:
    """
    Envia o feedback do usuário por e-mail usando Gmail SMTP.

    Args:
        mensagem: Texto do feedback enviado pelo usuário.
        nome:     Nome de quem enviou (opcional).
        contato:  E-mail de contato de quem enviou, para resposta (opcional).

    Raises:
        EnvironmentError: Se GMAIL_USER ou GMAIL_APP_PASSWORD não estiverem configurados.
        smtplib.SMTPException: Se o envio falhar.
    """
    if not feedback_configurado():
        raise EnvironmentError(
            "Envio de feedback não configurado. "
            "Defina GMAIL_USER e GMAIL_APP_PASSWORD no arquivo .env."
        )

    agora = datetime.now().strftime("%d/%m/%Y às %H:%M")

    corpo = (
        f"Novo feedback recebido em {agora}\n\n"
        f"Nome: {nome or 'não informado'}\n"
        f"Contato: {contato or 'não informado'}\n\n"
        f"Mensagem:\n{mensagem}"
    )

    email = MIMEText(corpo, "plain", "utf-8")
    email["Subject"] = "Novo feedback — Revisor de Projetos"
    email["From"] = GMAIL_USER
    email["To"] = FEEDBACK_EMAIL_DESTINO

    if contato:
        email["Reply-To"] = contato

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as servidor:
        servidor.login(GMAIL_USER, GMAIL_APP_PASSWORD)
        servidor.send_message(email)