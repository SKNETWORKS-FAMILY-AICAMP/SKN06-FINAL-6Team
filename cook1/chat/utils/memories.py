import uuid
from typing import List
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage
from langchain_core.chat_history import BaseChatMessageHistory
<<<<<<< HEAD
=======
from langchain_core.messages import HumanMessage, AIMessage
>>>>>>> 57faca037252e9d29427b9c2b95b05c38e23df88
from chat.models import HistoryChat 

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

def get_session_history(user_id: str, history_id: str) -> BaseChatMessageHistory:
    """대화 내용 불러오기 최신 대화 10개는 원문 그대로 가져오고 그 이전 대화는 요약한다."""
    if (user_id, history_id) not in store:
        try:
            history_record = HistoryChat.objects.get(user_id=user_id, history_id=history_id)
<<<<<<< HEAD
            messages = eval(history_record.messages)  # 저장된 JSON 문자열을 리스트로 변환
        except HistoryChat.DoesNotExist:
            messages = []
=======
            msgs = eval(history_record.messages) # 저장된 JSON 문자열을 리스트로 변환

            # BaseMessage 객체 리스트로 형변환
            messages = []
            for msg in msgs:
                if msg["role"] == "human":
                    messages.append(HumanMessage(content=msg["content"]))
                elif msg["role"] == "ai":
                    messages.append(AIMessage(content=msg["content"]))
        except HistoryChat.DoesNotExist:
            messages = []
        # print(f"id > {user_id, history_id}")
        # print(f"{HistoryChat.objects.get(user_id=user_id, history_id=history_id)}")
        # print(type(messages))
>>>>>>> 57faca037252e9d29427b9c2b95b05c38e23df88

        # 세션 메모리에서만 오래된 대화를 요약 (저장된 DB 데이터는 그대로 유지)
        if len(messages) > 10:
            recent_messages = messages[-10:]  # 최신 10개 유지
            old_messages = messages[:-10]  # 요약할 메시지
            summary = model.invoke({"question": "다음 대화를 요약해줘", "history": old_messages})  # 요약 수행
            messages = [summary] + recent_messages  # 요약 + 최신 메시지 합침
        
        store[(user_id, history_id)] = InMemoryHistory(messages=messages)
    
    return store[(user_id, history_id)]

<<<<<<< HEAD
def mkhisid(user_id: str) -> str:
=======
def mkhisid() -> str:
>>>>>>> 57faca037252e9d29427b9c2b95b05c38e23df88
    """UUID 기반 history_id 생성 함수"""
    return str(uuid.uuid4())