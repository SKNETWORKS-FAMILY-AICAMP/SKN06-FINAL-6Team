from .lcel.lcel import mkch
from .utils.memories import mkhisid

def chat(user_id):
    history_id = mkhisid(user_id)
    cchain = mkch()
    while True:
        query = input("메시지 입력 > ")
        if query == "종료":
            break
        res = cchain.invoke({"question": query}, config={"configurable": {"user_id": user_id, "history_id": history_id}})
        print(res)
