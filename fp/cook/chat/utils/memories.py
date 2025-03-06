import random
import string
import sqlite3
from typing import List
from pydantic import BaseModel, Field

from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage
from langchain_core.chat_history import BaseChatMessageHistory

from django.db import transaction
from chat.models import ChatSession, Chats, HistoryChat

model = ChatOpenAI(model="gpt-4o-mini")

store = {}
# 메모리 체인
class InMemoryHistory(BaseChatMessageHistory, BaseModel):
    """인메모리 히스토리 클래스"""
    messages: List[BaseMessage] = Field(default_factory=list)

    def add_messages(self, messages: List[BaseMessage]) -> None:
        """Add a list of messages to the store"""
        self.messages.extend(messages)

    def clear(self) -> None:
        self.messages = []

def get_session_history(user_id: int, session_id: int):
    """
    Django ORM을 사용하여 대화 내용을 불러옴.
    최신 10개는 원문 그대로 가져오고, 그 이전 대화는 요약.
    """
    try:
        session = ChatSession.objects.get(session_id=session_id, user_id=user_id)
        chats = Chats.objects.filter(session=session).order_by('-created_at')
        messages = list(chats.values_list('question_content', 'response_content'))
        
        if len(messages) > 10:
            recent_messages = messages[-10:]
            old_messages = messages[:-10]
            summary = model.invoke({"question": "다음 대화를 요약해줘", "history": old_messages})
            messages = [summary] + recent_messages
        
        return messages
    except ChatSession.DoesNotExist:
        return []
    
def save_history(user_id: int, session_id: int, question: str, response: str):
    """
    Django ORM을 사용하여 대화 내용 저장.
    """
    try:
        with transaction.atomic():
            session, created = ChatSession.objects.get_or_create(session_id=session_id, user_id=user_id)
            Chats.objects.create(session=session, user_id=user_id, question_type='text',
                                question_content=question, response_content=response)
    except Exception as e:
        print(f"Error saving chat history: {e}")

def mkhisid(user_id: int):
    """
    새로운 ChatSession 생성 및 ID 반환.
    """
    session = ChatSession.objects.create(user_id=user_id)
    return session.session_id