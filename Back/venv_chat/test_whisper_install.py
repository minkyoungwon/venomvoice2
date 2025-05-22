"""
Whisper 설치 및 테스트 스크립트

이 스크립트는 Whisper 모델을 설치하고 기본 테스트를 수행합니다.
"""

import os
import sys
import logging
import tempfile
import asyncio
from pathlib import Path

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_whisper_import():
    """Whisper 모듈 임포트 테스트"""
    try:
        import whisper
        from faster_whisper import WhisperModel
        import torch
        
        logger.info("✅ Whisper 모듈 임포트 성공")
        logger.info(f"   - OpenAI Whisper: 사용 가능")
        logger.info(f"   - Faster Whisper: 사용 가능")
        logger.info(f"   - PyTorch: {torch.__version__}")
        logger.info(f"   - CUDA 사용 가능: {torch.cuda.is_available()}")
        
        if torch.cuda.is_available():
            logger.info(f"   - CUDA 장치 수: {torch.cuda.device_count()}")
            for i in range(torch.cuda.device_count()):
                logger.info(f"   - GPU {i}: {torch.cuda.get_device_name(i)}")
        
        return True
    except ImportError as e:
        logger.error(f"❌ Whisper 모듈 임포트 실패: {e}")
        return False

def test_whisper_model_download():
    """Whisper 모델 다운로드 테스트"""
    try:
        from faster_whisper import WhisperModel
        import torch
        
        device = "cuda" if torch.cuda.is_available() else "cpu"
        compute_type = "float16" if device == "cuda" else "int8"
        
        logger.info(f"모델 다운로드 테스트 시작 (device: {device})")
        
        # base 모델 다운로드 (실제 사용할 모델)
        model = WhisperModel("base", device=device, compute_type=compute_type)
        
        logger.info("✅ Whisper 모델 다운로드 성공")
        return model
    except Exception as e:
        logger.error(f"❌ Whisper 모델 다운로드 실패: {e}")
        return None

def create_test_audio():
    """테스트용 오디오 파일 생성 (간단한 사인파)"""
    try:
        import numpy as np
        import soundfile as sf
        
        # 1초 길이의 440Hz 사인파 생성
        sample_rate = 16000
        duration = 1.0
        frequency = 440  # A4 note
        
        t = np.linspace(0, duration, int(sample_rate * duration), False)
        wave = 0.3 * np.sin(2 * np.pi * frequency * t)
        
        # 임시 파일로 저장
        temp_file = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        sf.write(temp_file.name, wave, sample_rate)
        
        logger.info(f"테스트 오디오 파일 생성: {temp_file.name}")
        return temp_file.name
    except Exception as e:
        logger.error(f"테스트 오디오 파일 생성 실패: {e}")
        return None

async def test_stt_service():
    """STT 서비스 테스트"""
    try:
        # 현재 디렉토리를 Python 경로에 추가
        current_dir = os.path.dirname(os.path.abspath(__file__))
        if current_dir not in sys.path:
            sys.path.insert(0, current_dir)
        
        # STT 서비스 임포트 시도
        try:
            from services.stt_service import STTService
            logger.info("STT 서비스 모듈 임포트 성공")
        except ImportError as e:
            logger.warning(f"STT 서비스 모듈 임포트 실패: {e}")
            logger.info("기본 STT 테스트로 진행합니다...")
            
            # 기본 STT 테스트
            from faster_whisper import WhisperModel
            import torch
            
            device = "cuda" if torch.cuda.is_available() else "cpu"
            compute_type = "float16" if device == "cuda" else "int8"
            
            logger.info("기본 Whisper 모델로 STT 테스트...")
            model = WhisperModel("base", device=device, compute_type=compute_type)
            
            # 테스트 오디오 파일 생성
            test_audio_path = create_test_audio()
            if not test_audio_path:
                logger.error("테스트 오디오 파일을 생성할 수 없습니다")
                return False
            
            try:
                # STT 테스트 실행
                logger.info("STT 테스트 실행 중...")
                segments, info = model.transcribe(
                    test_audio_path,
                    language="ko",
                    vad_filter=True,
                    vad_parameters={"min_silence_duration_ms": 500}
                )
                
                transcript = " ".join([segment.text for segment in segments])
                
                logger.info(f"✅ STT 테스트 성공!")
                logger.info(f"   감지된 언어: {info.language} (확률: {info.language_probability:.2f})")
                logger.info(f"   인식 결과: '{transcript}'")
                logger.info(f"   (참고: 테스트 오디오는 사인파이므로 의미있는 결과가 나오지 않을 수 있습니다)")
                
                return True
            finally:
                # 임시 파일 정리
                if os.path.exists(test_audio_path):
                    os.unlink(test_audio_path)
        
        # STT 서비스 클래스 테스트
        logger.info("STT 서비스 초기화 중...")
        stt_service = STTService(model_size="base")
        
        # 테스트 오디오 파일 생성
        test_audio_path = create_test_audio()
        if not test_audio_path:
            logger.error("테스트 오디오 파일을 생성할 수 없습니다")
            return False
        
        try:
            # 오디오 파일을 바이트로 읽기
            with open(test_audio_path, 'rb') as f:
                audio_bytes = f.read()
            
            # STT 테스트 실행
            logger.info("STT 테스트 실행 중...")
            transcript = await stt_service.transcribe(audio_bytes, language="ko")
            
            logger.info(f"✅ STT 서비스 테스트 성공!")
            logger.info(f"   인식 결과: '{transcript}'")
            logger.info(f"   (참고: 테스트 오디오는 사인파이므로 의미있는 결과가 나오지 않을 수 있습니다)")
            
            return True
        finally:
            # 임시 파일 정리
            if os.path.exists(test_audio_path):
                os.unlink(test_audio_path)
    
    except Exception as e:
        logger.error(f"❌ STT 서비스 테스트 실패: {e}")
        return False

