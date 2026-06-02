from app.lib.get_prompt import get_system_prompt,get_user_prompt
from langchain_groq import ChatGroq
from shared_lib.core.config import settings
from typing import List
import os

class LLM:
    def __init__(self):
        os.environ['GROQ_API_KEY']=settings.LLM_API
        self.llm = ChatGroq(model=settings.LLM_MODEL,max_retries=2,streaming=True)
        self.messages = [
            (
                "system",get_system_prompt()
            )
        ]
    
    def get_messages(self,query:str,context:List[str]):
        query_tup = ("human",get_user_prompt(query=query,context=context))
        # citations not working well
        self.messages.append(query_tup)
        return self.messages

    def get_llm(self):
        return self.llm