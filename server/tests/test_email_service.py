import pytest
from unittest.mock import patch, AsyncMock
from services.email_service import send_plain_email

@pytest.mark.asyncio
@patch("services.email_service.aiosmtplib.send", new_callable=AsyncMock)
async def test_send_plain_email_success(mock_aiosmtplib_send):
    """
    Prueba que la función send_plain_email llama correctamente a aiosmtplib.send
    con los datos esperados para un email de texto plano.
    """
    recipient = "test@example.com"
    subject = "Test Subject"
    body = "This is a test email."

    await send_plain_email(recipient, subject, body)

    # Verificamos que el método de envío fue llamado una vez
    mock_aiosmtplib_send.assert_awaited_once()

    # Extraemos los argumentos con los que fue llamado send
    call_args, call_kwargs = mock_aiosmtplib_send.call_args
    sent_message = call_args[0]

    # Verificamos el contenido del email enviado
    assert sent_message["Subject"] == subject
    assert sent_message["To"] == recipient
    assert sent_message["From"] is not None # Should be set from env
    assert sent_message.get_payload() == body