def test_model_info():
    """모델 정보 및 성능 테스트"""
    try:
        from faster_whisper import WhisperModel
        import torch
        
        device = "cuda" if torch.cuda.is_available() else "cpu"
        compute_type = "float16" if device == "cuda" else "int8"
        
        logger.info("모델 정보 확인 중...")
        model = WhisperModel("base", device=device, compute_type=compute_type)
        
        logger.info("✅ 모델 정보:")
        logger.info(f"   - 모델 크기: base")
        logger.info(f"   - 디바이스: {device}")
        logger.info(f"   - 연산 타입: {compute_type}")
        
        return True
    except Exception as e:
        logger.error(f"❌ 모델 정보 확인 실패: {e}")
        return False

async def main():
    """메인 테스트 함수"""
    logger.info("🚀 Whisper 설치 및 테스트 시작")
    
    # 1. 임포트 테스트
    logger.info("\n🔍 1단계: 모듈 임포트 테스트")
    if not test_whisper_import():
        logger.error("모듈 임포트 실패")
        return False
    
    # 2. 모델 다운로드 테스트
    logger.info("\n📥 2단계: 모델 다운로드 테스트")
    model = test_whisper_model_download()
    if model is None:
        logger.error("모델 다운로드 실패")
        return False
    
    # 3. 모델 정보 확인
    logger.info("\n📋 3단계: 모델 정보 확인")
    if not test_model_info():
        logger.error("모델 정보 확인 실패")
        return False
    
    # 4. STT 서비스 테스트
    logger.info("\n🎤 4단계: STT 서비스 테스트")
    if not await test_stt_service():
        logger.error("STT 서비스 테스트 실패")
        return False
    
    logger.info("\n✅ 모든 테스트 완료!")
    logger.info("이제 STT 서비스를 사용할 수 있습니다.")
    
    return True

def print_next_steps():
    """다음 단계 안내"""
    print("\n" + "="*60)
    print("🎉 Whisper 설치 및 테스트 완료!")
    print("="*60)
    print("\n📋 다음 단계:")
    print("1. STT 서비스 파일 업데이트:")
    print("   - services/stt_service.py 개선된 버전으로 교체")
    print("\n2. API 라우트 파일 업데이트:")
    print("   - routes/stt.py 개선된 버전으로 교체")
    print("   - routes/chat.py 새로운 파일로 추가")
    print("\n3. FastAPI 서버 실행:")
    print("   python main.py")
    print("\n4. STT API 테스트:")
    print("   GET http://localhost:8000/api/stt/check")
    print("\n5. 프론트엔드에서 음성 기능 테스트")
    print("="*60)

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        if success:
            print_next_steps()
        else:
            logger.error("❌ 테스트 실패")
            sys.exit(1)
    except KeyboardInterrupt:
        logger.info("사용자에 의해 중단됨")
        sys.exit(0)
    except Exception as e:
        logger.error(f"예상치 못한 오류: {e}")
        sys.exit(1)