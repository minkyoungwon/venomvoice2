"""
Metis TTS API 라우트 

TTS(Text-to-Speech) 관련 API 엔드포인트를 정의합니다.
"""

import os
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from fastapi.responses import FileResponse, StreamingResponse, JSONResponse
from pydantic import BaseModel, Field
import logging
import io
import uuid
from pathlib import Path

# 로깅 설정
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# 라우터 초기화
router = APIRouter(prefix="/tts", tags=["TTS"])

# 임시 파일 저장 디렉토리
TEMP_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "temp")
os.makedirs(TEMP_DIR, exist_ok=True)

# 모델 체크포인트와 설정 파일 경로
# 실제 파일 경로는 프로젝트 설정에 맞게 수정해야 합니다
MODEL_CHECKPOINT = os.path.abspath(os.path.join(
    os.path.dirname(os.path.dirname(__file__)), 
    "..", "..", "Amphion", "Amphion", "pretrained", "metis-korean-base.pth"
))
MODEL_CONFIG = os.path.abspath(os.path.join(
    os.path.dirname(os.path.dirname(__file__)), 
    "..", "..", "Amphion", "Amphion", "models", "tts", "metis", "config", "tts.json"
))

# 경로 출력 (디버깅용)
logger.info(f"MODEL_CHECKPOINT 경로: {MODEL_CHECKPOINT}")
logger.info(f"MODEL_CONFIG 경로: {MODEL_CONFIG}")
logger.info(f"TEMP_DIR 경로: {TEMP_DIR}")

# TTS 서비스 인스턴스 (싱글톤)
_tts_service = None

def get_tts_service():
    """TTS 서비스 싱글톤 인스턴스를 반환합니다."""
    global _tts_service
    
    if _tts_service is None:
        try:
            # TTS 서비스 모듈 임포트 (지연 임포트)
            from services.tts_service import MetisTTSService
            
            logger.info("TTS 서비스 초기화 중...")
            _tts_service = MetisTTSService(
                ckpt_path=MODEL_CHECKPOINT,
                config_path=MODEL_CONFIG
            )
            logger.info("TTS 서비스 초기화 완료")
        except Exception as e:
            logger.error(f"TTS 서비스 초기화 실패: {e}")
            # 여기서는 전체 오류를 남기기 위해 re-raise
            raise
    
    return _tts_service

# API 요청 모델
class TTSRequest(BaseModel):
    """TTS 요청 모델"""
    text: str = Field(..., description="음성으로 변환할 텍스트")
    use_cache: bool = Field(True, description="캐시 사용 여부")
    speaker_id: Optional[str] = Field(None, description="화자 ID (아직 미구현)")

class TTSResponse(BaseModel):
    """TTS 응답 모델"""
    success: bool = Field(..., description="요청 성공 여부")
    message: str = Field(..., description="응답 메시지")
    file_url: Optional[str] = Field(None, description="생성된 오디오 파일 URL")

# 임시 파일 정리 함수
def cleanup_temp_file(file_path: str):
    """임시 파일을 삭제합니다."""
    try:
        os.unlink(file_path)
        logger.info(f"임시 파일 삭제 완료: {file_path}")
    except Exception as e:
        logger.error(f"임시 파일 삭제 실패: {e}")

@router.post("/synthesize", response_model=TTSResponse)
async def synthesize_text(
    request: TTSRequest,
    background_tasks: BackgroundTasks
):
    """텍스트를 음성으로 변환하여 파일로 저장하고 URL을 반환합니다.
    
    이 API는 텍스트를 받아 음성 파일을 생성하고, 파일에 접근할 수 있는 URL을 반환합니다.
    생성된 파일은 임시 파일로, 다운로드 후 자동으로 삭제됩니다.
    """
    try:
        # 요청 파라미터 로깅
        logger.info(f"TTS 요청: 텍스트 길이={len(request.text)}, 캐시={request.use_cache}")
        
        # TTS 서비스 인스턴스 가져오기
        tts_service = get_tts_service()
        
        # 임시 파일 경로 생성
        file_name = f"tts_{uuid.uuid4()}.wav"
        output_path = os.path.join(TEMP_DIR, file_name)
        
        # 음성 합성 수행
        tts_service.synthesize_to_file(
            text=request.text,
            output_path=output_path,
            use_cache=request.use_cache
        )
        
        # 임시 파일 삭제 태스크 예약
        background_tasks.add_task(cleanup_temp_file, output_path)
        
        # 파일 URL 생성 (실제 배포 환경에 맞게 수정 필요)
        file_url = f"/tts/download/{file_name}"
        
        return TTSResponse(
            success=True,
            message="음성 합성 완료",
            file_url=file_url
        )
        
    except Exception as e:
        logger.error(f"음성 합성 중 오류 발생: {e}")
        raise HTTPException(status_code=500, detail=f"음성 합성 중 오류 발생: {e}")

@router.get("/download/{file_name}")
async def download_audio(file_name: str):
    """생성된 음성 파일을 다운로드합니다."""
    file_path = os.path.join(TEMP_DIR, file_name)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="파일을 찾을 수 없습니다")
    
    return FileResponse(
        path=file_path,
        filename=file_name,
        media_type="audio/wav"
    )

@router.post("/synthesize/stream")
async def synthesize_text_stream(request: TTSRequest):
    """텍스트를 음성으로 변환하여 스트리밍으로 반환합니다."""
    try:
        # TTS 서비스 인스턴스 가져오기
        tts_service = get_tts_service()
        
        # 오디오 바이트 생성
        audio_bytes = tts_service.synthesize_to_bytes(
            text=request.text,
            format="wav",
            use_cache=request.use_cache
        )
        
        # 스트리밍 응답 반환
        return StreamingResponse(
            io.BytesIO(audio_bytes),
            media_type="audio/wav"
        )
        
    except Exception as e:
        logger.error(f"음성 합성 스트리밍 중 오류 발생: {e}")
        raise HTTPException(status_code=500, detail=f"음성 합성 스트리밍 중 오류 발생: {e}")

@router.get("/check")
async def check_tts_service():
    """TTS 서비스 상태를 확인합니다."""
    try:
        # TTS 서비스 인스턴스 가져오기
        tts_service = get_tts_service()
        
        # 간단한 텍스트로 서비스 작동 확인
        tts_service.synthesize("안녕하세요, 메티스 TTS입니다.")
        return {"status": "ok", "message": "TTS 서비스가 정상 작동 중입니다."}
    except Exception as e:
        logger.error(f"TTS 서비스 확인 실패: {e}")
        raise HTTPException(status_code=500, detail=f"TTS 서비스 확인 실패: {e}")