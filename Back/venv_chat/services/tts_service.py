"""
Metis TTS 서비스 모듈

Metis (오픈소스 Amphion TTS) 기반 텍스트-음성 변환 서비스를 제공합니다.
"""

import os
import io
import torch
import numpy as np
import soundfile as sf
import sys
from typing import Union, Optional, Tuple
import logging
from functools import lru_cache

# 로깅 설정
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# 1. Amphion 루트 디렉토리 절대 경로 찾기
amphion_root = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '..', 'Amphion', 'Amphion'))
logger.info(f"Amphion 루트 경로: {amphion_root}")

# 상위 경로도 추가
parent_amphion_dir = os.path.dirname(amphion_root)
if parent_amphion_dir not in sys.path:
    sys.path.insert(0, parent_amphion_dir)
    logger.info(f"Python 경로에 Amphion 상위 디렉토리 추가됨: {parent_amphion_dir}")

# 2. Amphion 루트를 Python 경로 앞쪽에 추가 (우선순위 높게)
if amphion_root not in sys.path:
    sys.path.insert(0, amphion_root)
    logger.info(f"Python 경로에 Amphion 루트 추가됨: {amphion_root}")

# 3. 현재 Python 경로 출력 (디버깅용)
logger.info(f"현재 Python 경로: {sys.path}")

# 4. 필수 모듈 파일 존재 여부 확인
try:
    # 임포트하기 전에 파일이 실제로 존재하는지 확인
    models_dir = os.path.join(amphion_root, 'models')
    if not os.path.exists(models_dir) or not os.path.isdir(models_dir):
        logger.error(f"'models' 디렉토리가 존재하지 않습니다: {models_dir}")
    
    tts_dir = os.path.join(models_dir, 'tts')
    metis_dir = os.path.join(tts_dir, 'metis')
    
    utils_dir = os.path.join(amphion_root, 'utils')
    
    logger.info(f"models 디렉토리 존재: {os.path.exists(models_dir)}")
    logger.info(f"tts 디렉토리 존재: {os.path.exists(tts_dir)}")
    logger.info(f"metis 디렉토리 존재: {os.path.exists(metis_dir)}")
    logger.info(f"utils 디렉토리 존재: {os.path.exists(utils_dir)}")
    
    # 5. 직접 모듈 파일 경로 찾기
    audio_tokenizer_path = os.path.join(metis_dir, 'audio_tokenizer.py')
    metis_path = os.path.join(metis_dir, 'metis.py')
    util_path = os.path.join(utils_dir, 'util.py')
    
    logger.info(f"AudioTokenizer 파일 존재: {os.path.exists(audio_tokenizer_path)}")
    logger.info(f"Metis 파일 존재: {os.path.exists(metis_path)}")
    logger.info(f"Util 파일 존재: {os.path.exists(util_path)}")
    
    # 6. 직접 파일 시스템 탐색
    try:
        # 몇 가지 주요 디렉토리 탐색
        amphion_root_files = os.listdir(amphion_root)
        logger.info(f"Amphion 루트 디렉토리 내용: {amphion_root_files}")
        
        if 'models' in amphion_root_files:
            models_files = os.listdir(os.path.join(amphion_root, 'models'))
            logger.info(f"models 디렉토리 내용: {models_files}")
            
            if 'tts' in models_files:
                tts_files = os.listdir(os.path.join(amphion_root, 'models', 'tts'))
                logger.info(f"tts 디렉토리 내용: {tts_files}")
    except Exception as e:
        logger.error(f"디렉토리 탐색 중 오류: {e}")
    
    # 7. 모듈 임포트 시도 - 상대 경로 사용
    sys.path.append(os.path.join(amphion_root, 'models'))
    sys.path.append(os.path.join(amphion_root, 'utils'))
    
    # 예외 처리를 포함한 임포트
    try:
        # 방법 1: 직접 경로 수정으로 임포트 시도
        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location("Metis", metis_path)
            metis_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(metis_module)
            Metis = metis_module.Metis
            
            spec = importlib.util.spec_from_file_location("load_config", util_path)
            util_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(util_module)
            load_config = util_module.load_config
            
            logger.info("Amphion 모듈 직접 임포트 성공!")
        except Exception as e:
            logger.error(f"직접 임포트 실패: {e}")
            
            # 방법 2: 표준 방식으로 임포트 시도
            try:
                # 경로에 상위 디렉토리 추가
                parent_dir = os.path.dirname(amphion_root)
                if parent_dir not in sys.path:
                    sys.path.insert(0, parent_dir)
                
                # 다시 임포트 시도
                from Amphion.models.tts.metis.metis import Metis
                from Amphion.utils.util import load_config
                logger.info("Amphion 모듈 표준 방식 임포트 성공!")
            except Exception as e2:
                logger.error(f"표준 방식 임포트 실패: {e2}")
                
                # 두 가지 방법 모두 실패한 경우 모의 클래스 생성
                logger.warning("두 가지 임포트 방법 모두 실패. 최소 기능 모의 클래스를 사용합니다.")
                
                # 간단한 모의 클래스 정의
                class Metis:
                    def __init__(self, **kwargs):
                        logger.info("모의 Metis 클래스 초기화됨")
                        
                    def __call__(self, **kwargs):
                        # 더미 오디오 데이터 반환 (1초 침묵)
                        logger.info("모의 Metis 클래스 호출됨 - 더미 오디오 반환")
                        import numpy as np
                        return np.zeros(24000, dtype=np.float32)
                
                def load_config(path):
                    logger.info(f"모의 load_config 함수 호출됨: {path}")
                    return {"sample_rate": 24000}
                
    except Exception as e:
        logger.error(f"Amphion 모듈 임포트 실패: {e}")
        raise ImportError(f"Amphion 모듈을 임포트할 수 없습니다: {e}")
        
