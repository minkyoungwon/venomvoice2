"""
Chat API 라우트

DeepSeek API를 사용한 채팅 및 통합 음성 대화 API를 제공합니다.
"""

import logging
import asyncio
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, BackgroundTasks, UploadFile, File, Form
from pydantic import BaseModel, Field
import requests
import json
import os

# 로깅 설정
logger = logging.getLogger(__name__)

# 라우터 초기화
router = APIRouter(prefix="/api/chat", tags=["Chat"])

# DeepSeek API 설정
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"
DEEPSEEK_MODEL = "deepseek-chat"

# API 모델 정의
class ChatMessage(BaseModel):
    """채팅 메시지 모델"""
    role: str = Field(..., description="역할 (user, assistant, system)")
    content: str = Field(..., description="메시지 내용")

class ChatRequest(BaseModel):
    """채팅 요청 모델"""
    message: str = Field(..., description="사용자 메시지")
    history: Optional[List[ChatMessage]] = Field([], description="대화 기록")
    system_prompt: Optional[str] = Field(None, description="시스템 프롬프트")
    temperature: float = Field(0.7, description="창의성 정도 (0.0-2.0)")
    max_tokens: int = Field(500, description="최대 토큰 수")

class ChatResponse(BaseModel):
    """채팅 응답 모델"""
    success: bool = Field(..., description="요청 성공 여부")
    response: str = Field(..., description="AI 응답")
    usage: Optional[Dict[str, Any]] = Field(None, description="토큰 사용량 정보")

class VoiceChatRequest(BaseModel):
    """음성 채팅 요청 모델 (STT + Chat + TTS 통합)"""
    # 이 모델은 오디오 파일과 함께 사용됩니다
    history: Optional[List[ChatMessage]] = Field([], description="대화 기록")
    language: str = Field("ko", description="STT 언어 설정")
    system_prompt: Optional[str] = Field(None, description="시스템 프롬프트")
    temperature: float = Field(0.7, description="AI 창의성 정도")

def get_deepseek_api_key() -> str:
    """DeepSeek API 키를 가져옵니다."""
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=500,
            detail="DeepSeek API 키가 설정되지 않았습니다. 환경 변수 DEEPSEEK_API_KEY를 설정해주세요."
        )
    return api_key

