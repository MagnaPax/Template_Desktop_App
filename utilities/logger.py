# utilities/logger.py
"""
중앙 로깅 유틸리티
------------------
어떤 프로젝트에서든 재사용 가능한 독립적인 로깅 모듈

특징:
1. 독립성: 외부 설정(AppEnv, AppConfig 등)에 의존하지 않음
2. 주입식(Dependency Injection): 초기화 시점에 설정을 주입받음
3. 기능: 콘솔 컬러 출력, 날짜별 파일 로테이션, 에러 별도 저장
"""

import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional


# =============================================================================
# 콘솔에서 컬러 출력을 위한 포매터
# =============================================================================
class ColorFormatter(logging.Formatter):
    """
    콘솔 출력용 ANSI 색상 포매터
    """

    COLORS = {
        "DEBUG": "\x1b[36m",  # Cyan
        "INFO": "\x1b[32m",  # Green
        "WARNING": "\x1b[33m",  # Yellow
        "ERROR": "\x1b[31m",  # Red
        "CRITICAL": "\x1b[35m",  # Magenta
        "RESET": "\x1b[0m",
    }

    def format(self, record: logging.LogRecord) -> str:
        log_message = super().format(record)
        if hasattr(sys.stdout, "isatty") and sys.stdout.isatty():
            color = self.COLORS.get(record.levelname, self.COLORS["RESET"])
            return f"{color}{log_message}{self.COLORS['RESET']}"
        return log_message


# =============================================================================
# 커스텀 핸들러: 날짜별 파일 직접 생성 + 자동 로테이션
# =============================================================================
class DailyRotatingFileHandler(logging.FileHandler):
    """
    매일 날짜별로 새로운 로그 파일을 생성하는 핸들러.

    TimedRotatingFileHandler의 문제점(파일명 뒤에 날짜가 붙음, 재시작 시 app.log로 씀 등)을 해결하기 위해
    날짜가 포함된 파일명(app_YYYYMMDD.log)을 직접 생성하고 관리한다.
    """

    def __init__(
        self,
        log_dir: Path,
        prefix: str = "app",
        encoding: str = "utf-8",
        backup_count: int = 14,
    ):
        self.log_dir = log_dir
        self.prefix = prefix
        self.backup_count = backup_count
        self.current_date = datetime.now().date()

        # 오늘 날짜 파일명 계산
        filename = self._get_filename(self.current_date)

        # 부모 초기화 (파일 열기)
        super().__init__(str(filename), encoding=encoding, delay=True)

    def _get_filename(self, date_obj) -> Path:
        """날짜에 해당하는 파일명 반환"""
        date_str = date_obj.strftime("%Y%m%d")
        return self.log_dir / f"{self.prefix}_{date_str}.log"

    def emit(self, record):
        """로그를 기록할 때마다 날짜가 바뀌었는지 체크"""
        try:
            # 현재 날짜 확인
            today = datetime.now().date()

            # 날짜가 바뀌었다면 로테이션 수행
            if today != self.current_date:
                self.current_date = today
                self.close()  # 기존 파일 닫기

                # 새 파일명으로 교체
                self.baseFilename = str(self._get_filename(today))
                self.stream = self._open()  # 새 파일 열기

                # 오래된 로그 삭제
                self.cleanup_old_logs()

            super().emit(record)
        except Exception:
            self.handleError(record)

    def cleanup_old_logs(self):
        """오래된 로그 파일 삭제"""
        if self.backup_count <= 0:
            return

        try:
            # 로그 디렉토리의 모든 파일을 검색
            for log_file in self.log_dir.glob(f"{self.prefix}_*.log"):
                # 파일명에서 날짜 추출 (app_20250129.log -> 20250129)
                try:
                    date_part = log_file.stem.replace(f"{self.prefix}_", "")
                    file_date = datetime.strptime(date_part, "%Y%m%d").date()

                    # 보관 기간이 지난 파일 삭제
                    # (오늘 - 파일날짜) > 보관기간
                    if (self.current_date - file_date).days > self.backup_count:
                        os.remove(log_file)
                        # print(f"Deleted old log: {log_file}") # 디버깅용
                except (ValueError, OSError):
                    continue  # 날짜 형식이 아니거나 삭제 실패 시 무시
        except Exception:
            pass  # 청소 중 에러는 메인 로직에 영향 주지 않도록 무시


