
import hashlib
import json
import os
from cryptography.fernet import Fernet

META_FILE = "meta.json"
DATA_FILE = "data.dat"

def derive_key(password: str) -> bytes:
    h = hashlib.sha256(password.encode()).digest()
    return Fernet(base64.urlsafe_b64encode(h))

def generate_key_from_password(password: str) -> Fernet:
    key = hashlib.pbkdf2_hmac('sha256', password.encode(), b'salt1234', 100000)
    return Fernet(base64.urlsafe_b64encode(key))

def encrypt_data(data: list, password: str) -> bytes:
    f = generate_key_from_password(password)
    return f.encrypt(json.dumps(data).encode())

def decrypt_data(data: bytes, password: str) -> list:
    try:
        f = generate_key_from_password(password)
        return json.loads(f.decrypt(data).decode())
    except:
        return []

def save_encrypted_passwords(data: list, password: str):
    with open(DATA_FILE, "wb") as f:
        f.write(encrypt_data(data, password))

def load_encrypted_passwords(password: str) -> list:
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, "rb") as f:
        return decrypt_data(f.read(), password)

def save_meta(password: str, question: str, answer: str):
    hashed = hashlib.sha256(password.encode()).hexdigest()
    with open(META_FILE, "w") as f:
        json.dump({"hash": hashed, "question": question, "answer": answer.lower()}, f)

def load_meta():
    if not os.path.exists(META_FILE):
        return None
    with open(META_FILE) as f:
        return json.load(f)

def verify_master_password(password: str) -> bool:
    meta = load_meta()
    if not meta:
        return False
    return hashlib.sha256(password.encode()).hexdigest() == meta["hash"]

def get_recovery_question() -> str:
    meta = load_meta()
    return meta["question"] if meta else ""

def verify_recovery_answer(answer: str) -> bool:
    meta = load_meta()
    return meta and meta["answer"] == answer.lower()
        