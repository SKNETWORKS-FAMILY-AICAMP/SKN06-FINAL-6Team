import random
import string
import sqlite3
from typing import List
from pydantic import BaseModel, Field

from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage
from langchain_core.chat_history import BaseChatMessageHistory

from dotenv import load_dotenv

load_dotenv()

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
    """대화 내용 불러오기 최신 대화 5쌍은 원문 그대로 가져오고 그 이전 대화는 요약한다."""
    if (user_id, history_id) not in store:
        try:
            conn = sqlite3.connect("./db/history.db")
            cursor = conn.cursor()
            cursor.execute("SELECT messages FROM chat_history WHERE user_id=? AND history_id=?", (user_id, history_id))
            result = cursor.fetchone()
            conn.close()
        except:
            result = None

        if result:
            messages = eval(result[0])  # 저장된 문자열을 리스트로 변환
        else:
            messages = []

        # 세션 메모리에서만 오래된 대화를 요약 (저장된 DB 데이터는 그대로 유지)
        if len(messages) > 5:
            recent_messages = messages[-5:]  # 최신 5쌍 유지
            old_messages = messages[:-5]  # 요약할 메시지
            summary = model.invoke({"question": "다음 대화를 요약해줘", "history": old_messages})  # 요약 수행
            messages = [summary] + recent_messages  # 요약 + 최신 메시지 합침
        store[(user_id, history_id)] = InMemoryHistory(messages=messages)
    return store[(user_id, history_id)]

def save_history(user_id, history_id, messages):
    """대화 내용 저장 함수 -> 추후 장고 db에 맞춰서 수정해야함"""
    conn = sqlite3.connect("./db/history.db")
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS chat_history (user_id TEXT, history_id TEXT, messages TEXT)")
    cursor.execute("INSERT INTO chat_history VALUES (?, ?, ?)", (user_id, history_id, str(messages)))
    conn.commit()
    conn.close()

def mkhisid(user_id):
    """history_id 생성 함수"""
    while True:
        history_id = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(6))
        if user_id + history_id not in store.keys():
            # user_id와 history_id가 없는 경우 종료
            return history_id