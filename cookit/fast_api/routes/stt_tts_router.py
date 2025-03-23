import os
import tempfile
from fastapi import APIRouter, UploadFile, File
from fastapi.responses import JSONResponse
from pydub import AudioSegment
from utils.speech import SpeechProcessor

router = APIRouter()

speech_processor = SpeechProcessor()

MEDIA_DIR = os.path.abspath(os.path.join(os.getcwd(), "../media/"))

@router.post("/stt/")
async def stt_api(audio: UploadFile = File(...)):
    """STT 변환"""
    temp_webm = tempfile.NamedTemporaryFile(delete=False, suffix=".webm", dir=MEDIA_DIR)
    temp_wav = tempfile.NamedTemporaryFile(delete=False, suffix=".wav", dir=MEDIA_DIR)
    try:
        with open(temp_webm.name, "wb") as f:
            f.write(await audio.read())

        audio = AudioSegment.from_file(temp_webm.name)
        audio.export(temp_wav.name, format="wav")
        text_result = speech_processor.transcribe_audio(temp_wav.name)
    except Exception as e:
        return JSONResponse({"error": f"STT 변환 오류: {str(e)}"}, status=500)
    finally:
        os.remove(temp_webm.name)
        os.remove(temp_wav.name)

    return JSONResponse({"text": text_result})

@router.post("/tts/")
async def tts_api(text: str, user_id: str = "default_user"):
    """TTS 변환"""
    try:
        audio_path = speech_processor.generate_speech(text, user_id)
        audio_url = f"/media/tts_audio/{os.path.basename(audio_path)}" if audio_path else None
        return JSONResponse({"audio_url": audio_url if audio_url else ""})
    except Exception as e:
        return JSONResponse({"error": f"TTS 변환 오류: {str(e)}"}, status=500)