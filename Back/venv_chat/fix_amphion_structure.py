"""
Amphion 라이브러리 구조 문제 해결 스크립트

이 스크립트는 Amphion 라이브러리 구조를 분석하고, 필요한 경우 모듈 임포트를 위한 
심볼릭 링크를 생성합니다.
"""

import os
import sys
import logging
import shutil
from pathlib import Path

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_symlinks_if_needed():
    """
    Amphion 라이브러리 구조를 분석하고 필요한 심볼릭 링크를 생성합니다.
    """
    # 기본 경로 설정
    base_dir = os.path.abspath(os.path.dirname(__file__))
    amphion_root = os.path.abspath(os.path.join(base_dir, "..", "..", "Amphion", "Amphion"))
    
    logger.info(f"기본 디렉토리: {base_dir}")
    logger.info(f"Amphion 루트 경로: {amphion_root}")
    
    if not os.path.exists(amphion_root):
        logger.error(f"Amphion 루트 디렉토리가 존재하지 않습니다: {amphion_root}")
        return False
    
    # 1. 디렉토리 구조 분석
    amphion_contents = os.listdir(amphion_root)
    logger.info(f"Amphion 디렉토리 내용: {amphion_contents}")
    
    # 2. 'models' 디렉토리 찾기 또는 링크 생성
    models_expected_dir = os.path.join(amphion_root, "models")
    models_actual_dir = None
    
    # 실제 models 디렉토리 찾기
    for item in amphion_contents:
        if item.lower() == "models":
            models_actual_dir = os.path.join(amphion_root, item)
            break
    
    # models 디렉토리가 없다면 찾거나 생성
    if models_actual_dir is None:
        # 다른 가능한 위치 확인
        candidate_dirs = [
            os.path.join(amphion_root, "..", "models"),
            os.path.join(amphion_root, "..", "..", "models")
        ]
        
        for candidate in candidate_dirs:
            if os.path.exists(candidate) and os.path.isdir(candidate):
                models_actual_dir = candidate
                break
        
        if models_actual_dir is None:
            # 디렉토리가 없으면 생성
            os.makedirs(models_expected_dir, exist_ok=True)
            models_actual_dir = models_expected_dir
            logger.info(f"models 디렉토리를 생성했습니다: {models_expected_dir}")
    
    logger.info(f"models 디렉토리 경로: {models_actual_dir}")
    
    # 3. 실제 models 디렉토리와 예상 경로가 다르면 심볼릭 링크 생성
    if models_actual_dir != models_expected_dir:
        try:
            # 기존 링크나 디렉토리가 있으면 제거
            if os.path.exists(models_expected_dir):
                if os.path.islink(models_expected_dir):
                    os.unlink(models_expected_dir)
                elif os.path.isdir(models_expected_dir):
                    shutil.rmtree(models_expected_dir)
            
            # 심볼릭 링크 생성 (Windows에서는 관리자 권한 필요)
            try:
                os.symlink(models_actual_dir, models_expected_dir, target_is_directory=True)
                logger.info(f"models 디렉토리 심볼릭 링크 생성: {models_expected_dir} -> {models_actual_dir}")
            except OSError as e:
                logger.warning(f"심볼릭 링크 생성 실패 (관리자 권한 필요): {e}")
                # 대안으로 디렉토리 복사
                shutil.copytree(models_actual_dir, models_expected_dir)
                logger.info(f"models 디렉토리 복사: {models_actual_dir} -> {models_expected_dir}")
        except Exception as e:
            logger.error(f"models 디렉토리 링크/복사 중 오류: {e}")
    
    # 4. 같은 방식으로 'utils' 디렉토리도 확인 및 링크
    utils_expected_dir = os.path.join(amphion_root, "utils")
    utils_actual_dir = None
    
    for item in amphion_contents:
        if item.lower() == "utils":
            utils_actual_dir = os.path.join(amphion_root, item)
            break
    
    if utils_actual_dir is None:
        # 다른 가능한 위치 확인
        candidate_dirs = [
            os.path.join(amphion_root, "..", "utils"),
            os.path.join(amphion_root, "..", "..", "utils")
        ]
        
        for candidate in candidate_dirs:
            if os.path.exists(candidate) and os.path.isdir(candidate):
                utils_actual_dir = candidate
                break
        
        if utils_actual_dir is None:
            # 디렉토리가 없으면 생성
            os.makedirs(utils_expected_dir, exist_ok=True)
            utils_actual_dir = utils_expected_dir
            logger.info(f"utils 디렉토리를 생성했습니다: {utils_expected_dir}")
    
    logger.info(f"utils 디렉토리 경로: {utils_actual_dir}")
    
    if utils_actual_dir != utils_expected_dir:
        try:
            # 기존 링크나 디렉토리가 있으면 제거
            if os.path.exists(utils_expected_dir):
                if os.path.islink(utils_expected_dir):
                    os.unlink(utils_expected_dir)
                elif os.path.isdir(utils_expected_dir):
                    shutil.rmtree(utils_expected_dir)
            
            # 심볼릭 링크 생성 (Windows에서는 관리자 권한 필요)
            try:
                os.symlink(utils_actual_dir, utils_expected_dir, target_is_directory=True)
                logger.info(f"utils 디렉토리 심볼릭 링크 생성: {utils_expected_dir} -> {utils_actual_dir}")
            except OSError as e:
                logger.warning(f"심볼릭 링크 생성 실패 (관리자 권한 필요): {e}")
                # 대안으로 디렉토리 복사
                shutil.copytree(utils_actual_dir, utils_expected_dir)
                logger.info(f"utils 디렉토리 복사: {utils_actual_dir} -> {utils_expected_dir}")
        except Exception as e:
            logger.error(f"utils 디렉토리 링크/복사 중 오류: {e}")
    
    # 5. Python 경로에 필요한 디렉토리 추가
    python_paths = [
        amphion_root,  # Amphion 루트 경로
        os.path.dirname(amphion_root),  # 상위 디렉토리
        models_expected_dir,  # models 디렉토리
        utils_expected_dir  # utils 디렉토리
    ]
    
    for path in python_paths:
        if path not in sys.path:
            sys.path.insert(0, path)
            logger.info(f"Python 경로에 추가됨: {path}")
    
    logger.info("Amphion 라이브러리 구조 수정 완료!")
    return True

if __name__ == "__main__":
    if create_symlinks_if_needed():
        logger.info("스크립트 실행 성공!")
    else:
        logger.error("스크립트 실행 실패!")