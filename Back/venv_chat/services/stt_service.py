import os
import tempfile
import torch
from faster_whisper import WhisperModel

class STTService:
    def __init__(self, model_size="base"):
        # GPU가 있으면 사용, 없으면 CPU로 실행
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.compute_type = "float16" if self.device == "cuda" else "int8"
        
        print(f"Loading Whisper model: {model_size} on {self.device}")
        self.model = WhisperModel(model_size, device=self.device, compute_type=self.compute_type)
    
    async def transcribe(self, audio_bytes, language="ko"):
        """오디오 파일을 텍스트로 변환합니다."""
        # 임시 파일 생성
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
            temp_path = temp_file.name
            temp_file.write(audio_bytes)
        
        try:
            # 음성 인식 실행
            segments, info = self.model.transcribe(
                temp_path, 
                language=language, 
                vad_filter=True,  # 음성 감지 기능 활성화
                vad_parameters={"min_silence_duration_ms": 500}  # 0.5초 이상 침묵 시 분리
            )
            
            # 결과 텍스트 합치기
            transcript = " ".join([segment.text for segment in segments])
            return transcript.strip()
            
        finally:
            # 임시 파일 삭제
            if os.path.exists(temp_path):
                os.remove(temp_path)

# 싱글톤 인스턴스
stt_service = STTService()