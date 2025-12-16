import os
import json
from hashlib import sha256
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from base64 import b64encode, b64decode
from django.conf import settings


class AESCipher:
    def __init__(self, key):
        # Use first 32 chars of sha256 hex digest to match Dart implementation
        self.key = sha256(key.encode()).hexdigest()[:32].encode()

    def encrypt(self, data):
        iv = os.urandom(16)
        cipher = Cipher(algorithms.AES(self.key), modes.CFB(iv), backend=default_backend())
        encryptor = cipher.encryptor()
        ct = encryptor.update(json.dumps(data).encode()) + encryptor.finalize()
        return b64encode(iv + ct).decode("utf-8")

    def decrypt(self, data):
        raw = b64decode(data.strip())
        iv = raw[:16]
        ct = raw[16:]
        cipher = Cipher(algorithms.AES(self.key), modes.CFB(iv), backend=default_backend())
        decryptor = cipher.decryptor()
        decrypted_data = decryptor.update(ct) + decryptor.finalize()
        return json.loads(decrypted_data.decode("utf-8"))
