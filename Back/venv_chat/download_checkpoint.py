"""
Metis TTS 체크포인트 다운로드 스크립트

Hugging Face Hub에서 Metis TTS 모델 체크포인트를 다운로드합니다.
"""

import os
import sys
import logging
import argparse
from huggingface_hub import snapshot_download, hf_hub_download

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

def download_metis_checkpoint(save_dir, model_id="openai/whisper-tiny"):
    """체크포인트를 다운로드합니다.
    
    Args:
        save_dir: 저장 디렉토리
        model_id: 모델 ID (기본: "openai/whisper-tiny")
        
    Returns:
        str: 다운로드된 파일 경로
    """
    try:
        # 저장 디렉토리 생성
        os.makedirs(save_dir, exist_ok=True)
        
        # 체크포인트 다운로드
        logger.info(f"체크포인트 다운로드 중: {model_id}")
        
        # 두 가지 방법 제공
        try:
            # 방법 1: snapshot_download 사용
            checkpoint_dir = snapshot_download(
                repo_id=model_id,
                repo_type="model",
                local_dir=save_dir,
                allow_patterns=["*.pth", "*.safetensors", "*.bin"],
            )
            logger.info(f"체크포인트 다운로드 완료: {checkpoint_dir}")
            return checkpoint_dir
        except Exception as e:
            logger.warning(f"snapshot_download 실패: {e}")
            
            # 방법 2: hf_hub_download 사용
            file_path = hf_hub_download(
                repo_id=model_id,
                filename="model.safetensors",  # 파일 이름 수정 가능
                repo_type="model",
                local_dir=save_dir,
            )
            logger.info(f"체크포인트 다운로드 완료: {file_path}")
            return file_path
            
    except Exception as e:
        logger.error(f"체크포인트 다운로드 실패: {e}")
        raise

def main():
    parser = argparse.ArgumentParser(description="Metis TTS 체크포인트 다운로드")
    parser.add_argument("--model-id", type=str, default="amphion/maskgct", help="모델 ID")
    parser.add_argument("--save-dir", type=str, default="../Amphion/Amphion/pretrained", help="저장 디렉토리")
    parser.add_argument("--output-name", type=str, default="metis-korean-base.pth", help="출력 파일 이름")
    
    args = parser.parse_args()
    
    # 경로 정규화
    save_dir = os.path.abspath(args.save_dir)
    
    # 체크포인트 다운로드
    try:
        checkpoint_path = download_metis_checkpoint(save_dir, args.model_id)
        
        # 결과 출력
        logger.info(f"체크포인트 다운로드 완료: {checkpoint_path}")
        logger.info(f"저장 디렉토리: {save_dir}")
        
        # 파일 이름 변경 (필요 시)
        if args.output_name and not os.path.basename(checkpoint_path) == args.output_name:
            output_path = os.path.join(save_dir, args.output_name)
            try:
                os.rename(checkpoint_path, output_path)
                logger.info(f"파일 이름 변경: {checkpoint_path} -> {output_path}")
            except Exception as e:
                logger.warning(f"파일 이름 변경 실패: {e}")
        
    except Exception as e:
        logger.error(f"체크포인트 다운로드 중 오류: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()