from fastapi import APIRouter, UploadFile, File, HTTPException
from services.stt_service import stt_service
import io

router = APIRouter()

@router.post("/api/stt")
async def transcribe_audio(audio: UploadFile = File(...)):
    """
    오디오 파일을 받아서 텍스트로 변환합니다.
    """
    try:
        # 오디오 데이터 읽기
        audio_data = await audio.read()
        
        # 텍스트 변환
        transcript = await stt_service.transcribe(audio_data)
        
        return {"text": transcript}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"STT 처리 중 오류: {str(e)}")