from lcel.lcel import mkch
from utils.memories import mkhisid
from utils.memories import save_history
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse

app = FastAPI()

@app.get("/chat/")
async def chatting(user_id, history, query):
    history_id = mkhisid(user_id)
    cchain = mkch()
    async def event_stream():
        outputs = ""
        try:
            async for chunk in cchain.astream({"question": query}, config={"configurable": {"user_id": user_id, "history_id": history_id}}):
                output = chunk['output']
                outputs += output
                yield f"ai: {output}"
        except Exception as e:
            yield f"{e}"
        finally:
            save_history(user_id, history_id, {query:outputs})
    return StreamingResponse(event_stream(), media_type="text/event-stream")

@app.get("/chat/init/")
def init_hisid(user_id):
    history_id = mkhisid(user_id)
    return {"user_id":user_id, "history_id":history_id}