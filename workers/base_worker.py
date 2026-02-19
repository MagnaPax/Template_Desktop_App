from PySide6.QtCore import QObject, Signal

from core.events.qt_bus import EVENT_BUS


class BaseWorker(QObject):
    """
    백그라운드 작업을 수행하는 Worker의 기본 클래스이다.
    작업 상태(시작, 종료, 에러)를 시그널로 알린다.
    """

    worker_task_finished = Signal()  # 작업 완료 시
    worker_error_occurred = Signal(str)  # 에러 발생 시 (메시지)

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

    # ==========================================================
    # [외부 접근] 작업 실행 및 종료
    # ==========================================================
    def run(self):
        """실제 작업을 수행하는 메서드이다. 하위 클래스에서 오버라이드해야 한다."""
        try:
            self.process()
            self.worker_task_finished.emit()
        except Exception as e:
            self.worker_error_occurred.emit(str(e))

    def process(self):
        """작업 로직을 구현한다."""
        raise NotImplementedError("하위 클래스에서 구현해야 한다.")
