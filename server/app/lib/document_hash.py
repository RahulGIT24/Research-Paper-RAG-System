import hashlib
from fastapi import UploadFile

async def get_file_hash(file: UploadFile):

    content = await file.read()

    file_hash = hashlib.sha256(content).hexdigest()

    await file.seek(0)

    return file_hash