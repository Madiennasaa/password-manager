from cryptography.fernet import Fernet
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
import base64
import os
import hashlib

ph = PasswordHasher()

def hash_master_password(password):
    return ph.hash(password)

def verify_master_password(password_hash, input_password):
    try:
        ph.verify(password_hash, input_password)
        return True
    except VerifyMismatchError:
        return False
    except Exception:
        return False

def derive_fernet_key(master_password):
    key_bytes = hashlib.sha256(master_password.encode()).digest()
    return base64.urlsafe_b64encode(key_bytes)


def encrypt_password(password, fernet_key):
    f = Fernet(fernet_key)
    return f.encrypt(password.encode())

def decrypt_password(encrypted_data, fernet_key):
    f = Fernet(fernet_key)
    return f.decrypt(encrypted_data).decode()