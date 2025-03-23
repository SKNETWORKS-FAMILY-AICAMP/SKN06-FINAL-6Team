from typing import List
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.messages import HumanMessage, AIMessage

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

def get_session_history(messages: list) -> BaseChatMessageHistory:
    """대화 내용 불러오기 최신 대화 10개는 원문 그대로 가져오고 그 이전 대화는 요약한다."""
    chat_messages = []
    
    # BaseMessage 객체 리스트로 변환
    for msg in messages:
        if msg["role"] == "human":
            chat_messages.append(HumanMessage(content=msg["content"]))
        elif msg["role"] == "ai":
            chat_messages.append(AIMessage(content=msg["content"]))

    # 오래된 메시지 요약 (FastAPI에서 실행되지 않도록 변경)
    if len(chat_messages) > 10:
        recent_messages = chat_messages[-10:]
        old_messages = chat_messages[:-10]
        summary = model.invoke({"question": "다음 대화를 요약해줘", "history": old_messages})  # 요약 수행
        chat_messages = [summary] + recent_messages  # 요약 + 최신 메시지 합침
    
    return InMemoryHistory(messages=chat_messages)
