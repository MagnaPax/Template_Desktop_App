# config/paths.py
"""
경로 정보
    이 앱의 '고정'된 구조 관리
"""
from pathlib import Path

# 프로젝트 루트 (현재 파일의 부모의 부모) -> config/paths.py -> config -> root
ROOT_DIR = Path(__file__).resolve().parent.parent


# 사용자 변경 옵션 파일 위치
CONFIG_INI_PATH = ROOT_DIR / "config" / "settings.ini"

# 앱 아이콘 경로
APP_ICON = ROOT_DIR / "resources" / "KDT_logo.png"

# 스타일시트
STYLESHEET_PATH = ROOT_DIR / "styles" / "stylesheet.qss"

# 로그파일 저장 경로
LOG_DIR = ROOT_DIR / "logs"