# =============================================================================
# 로거 설정 및 관리 (싱글톤)
# =============================================================================
class Logger:
    """
    [범용 로거 클래스]

    사용법:
        1. 앱 시작 지점(main)에서 초기화:
            Logger.initialize(
                app_name="MyApp",
                log_dir=Path("./logs"),
                level=logging.DEBUG
            )

        2. 어디서든 가져다 쓰기:
            from utilities.logger import get_logger
            logger = get_logger(__name__)
    """

    _instance: Optional["Logger"] = None
    _root_logger: Optional[logging.Logger] = None
    _initialized = False

    # 기본 상수 (필요하면 initialize 인자로 오버라이딩 가능하게 확장 가능)
    DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
    MESSAGE_FORMAT = "%(asctime)s | %(levelname)-8s | %(message)s"
    ERROR_FORMAT = (
        "%(asctime)s | %(levelname)s | %(pathname)s:%(lineno)d\n%(message)s\n"
    )

    LOG_KEEP_DAYS = 14  # 일반 로그 보관 기간
    ERROR_LOG_KEEP_DAYS = 30  # 에러 로그 보관 기간

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def initialize(
        cls,
        app_name: str,
        log_dir: Path,
        level: int = logging.INFO,
        console: bool = True,
    ):
        """
        로거 초기화 (설정 주입)

        Args:
            app_name: 로거 이름 (프로젝트명)
            log_dir: 로그를 저장할 폴더 경로 (이미 생성되어 있거나 생성 가능한 경로)
            level: 기본 로그 레벨 (logging.DEBUG, logging.INFO ...)
            console: 콘솔 출력 여부 (배포 시 False 권장)
        """
        if cls._initialized:
            return

        cls._initialized = True

        # 1. 로그 디렉토리 생성
        try:
            log_dir.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            print(f"❌ 로그 디렉토리 생성 실패: {log_dir} - {e}")
            return

        # 2. 루트 로거 설정
        instance = cls()
        instance._root_logger = logging.getLogger(app_name)
        instance._root_logger.setLevel(level)
        instance._root_logger.propagate = False
        instance._root_logger.handlers.clear()

        # 3. 파일 핸들러 (커스텀: 날짜별 직접 관리)

        # 일반 로그
        file_handler = DailyRotatingFileHandler(
            log_dir=log_dir,
            prefix="app",
            encoding="utf-8",
            backup_count=cls.LOG_KEEP_DAYS,
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(
            logging.Formatter(cls.MESSAGE_FORMAT, cls.DATE_FORMAT)
        )
        instance._root_logger.addHandler(file_handler)

        # 에러 로그 (별도 저장)
        error_handler = DailyRotatingFileHandler(
            log_dir=log_dir,
            prefix="error",
            encoding="utf-8",
            backup_count=cls.ERROR_LOG_KEEP_DAYS,
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(logging.Formatter(cls.ERROR_FORMAT, cls.DATE_FORMAT))
        instance._root_logger.addHandler(error_handler)

        # 5. 콘솔 핸들러
        if console:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(level)
            console_handler.setFormatter(
                ColorFormatter(cls.MESSAGE_FORMAT, cls.DATE_FORMAT)
            )
            instance._root_logger.addHandler(console_handler)

        # 6. 외부 라이브러리 노이즈 제거
        cls._suppress_noisy_loggers()

        instance._root_logger.info(f"Logger initialized for '{app_name}' at {log_dir}")
        print(f"✅ Logger initialized for '{app_name}' at {log_dir}")

    @staticmethod
    def _suppress_noisy_loggers():
        noisy_loggers = ["PyQt6", "urllib3", "PIL", "matplotlib"]
        for name in noisy_loggers:
            logging.getLogger(name).setLevel(logging.WARNING)

    def _get_child_logger(self, name: str) -> logging.Logger:
        if self._root_logger is None:
            # 아직 초기화 안 됐으면 기본 로거라도 반환 (안전장치)
            return logging.getLogger(name)
        return self._root_logger.getChild(name)


# =============================================================================
# 공개 함수
# =============================================================================
def get_logger(name: str = __name__) -> logging.Logger:
    """사용자가 사용하는 로거 획득 함수"""
    return Logger()._get_child_logger(name)


# 호환성을 위한 전역 객체(초기화 전 사용 시 기본 로거 반환됨)
logger = get_logger(__name__)

if __name__ == "__main__":
    # 테스트 코드
    print("--- Logger Utility Test ---")
    test_dir = Path("./test_logs")

    Logger.initialize(
        app_name="TestApp", log_dir=test_dir, level=logging.DEBUG, console=True
    )

    log = get_logger("MyModule")
    log.debug("디버그")
    log.info("정보")
    log.warning("경고")
    log.error("에러")
    try:
        1 / 0
    except Exception:
        log.exception("예외 발생 테스트")

    print(f"Check logs in: {test_dir.absolute()}")
