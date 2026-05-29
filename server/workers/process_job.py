from shared_lib.pydantic_models.models import JobData
from sqlalchemy.orm import Session

class ProcessJob:

    def __init__(self,db:Session,redis_client):
        self.db=db
        self.redis_client=redis_client

    async def process_job(self,data:JobData):
        ext = data.ext
        if ext == 'pdf':
            await self._process_pdf()
    
    async def _process_pdf():
        pass
    
    async def _process_excel():
        pass

    async def _process_txt_file():
        pass