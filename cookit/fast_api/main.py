from fastapi import FastAPI
from routes.chat_router import router as chat_router
from routes.stt_tts_router import router as stt_tts_router

app = FastAPI()

# 라우터 등록
app.include_router(chat_router, prefix="/chat")
app.include_router(stt_tts_router, prefix="/speech")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9000)