from typing import Generic, TypeVar

from PySide6.QtWidgets import QWidget

from core.events.qt_bus import EVENT_BUS

# 제네릭 타입을 사용하여 구체적인 ViewModel 타입을 명시할 수 있게 한다.
T = TypeVar("T")


class BaseView(QWidget, Generic[T]):
    """
    모든 View(Widget)의 기본 클래스이다.
    ViewModel을 연결하고 관리하는 공통 로직을 포함한다.
    """

    def __init__(self, view_model: T | None):
        super().__init__()
        self.view_model = view_model

        # 로그 소스 이름 설정 (클래스 이름 자동 사용)
        self.log_source = self.__class__.__name__

        self.init_ui()
        self.init_bindings()

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

    def init_ui(self):
        """UI 컴포넌트를 초기화하고 레이아웃을 구성한다."""
        raise NotImplementedError("하위 클래스에서 구현해야 한다.")

    def init_bindings(self):
        """ViewModel의 시그널과 View의 슬롯을 연결한다."""
        pass
