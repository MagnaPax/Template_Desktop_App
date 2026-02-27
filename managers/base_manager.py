from PySide6.QtCore import QObject

from core.events.qt_bus import EVENT_BUS


class BaseManager(QObject):
    """
    애플리케이션의 공통 상태(State)와 데이터를 보관/관리하는 매니저의 기본 클래스이다.
    여러 ViewModel에 주입(Injection)되어 공통의 진실 공급원(Single Source of Truth) 역할을 한다.

    사용 예:
        from PySide6.QtCore import Signal
        from managers.base_manager import BaseManager

        class ProgressManager(BaseManager):
            # 상태 변경을 구독자(ViewModel)에게 알리는 시그널
            progress_updated = Signal(int)

            def __init__(self):
                super().__init__()
                self._current_progress = 0  # 내부에 상태(State) 보관

            def update_progress(self, percent: int):
                self._current_progress = percent
                self.progress_updated.emit(self._current_progress)

        # ----------------------------------------------------------------
        # [A 뷰모델] (일을 시키는 애): 자신이 만든 워커를 매니저한테 등록함
        # ----------------------------------------------------------------
        class DownloadViewModel(BaseViewModel):
            def __init__(self, progress_manager: ProgressManager, service: BaseService):
                super().__init__()
                self.progress_manager = progress_manager
                self.service = service

            def start_download(self, url):
                worker = DownloadWorker(url)
                # 워커가 내는 소리(Signal)를 매니저의 상태 업데이트(Slot)에 연결한다.
                worker.worker_progressed.connect(self.progress_manager.update_progress)
                self.service.start_worker(worker)

        # ----------------------------------------------------------------
        # [B 뷰모델] (진행률 그리는 애): 매니저만 쳐다보고 화면을 갱신함
        # ----------------------------------------------------------------
        class ProgressViewModel(BaseViewModel):
            def __init__(self, progress_manager: ProgressManager):
                super().__init__()
                self.progress_manager = progress_manager
                
                # 매니저의 상태가 변하면 내 화면 갱신 함수를 호출한다.
                self.progress_manager.progress_updated.connect(self.update_ui)

            def update_ui(self, percent):
                print(f"화면에 그림: {percent}%")
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
