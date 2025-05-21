"""
Utils 모듈: TTS 서비스 및 기타 유틸리티 함수를 위한 헬퍼 모듈
"""

import os
import logging
import re
from pathlib import Path
from typing import List, Tuple

# 로깅 설정
logger = logging.getLogger(__name__)

def ensure_dir_exists(dir_path: str) -> str:
    """디렉토리가 존재하는지 확인하고, 없으면 생성합니다.
    
    Args:
        dir_path: 확인할 디렉토리 경로
        
    Returns:
        str: 생성된 디렉토리 경로
    """
    os.makedirs(dir_path, exist_ok=True)
    return dir_path

def get_file_paths(directory: str, extension: str = None) -> List[str]:
    """지정된 디렉토리에서 특정 확장자를 가진 모든 파일 경로를 가져옵니다.
    
    Args:
        directory: 스캔할 디렉토리 경로
        extension: 파일 확장자 (예: '.wav', '.txt')
        
    Returns:
        List[str]: 파일 경로 목록
    """
    file_paths = []
    
    if not os.path.exists(directory):
        logger.warning(f"디렉토리가 존재하지 않습니다: {directory}")
        return file_paths
    
    for root, _, files in os.walk(directory):
        for file in files:
            if extension is None or file.endswith(extension):
                file_paths.append(os.path.join(root, file))
    
    return file_paths

def split_text_into_sentences(text: str) -> List[str]:
    """텍스트를 문장 단위로 분할합니다.
    
    Args:
        text: 분할할 텍스트
        
    Returns:
        List[str]: 문장 목록
    """
    # 문장 구분자: 마침표, 물음표, 느낌표 뒤에 공백이 있는 경우
    delimiters = r'(?<=[.!?])\s+'
    
    # 텍스트 분할
    sentences = re.split(delimiters, text)
    
    # 빈 문장 제거
    sentences = [sentence.strip() for sentence in sentences if sentence.strip()]
    
    return sentences

def is_korean(text: str) -> bool:
    """텍스트에 한글이 포함되어 있는지 확인합니다.
    
    Args:
        text: 확인할 텍스트
        
    Returns:
        bool: 한글 포함 여부
    """
    # 한글 유니코드 범위: AC00-D7A3
    return bool(re.search(r'[\uAC00-\uD7A3]', text))

def get_project_root() -> Path:
    """프로젝트 루트 디렉토리 경로를 반환합니다.
    
    Returns:
        Path: 프로젝트 루트 경로
    """
    return Path(__file__).parent.parent