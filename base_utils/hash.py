import hashlib


def hash_content(content):
    return hashlib.md5(content.encode('utf-8')).hexdigest()
