from PySide6.QtCore import QObject

from core.events.qt_bus import EVENT_BUS


class BaseViewModel(QObject):
    """
    모든 ViewModel의 기본 클래스이다.
    QObject를 상속받아 시그널/슬롯 기능을 지원한다.
    """

    def __init__(self):
        super().__init__()
        # 로그 소스 이름 설정 (클래스 이름 자동 사용)
        self.log_source = self.__class__.__name__

    # ==========================================================
    # [외부 접근] 로깅
    # ==========================================================
    def log(self, message: str, level: str = "INFO"):
        """EventBus를 통해 로그를 전송한다."""
        EVENT_BUS.log.message.emit(self.log_source, message, level)

    def log_info(self, message: str):
        self.log(message, "INFO")

    def log_warning(self, message: str):
        self.log(message, "WARNING")

    def log_error(self, message: str):
        self.log(message, "ERROR")

    def log_debug(self, message: str):
        self.log(message, "DEBUG")
