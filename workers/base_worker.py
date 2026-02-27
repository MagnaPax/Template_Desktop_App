from PySide6.QtCore import QObject, Signal, QThread

from core.events.qt_bus import EVENT_BUS


class BaseWorker(QObject):
    """
    백그라운드 작업을 수행하는 Worker의 기본 클래스이다.
    스레드 제어는 완전히 Service에 위임하고, 오직 비즈니스 로직에만 집중한다.
    작업 상태(성공, 실패)를 시그널로 알린다.
    """

    worker_started = Signal()          # 작업 시작 시
    worker_finished = Signal()         # 정상 완료 시
    worker_failed = Signal(str)        # 에러 발생 시

    def __init__(self):
        super().__init__()
        self.log_source = self.__class__.__name__

    # ==========================================================
    # [외부 접근] 로깅
    # ==========================================================
    def log(self, message: str, level: str = "INFO"):
        """EventBus를 통해 로그를 전송한다."""
        EVENT_BUS.log.message.emit(self.log_source, message, level)

    def log_info(self, message: str): self.log(message, "INFO")
    def log_warning(self, message: str): self.log(message, "WARNING")
    def log_error(self, message: str): self.log(message, "ERROR")
    def log_debug(self, message: str): self.log(message, "DEBUG")

    # ==========================================================
    # Entry Point
    # ==========================================================
    def run(self):
        """Service의 스레드 시작 시 연결되는 메인 진입점이다."""

        self.log_info("작업 시작")
        self.worker_started.emit()

        try:
            self.process()
        except Exception as e:
            self.log_error(f"작업 중 예외 발생: {str(e)}")
            self.worker_failed.emit(str(e))
            return  # 예외 발생 시 즉시 종료 (finished 시그널 발생 안 함)

        # 에러 없이 루프를 빠져나왔을 때만 완료 시그널 전송
        self.worker_finished.emit()

    def stop_custom_resources(self):
        """
        [선택적 오버라이드] 
        스레드 Interruption 외에 DB 커넥션 종료, 소켓 닫기 등
        Worker 내부에서 점유한 자원을 비동기적으로 해제해야 할 때 하위 클래스에서 오버라이드한다.
        """
        pass

    # ==========================================================
    # [하위 클래스 구현부]
    # ==========================================================
    def process(self):
        """작업 로직을 구현한다."""
        raise NotImplementedError("하위 클래스에서 구현해야 한다.")
