from nacl.exceptions import BadSignatureError
from nacl.signing import VerifyKey


def assinatura_valida(public_key: str, assinatura: str, timestamp: str, corpo: bytes) -> bool:
    """Confere a assinatura Ed25519 que o Discord envia em toda interação."""
    if not public_key or not assinatura or not timestamp:
        return False
    try:
        chave = VerifyKey(bytes.fromhex(public_key))
        chave.verify(timestamp.encode() + corpo, bytes.fromhex(assinatura))
        return True
    except (BadSignatureError, ValueError):
        return False