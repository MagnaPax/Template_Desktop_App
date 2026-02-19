import configparser
import os
import sys
from pathlib import Path


class AppPaths:
    """애플리케이션 경로 정보 관리"""

    def __init__(self):

        # 앱의 루트 디렉토리 (개발/배포 환경에 따라 다르게 결정)
        self.is_packaged = self._check_is_packaged()
        self.ROOT_DIR = self._get_root_dir()

        # 설정 파일, 아이콘, 스타일시트, 로그 디렉토리 등
        self.CONFIG_INI_PATH = self.ROOT_DIR / "config" / "settings.ini"
        self.APP_ICON = self.ROOT_DIR / "resources" / "KDT_logo.png"
        self.STYLESHEET_PATH = self.ROOT_DIR / "styles" / "stylesheet.qss"
        self.LOG_DIR = self.ROOT_DIR / "logs"

    def _check_is_packaged(self) -> bool:
        """
        앱이 패키징된 실행 파일인지 판단
        1. DEV_MODE 환경변수가 1이면 강제 개발 모드 (False)
        2. sys.frozen 속성이 있으면 패키징 모드 (True)
        """
        dev_mode = os.getenv("DEV_MODE", "0").strip().lower()
        if dev_mode in ("1", "true", "yes"):
            return False

        return getattr(sys, "frozen", False)

    def _get_root_dir(self) -> Path:
        """실행 환경에 따른 루트 디렉토리 반환"""
        if self.is_packaged:
            # 배포 환경: 실행 파일이 있는 폴더
            return Path(sys.executable).resolve().parent
        else:
            # 개발 환경: 프로젝트 루트 (현재 파일의 부모의 부모)
            return Path(__file__).resolve().parent.parent


class AppConfig:
    """애플리케이션 전체 설정 및 경로 관리"""

    def __init__(self):
        self.paths = AppPaths()
        self._config = self._load_settings()

    def _load_settings(self) -> configparser.ConfigParser:
        """settings.ini 파일을 로드한다."""
        config = configparser.ConfigParser()
        if self.paths.CONFIG_INI_PATH.exists():
            config.read(str(self.paths.CONFIG_INI_PATH), encoding="utf-8")
        return config

    @property
    def is_packaged(self) -> bool:
        """앱이 패키징된 상태인지 여부"""
        return self.paths.is_packaged

    @property
    def app_name(self) -> str:
        """앱 이름을 반환한다."""
        return self._config.get("App", "APP_NAME", fallback="Quiet Zone Scanner")

    # 필요한 다른 설정값들도 프로퍼티로 추가 가능
    @property
    def version(self) -> str:
        return self._config.get("App", "VERSION", fallback="1.0.0")

    @property
    def debug(self) -> bool:
        return self._config.getboolean("App", "DEBUG", fallback=False)


# 전역 설정 인스턴스
APP_CONFIG = AppConfig()
