import hashlib
import hmac


def assinatura_valida(app_secret: str, cabecalho: str, corpo: bytes) -> bool:
    """Confere o cabeçalho X-Hub-Signature-256: sha256= + HMAC-SHA256 do corpo com o App Secret."""
    if not app_secret or not cabecalho.startswith("sha256="):
        return False
    esperado = hmac.new(app_secret.encode(), corpo, hashlib.sha256).hexdigest()
    return hmac.compare_digest(esperado, cabecalho.removeprefix("sha256="))