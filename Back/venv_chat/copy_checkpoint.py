"""
체크포인트 파일 복사 및 이름 변경 스크립트
"""

import os
import shutil
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 파일 경로
src_file = r"C:\src\asd\Amphion\Amphion\pretrained\t2s_model\model.safetensors"
dst_file = r"C:\src\asd\Amphion\Amphion\pretrained\metis-korean-base.pth"

# 파일 복사
if os.path.exists(src_file):
    try:
        shutil.copy2(src_file, dst_file)
        logger.info(f"파일 복사 성공: {src_file} -> {dst_file}")
    except Exception as e:
        logger.error(f"파일 복사 실패: {e}")
else:
    logger.error(f"소스 파일이 존재하지 않습니다: {src_file}")

# 파일 존재 확인
if os.path.exists(dst_file):
    logger.info(f"체크포인트 파일 준비 완료: {dst_file}")
    logger.info(f"파일 크기: {os.path.getsize(dst_file) / (1024 * 1024):.2f} MB")
else:
    logger.error(f"체크포인트 파일이 존재하지 않습니다: {dst_file}")