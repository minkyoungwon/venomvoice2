"""
Metis 기반 음성 챗봇 FastAPI 애플리케이션

FastAPI를 사용하여 Metis TTS 기반의 음성 챗봇 API를 제공합니다.
"""

import os
import sys
import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# 애플리케이션 초기화
app = FastAPI(
    title="Metis 음성 챗봇 API",
    description="Metis TTS와 Whisper STT를 사용한 음성 챗봇 API",
    version="0.1.0",
)

# CORS 미들웨어 설정 (프론트엔드에서 API 접근 허용)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 모든 오리진 허용 (실제 배포 시 제한 필요)
    allow_credentials=True,
    allow_methods=["*"],  # 모든 HTTP 메소드 허용
    allow_headers=["*"],  # 모든 헤더 허용
)

# 정적 파일 디렉토리 설정 (오디오 파일 등 제공)
assets_dir = os.path.join(os.path.dirname(__file__), "assets")
os.makedirs(assets_dir, exist_ok=True)
app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

# Amphion 경로를 Python 경로에 추가 (TTS 서비스보다 먼저)
amphion_root = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)),  '..','Amphion', 'Amphion'))
if amphion_root not in sys.path:
    sys.path.insert(0, amphion_root)
    logger.info(f"Python 경로에 Amphion 루트 추가됨: {amphion_root}")

# TTS 라우터만 임포트 (에러가 발생하지 않도록)
try:
    from routes import tts
    app.include_router(tts.router)
    logger.info("TTS 라우터 로드 성공")
except Exception as e:
    logger.error(f"TTS 라우터 로드 실패: {e}")

# STT와 Chat 라우터는 아직 구현되지 않았으므로 주석 처리
# try:
#     from routes import stt
#     app.include_router(stt.router)
# except Exception as e:
#     logger.error(f"STT 라우터 로드 실패: {e}")

# try:
#     from routes import chat
#     app.include_router(chat.router)
# except Exception as e:
#     logger.error(f"Chat 라우터 로드 실패: {e}")

@app.get("/")
async def root():
    """API 루트 엔드포인트"""
    return {
        "message": "Metis 기반 음성 챗봇 서버입니다.",
        "endpoints": {
            "tts": "/tts/synthesize - 텍스트를 음성으로 변환",
            "status": "/status - 시스템 상태 확인"
        }
    }

@app.get("/status")
async def status():
    """시스템 상태 확인 엔드포인트"""
    
    # 모델 경로 확인
    tts_model_path = os.path.abspath(os.path.join(
        os.path.dirname(__file__), 
        "..", "..", "Amphion", "Amphion", "pretrained", "metis-korean-base.pth"
    ))
    tts_config_path = os.path.abspath(os.path.join(
        os.path.dirname(__file__), 
        "..", "..", "Amphion", "Amphion", "models", "tts", "metis", "config", "tts.json"
    ))
    
    # CUDA 사용 가능 여부 확인
    import torch
    cuda_available = torch.cuda.is_available()
    cuda_devices = torch.cuda.device_count() if cuda_available else 0
    
    return {
        "status": "running",
        "components": {
            "tts": {
                "engine": "Metis (Amphion)",
                "model_exists": os.path.exists(tts_model_path),
                "model_path": tts_model_path,
                "config_exists": os.path.exists(tts_config_path),
            },
            "system": {
                "cuda_available": cuda_available,
                "cuda_devices": cuda_devices,
                "torch_version": torch.__version__,
            }
        }
    }

# 애플리케이션 실행 (직접 실행 시)
if __name__ == "__main__":
    import uvicorn
    
    logger.info("Metis 음성 챗봇 서버를 시작합니다...")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )