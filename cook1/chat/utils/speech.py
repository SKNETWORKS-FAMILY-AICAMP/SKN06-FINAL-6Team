import openai
import os
# import librosa
# import noisereduce as nr
import soundfile as sf
import nltk
from datetime import datetime

openai.api_key = os.getenv("OPENAI_API_KEY")

class SpeechProcessor:
    def __init__(self):
        self.base_dir = "media/tts_audio"

    def transcribe_audio(self, audio_file):
        """음성 파일을 텍스트로 변환 (파일 저장 없이 임시 변환)"""
        try:
            with open(audio_file, "rb") as audio:
                response = openai.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio
                )
            return self.format_transcription(response.text)
        except Exception as e:
            print(f"STT 변환 오류: {e}")
            return None

    def format_transcription(self, text):
        """STT 변환 후 문장 정리"""
        sentences = nltk.sent_tokenize(text.strip())
        return " ".join([sentence.capitalize() for sentence in sentences])

    def generate_speech(self, text, user_id, voice="nova"):
        """텍스트를 음성 파일로 변환 (저장됨)"""
        try:
            user_dir = os.path.join(self.base_dir, f"user_{user_id}")
            os.makedirs(user_dir, exist_ok=True)

            # ✅ 기존 오래된 파일 정리 (예: 10개 이상이면 삭제)
            existing_files = sorted(
                [os.path.join(user_dir, f) for f in os.listdir(user_dir)],
                key=os.path.getctime
            )
            if len(existing_files) > 10:  # 10개 이상이면 가장 오래된 파일 삭제
                os.remove(existing_files[0])

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = os.path.join(user_dir, f"{timestamp}.mp3")

            response = openai.audio.speech.create(
                model="tts-1",
                voice=voice,
                input=text
            )

            with open(output_file, "wb") as f:
                f.write(response.content)

            return output_file
        except Exception as e:
            print(f"TTS 변환 오류: {e}")
            return None