async def call_deepseek_api(messages: List[Dict[str, str]], temperature: float = 0.7, max_tokens: int = 500) -> Dict[str, Any]:
    """DeepSeek API를 비동기로 호출합니다."""
    api_key = get_deepseek_api_key()
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    payload = {
        "model": DEEPSEEK_MODEL,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": False
    }
    
    try:
        # 비동기 요청을 위해 requests를 별도 스레드에서 실행
        def sync_request():
            response = requests.post(DEEPSEEK_API_URL, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            return response.json()
        
        # asyncio.to_thread를 사용하여 비동기로 실행
        import asyncio
        result = await asyncio.to_thread(sync_request)
        return result
        
    except requests.exceptions.RequestException as e:
        logger.error(f"DeepSeek API 호출 실패: {e}")
        raise HTTPException(status_code=500, detail=f"DeepSeek API 호출 실패: {str(e)}")
    except Exception as e:
        logger.error(f"예상치 못한 오류: {e}")
        raise HTTPException(status_code=500, detail=f"예상치 못한 오류: {str(e)}")

@router.post("/", response_model=ChatResponse)
async def chat_completion(request: ChatRequest):
    """텍스트 기반 채팅 완성 API"""
    try:
        # 메시지 구성
        messages = []
        
        # 시스템 프롬프트 추가
        if request.system_prompt:
            messages.append({"role": "system", "content": request.system_prompt})
        else:
            # 기본 시스템 프롬프트
            messages.append({
                "role": "system", 
                "content": "당신은 도움이 되고 친근한 AI 어시스턴트입니다. 사용자의 질문에 정확하고 유용한 답변을 제공해주세요."
            })
        
        # 대화 기록 추가
        for msg in request.history[-10:]:  # 최근 10개 메시지만 사용
            messages.append({"role": msg.role, "content": msg.content})
        
        # 현재 사용자 메시지 추가
        messages.append({"role": "user", "content": request.message})
        
        logger.info(f"DeepSeek API 호출: 메시지 수={len(messages)}, 온도={request.temperature}")
        
        # DeepSeek API 호출
        result = await call_deepseek_api(
            messages=messages,
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )
        
        # 응답 추출
        response_text = result["choices"][0]["message"]["content"]
        usage_info = result.get("usage", {})
        
        logger.info(f"DeepSeek API 응답 성공: 토큰 사용량={usage_info}")
        
        return ChatResponse(
            success=True,
            response=response_text,
            usage=usage_info
        )
        
    except HTTPException:
        # HTTPException은 그대로 재발생
        raise
    except Exception as e:
        logger.error(f"채팅 처리 중 오류 발생: {e}")
        raise HTTPException(status_code=500, detail=f"채팅 처리 중 오류 발생: {str(e)}")

@router.post("/voice", response_model=Dict[str, Any])
async def voice_chat(
    audio: UploadFile = File(..., description="음성 파일"),
    history: str = Form("[]", description="대화 기록 (JSON 문자열)"),
    language: str = Form("ko", description="STT 언어"),
    system_prompt: Optional[str] = Form(None, description="시스템 프롬프트"),
    temperature: float = Form(0.7, description="AI 창의성")
):
    """통합 음성 채팅 API (STT + Chat + TTS)"""
    try:
        # 대화 기록 파싱
        try:
            history_list = json.loads(history) if history else []
        except json.JSONDecodeError:
            history_list = []
        
        # 1. STT: 음성을 텍스트로 변환
        from services.stt_service import stt_service
        if stt_service is None:
            raise HTTPException(status_code=500, detail="STT 서비스를 사용할 수 없습니다")
        
        audio_data = await audio.read()
        user_text = await stt_service.transcribe(audio_data, language=language)
        
        if not user_text.strip():
            raise HTTPException(status_code=400, detail="음성에서 텍스트를 인식할 수 없습니다")
        
        logger.info(f"STT 결과: '{user_text}'")
        
        # 2. Chat: 텍스트 응답 생성
        chat_request = ChatRequest(
            message=user_text,
            history=[ChatMessage(**msg) for msg in history_list],
            system_prompt=system_prompt,
            temperature=temperature
        )
        
        chat_response = await chat_completion(chat_request)
        ai_response = chat_response.response
        
        logger.info(f"AI 응답: '{ai_response}'")
        
        # 3. TTS: 응답을 음성으로 변환
        from services.tts_service import get_tts_service
        try:
            tts_service = get_tts_service()
            audio_bytes = tts_service.synthesize_to_bytes(ai_response, format="wav")
            
            # 음성 파일을 Base64로 인코딩하여 전송
            import base64
            audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
            
        except Exception as e:
            logger.error(f"TTS 처리 실패: {e}")
            audio_base64 = None
        
        return {
            "success": True,
            "user_text": user_text,
            "ai_response": ai_response,
            "audio_base64": audio_base64,
            "usage": chat_response.usage
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"음성 채팅 처리 중 오류: {e}")
        raise HTTPException(status_code=500, detail=f"음성 채팅 처리 중 오류: {str(e)}")

@router.get("/check")
async def check_chat_service():
    """채팅 서비스 상태 확인"""
    try:
        # API 키 확인
        api_key = get_deepseek_api_key()
        
        # 간단한 테스트 요청
        test_messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello, this is a test message."}
        ]
        
        await call_deepseek_api(test_messages, temperature=0.1, max_tokens=10)
        
        return {
            "status": "ok",
            "message": "채팅 서비스가 정상 작동 중입니다.",
            "deepseek_api": "연결 성공"
        }
        
    except Exception as e:
        logger.error(f"채팅 서비스 확인 실패: {e}")
        raise HTTPException(status_code=500, detail=f"채팅 서비스 확인 실패: {str(e)}")