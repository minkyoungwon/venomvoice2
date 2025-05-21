"""
Amphion 라이브러리 임포트 테스트

이 스크립트는 Amphion 라이브러리를 올바르게 임포트할 수 있는지 테스트합니다.
"""

import os
import sys
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_amphion_import():
    """Amphion 라이브러리 임포트를 테스트합니다."""
    try:
        # 현재 디렉토리 경로 출력
        current_dir = os.path.abspath(os.path.dirname(__file__))
        logger.info(f"현재 디렉토리: {current_dir}")
        
        # Amphion 루트 디렉토리 경로 설정
        amphion_root = os.path.abspath(os.path.join(current_dir, "..", "..", "Amphion", "Amphion"))
        logger.info(f"Amphion 루트 경로: {amphion_root}")
        
        # Python 경로에 Amphion 루트 추가
        if amphion_root not in sys.path:
            sys.path.insert(0, amphion_root)
            logger.info(f"Python 경로에 Amphion 루트 추가됨: {amphion_root}")
        
        # 상위 디렉토리도 추가
        parent_dir = os.path.dirname(amphion_root)
        if parent_dir not in sys.path:
            sys.path.insert(0, parent_dir)
            logger.info(f"Python 경로에 상위 디렉토리 추가됨: {parent_dir}")
        
        # Python 경로 출력
        logger.info(f"현재 Python 경로: {sys.path}")
        
        # 1. 방법 1: Amphion 패키지로 임포트 시도
        try:
            logger.info("방법 1: Amphion 패키지로 임포트 시도...")
            from Amphion.models.tts.metis.metis import Metis
            from Amphion.utils.util import load_config
            logger.info("방법 1 성공: Amphion 패키지로 임포트 성공!")
            return True, "Amphion 패키지로 임포트 성공"
        except ImportError as e:
            logger.warning(f"방법 1 실패: {e}")
            
            # 2. 방법 2: 절대 경로로 임포트 시도
            try:
                logger.info("방법 2: 절대 경로로 임포트 시도...")
                from models.tts.metis.metis import Metis
                from utils.util import load_config
                logger.info("방법 2 성공: 절대 경로로 임포트 성공!")
                return True, "절대 경로로 임포트 성공"
            except ImportError as e2:
                logger.warning(f"방법 2 실패: {e2}")
                
                # 3. 방법 3: 파일 직접 로드로 임포트 시도
                try:
                    logger.info("방법 3: 파일 직접 로드로 임포트 시도...")
                    import importlib.util
                    
                    # Metis 모듈 로드
                    metis_path = os.path.join(amphion_root, "models", "tts", "metis", "metis.py")
                    if not os.path.exists(metis_path):
                        logger.error(f"metis.py 파일이 존재하지 않습니다: {metis_path}")
                        
                        # 파일 찾기 시도
                        for root, dirs, files in os.walk(amphion_root):
                            for file in files:
                                if file == "metis.py":
                                    metis_path = os.path.join(root, file)
                                    logger.info(f"metis.py 파일 발견: {metis_path}")
                                    break
                            if os.path.exists(metis_path):
                                break
                    
                    if os.path.exists(metis_path):
                        spec = importlib.util.spec_from_file_location("Metis", metis_path)
                        metis_module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(metis_module)
                        Metis = metis_module.Metis
                        
                        # util 모듈 로드
                        util_path = os.path.join(amphion_root, "utils", "util.py")
                        if not os.path.exists(util_path):
                            logger.error(f"util.py 파일이 존재하지 않습니다: {util_path}")
                            
                            # 파일 찾기 시도
                            for root, dirs, files in os.walk(amphion_root):
                                for file in files:
                                    if file == "util.py":
                                        util_path = os.path.join(root, file)
                                        logger.info(f"util.py 파일 발견: {util_path}")
                                        break
                                if os.path.exists(util_path):
                                    break
                        
                        if os.path.exists(util_path):
                            spec = importlib.util.spec_from_file_location("load_config", util_path)
                            util_module = importlib.util.module_from_spec(spec)
                            spec.loader.exec_module(util_module)
                            load_config = util_module.load_config
                            
                            logger.info("방법 3 성공: 파일 직접 로드로 임포트 성공!")
                            return True, "파일 직접 로드로 임포트 성공"
                        else:
                            logger.error("util.py 파일을 찾을 수 없습니다.")
                    else:
                        logger.error("metis.py 파일을 찾을 수 없습니다.")
                    
                    return False, "메소드 3 실패: 파일 직접 로드 실패"
                except Exception as e3:
                    logger.error(f"방법 3 실패: {e3}")
                    return False, f"모든 임포트 방법 실패: {e}, {e2}, {e3}"
    except Exception as e:
        logger.error(f"테스트 중 오류 발생: {e}")
        return False, f"테스트 중 오류 발생: {e}"

if __name__ == "__main__":
    success, message = test_amphion_import()
    if success:
        logger.info(f"테스트 성공: {message}")
        exit(0)
    else:
        logger.error(f"테스트 실패: {message}")
        exit(1)