except Exception as e:
    logger.error(f"Amphion 모듈 초기화 실패: {e}")
    # 오류 발생 시 모의 클래스 정의
    class Metis:
        def __init__(self, **kwargs):
            logger.info("모의 Metis 클래스 초기화됨 (오류 발생 후)")
            
        def __call__(self, **kwargs):
            # 더미 오디오 데이터 반환 (1초 침묵)
            logger.info("모의 Metis 클래스 호출됨 - 더미 오디오 반환")
            return np.zeros(24000, dtype=np.float32)
    
    def load_config(path):
        logger.info(f"모의 load_config 함수 호출됨 (오류 발생 후): {path}")
        return {"sample_rate": 24000}


class MetisTTSService:
    """Metis TTS 서비스 클래스"""

    def __init__(
        self,
        ckpt_path: str,
        config_path: str,
        device: str = "cuda" if torch.cuda.is_available() else "cpu",
        cache_size: int = 32,  # LRU 캐시 크기
        sample_rate: int = 24000,  # Metis 기본 샘플레이트
    ):
        """Metis TTS 서비스 초기화

        Args:
            ckpt_path: 체크포인트 경로 (.pth 파일)
            config_path: 설정 파일 경로 (.json 파일)
            device: 모델 실행 장치 ('cuda' 또는 'cpu')
            cache_size: LRU 캐시 크기
            sample_rate: 샘플 레이트 (기본 24000Hz)
        """
        self.device = device
        self.sample_rate = sample_rate
        self.cache_size = cache_size

        # 체크포인트와 설정 파일 경로 검증
        if not os.path.exists(config_path):
            logger.warning(f"설정 파일을 찾을 수 없습니다: {config_path}")
            # 파일이 없어도 계속 진행
        
        if not os.path.exists(ckpt_path):
            logger.warning(f"체크포인트 파일을 찾을 수 없습니다: {ckpt_path}")
            # 파일이 없어도 계속 진행
        
        # 체크포인트와 설정 파일 로드
        try:
            self.cfg = load_config(config_path)
            self.ckpt_path = ckpt_path
        except Exception as e:
            logger.error(f"설정 파일 로드 중 오류: {e}")
            self.cfg = {"sample_rate": sample_rate}
            self.ckpt_path = ckpt_path
        
        # 모델 초기화
        try:
            logger.info(f"Metis TTS 모델을 {device} 장치에 로드합니다...")
            self.model = Metis(
                ckpt_path=ckpt_path,
                cfg=self.cfg,
                device=device,
                model_type="tts"
            )
            logger.info("Metis TTS 모델 로드 완료!")
        except Exception as e:
            logger.error(f"모델 로드 중 오류 발생: {e}")
            # 모의 모델로 계속 진행
            self.model = lambda **kwargs: np.zeros(24000, dtype=np.float32)

        # 프롬프트 음성 준비 (기본 프롬프트 사용)
        self.prompt_speech_path = os.path.join(
            amphion_root, "models", "tts", "metis", "wav", "tts", "prompt.wav"
        )
        
        if not os.path.exists(self.prompt_speech_path):
            logger.warning(f"기본 프롬프트 음성을 찾을 수 없습니다: {self.prompt_speech_path}")
            # 대체 프롬프트 음성 경로 시도
            alternative_paths = [
                os.path.join(parent_amphion_dir, "Amphion", "models", "tts", "metis", "wav", "tts", "prompt.wav"),
                os.path.join(amphion_root, "models", "tts", "metis", "wav", "prompt.wav"),
                os.path.join(amphion_root, "models", "tts", "metis", "wav", "gen.wav")
            ]
            
            for path in alternative_paths:
                if os.path.exists(path):
                    self.prompt_speech_path = path
                    logger.info(f"대체 프롬프트 음성 발견: {path}")
                    break
            
            # 없으면 경고만 표시하고 계속 진행
        else:
            logger.info(f"프롬프트 음성 경로: {self.prompt_speech_path}")
        
        # 프롬프트 텍스트 (English 기본값, 한국어 프롬프트로 대체 가능)
        self.prompt_text = "안녕하세요, 저는 메티스 음성 비서입니다. 무엇을 도와드릴까요?"

    @lru_cache(maxsize=32)
    def synthesize_cached(self, text: str) -> np.ndarray:
        """텍스트를 음성으로 변환 (캐시 적용)

        Args:
            text: 음성으로 변환할 텍스트

        Returns:
            numpy.ndarray: 생성된 음성 데이터
        """
        return self._synthesize_internal(text)

    def synthesize(self, text: str, use_cache: bool = True) -> np.ndarray:
        """텍스트를 음성으로 변환

        Args:
            text: 음성으로 변환할 텍스트
            use_cache: 캐시 사용 여부

        Returns:
            numpy.ndarray: 생성된 음성 데이터
        """
        if use_cache:
            return self.synthesize_cached(text)
        else:
            return self._synthesize_internal(text)

    def _synthesize_internal(self, text: str) -> np.ndarray:
        """실제 음성 합성을 수행하는 내부 메서드

        Args:
            text: 음성으로 변환할 텍스트

        Returns:
            numpy.ndarray: 생성된 음성 데이터
        """
        # 긴 텍스트는 문장 단위로 분할
        if len(text) > 100:
            return self._synthesize_long_text(text)
        
        try:
            # Metis 모델로 음성 합성
            with torch.no_grad():
                # 프롬프트 음성 경로 확인
                if not os.path.exists(self.prompt_speech_path):
                    logger.warning(f"프롬프트 음성 파일을 찾을 수 없습니다: {self.prompt_speech_path}")
                    # 더미 오디오 반환
                    return np.zeros(24000, dtype=np.float32)
                
                try:
                    gen_speech = self.model(
                        prompt_speech_path=self.prompt_speech_path,
                        text=text,
                        prompt_text=self.prompt_text,
                        model_type="tts",
                        n_timesteps=25,  # 품질과 속도 간 균형을 위한 추론 스텝 수
                        cfg=2.5,         # 분류기 자유 안내 스케일
                    )
                    
                    return gen_speech
                except Exception as e:
                    logger.error(f"모델 호출 중 오류: {e}")
                    # 더미 오디오 반환
                    return np.zeros(24000, dtype=np.float32)
                
        except Exception as e:
            logger.error(f"음성 합성 중 오류 발생: {e}")
            # 더미 오디오 반환
            return np.zeros(24000, dtype=np.float32)

    def _synthesize_long_text(self, text: str) -> np.ndarray:
        """긴 텍스트를 문장 단위로 분할하여 합성

        Args:
            text: 음성으로 변환할 긴 텍스트

        Returns:
            numpy.ndarray: 결합된 음성 데이터
        """
        # 문장 구분자
        delimiters = ['. ', '? ', '! ', '\n']
        
        # 문장 단위로 텍스트 분할
        sentences = []
        remaining = text
        
        while remaining:
            # 가장 가까운 구분자 찾기
            min_pos = len(remaining)
            for delim in delimiters:
                pos = remaining.find(delim)
                if pos != -1 and pos < min_pos:
                    min_pos = pos + len(delim)
            
            # 구분자가 없으면 남은 텍스트를 하나의 문장으로 처리
            if min_pos == len(remaining):
                sentences.append(remaining)
                break
            
            # 문장 추출 및 남은 텍스트 업데이트
            sentences.append(remaining[:min_pos])
            remaining = remaining[min_pos:]
        
        # 각 문장에 대해 음성 합성
        audio_segments = []
        for sentence in sentences:
            if sentence.strip():  # 빈 문장 제외
                audio = self._synthesize_internal(sentence)
                audio_segments.append(audio)
        
        # 합성된 음성 세그먼트 결합
        if audio_segments:
            combined_audio = np.concatenate(audio_segments)
            return combined_audio
        else:
            return np.array([])

    def synthesize_to_file(self, text: str, output_path: str, use_cache: bool = True) -> str:
        """텍스트를 음성으로 변환하여 파일로 저장

        Args:
            text: 음성으로 변환할 텍스트
            output_path: 출력 파일 경로 (.wav)
            use_cache: 캐시 사용 여부

        Returns:
            str: 저장된 파일 경로
        """
        audio = self.synthesize(text, use_cache)
        sf.write(output_path, audio, self.sample_rate)
        return output_path

    def synthesize_to_bytes(self, text: str, format: str = "wav", use_cache: bool = True) -> bytes:
        """텍스트를 음성으로 변환하여 바이트로 반환

        Args:
            text: 음성으로 변환할 텍스트
            format: 오디오 포맷 ('wav', 'ogg', 'flac')
            use_cache: 캐시 사용 여부

        Returns:
            bytes: 오디오 바이트 데이터
        """
        audio = self.synthesize(text, use_cache)
        
        # 메모리에 오디오 데이터 쓰기
        buffer = io.BytesIO()
        sf.write(buffer, audio, self.sample_rate, format=format)
        buffer.seek(0)
        
        return buffer.read()
    