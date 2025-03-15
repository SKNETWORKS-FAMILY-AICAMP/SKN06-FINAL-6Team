from lcel.lcel import mkch
from utils.memories import mkhisid
from utils.memories import save_history

def chat(user_id):
    history_id = mkhisid(user_id)
    cchain = mkch()
    while True:
        query = input("메시지 입력 > ")
        if query == "종료":
            break
        res = cchain.invoke({"question": query}, config={"configurable": {"user_id": user_id, "history_id": history_id}})
        print(res['output'])
        save_history(user_id, history_id, {query:res['output']})

        # res = cchain.stream({"question": query}, config={"configurable": {"user_id": user_id, "history_id": history_id}})
        # print("AI: ", end="", flush=True)
        # for chunk in res:
        #         for chk in chunk['output']:
        #             print(chk, end="", flush=True)
        # print() 
chat("dddd")