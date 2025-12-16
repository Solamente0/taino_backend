import binascii
import hashlib
import os
import time
import uuid
from ulid import microsecond as ulid


def generate_unique_public_id() -> str:
    # nano_seconds = str(time.time_ns())
    # system_random = str(binascii.b2a_hex(os.urandom(30)))
    # uuid4 = str(uuid.uuid4().hex)
    #
    # # todo not a good idea to md5 an uuid
    # hashed = hashlib.md5(str(nano_seconds + system_random + uuid4).encode("utf-8"))
    #
    # return hashed.hexdigest()

    return str(ulid.new()).lower()
