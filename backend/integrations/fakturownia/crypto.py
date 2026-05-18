"""
RAO-P2-012: Fernet encryption dla API tokenów Fakturownia.

Użycie:
- encrypt_token(plain) → bytes (ciphertext)
- decrypt_token(ciphertext) → str (plaintext)
- mask_token(plain) → str (preview, np. "tk_****1234")

Security:
- Fernet (AES-128-CBC + HMAC) z cryptography lib
- Key z env: RAO_FAKTUROWNIA_ENC_KEY (32 bytes base64)
- Jeśli key pusty → encryption disabled (dev fallback)
"""
from cryptography.fernet import Fernet, InvalidToken
from config import settings

# Lazy initialization — jeśli key pusty, encryption disabled
_fernet: Fernet | None = None


def _get_fernet() -> Fernet:
    """Zwraca F instance lub rzuca ValueError jeśli key nieustawiony."""
    global _fernet
    if _fernet is None:
        key = settings.RAO_FAKTUROWNIA_ENC_KEY
        if not key:
            raise ValueError(
                "RAO_FAKTUROWNIA_ENC_KEY not set — encryption disabled. "
                "Set in .env or disable encryption for dev."
            )
        try:
            _fernet = Fernet(key.encode())
        except Exception as e:
            raise ValueError(f"Invalid Fernet key: {e}")
    return _fernet


def encrypt_token(plain: str, key: str | None = None) -> bytes:
    """Szyfruje plaintext token → ciphertext (VARBINARY).

    Args:
        plain: Plaintext token
        key: Optional Fernet key (32 bytes base64). If None, reads from settings.
    """
    if not plain:
        raise ValueError("Token cannot be empty")
    if key:
        # Backwards-compatible: allow passing key directly
        f = Fernet(key.encode())
    else:
        f = _get_fernet()
    return f.encrypt(plain.encode())


def decrypt_token(ciphertext: bytes, key: str | None = None) -> str:
    """Odszyfrowuje ciphertext → plaintext token.

    Args:
        ciphertext: Encrypted token bytes
        key: Optional Fernet key (32 bytes base64). If None, reads from settings.
    """
    if not ciphertext:
        raise ValueError("Ciphertext cannot be empty")
    if key:
        # Backwards-compatible: allow passing key directly
        f = Fernet(key.encode())
    else:
        f = _get_fernet()
    try:
        return f.decrypt(ciphertext).decode()
    except InvalidToken:
        raise ValueError("Invalid ciphertext or wrong encryption key")


def mask_token(plain: str) -> str:
    """Zwraca bezpieczny preview tokena (np. 'tk_****1234')."""
    if not plain:
        return "****"
    if len(plain) < 8:
        return "****" * min(4, len(plain) // 2)
    # Pierwsze 4 + ostatnie 4 znaki
    return f"{plain[:4]}****{plain[-4:]}"