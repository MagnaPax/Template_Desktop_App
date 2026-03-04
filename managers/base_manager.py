from PySide6.QtCore import QObject

from core.events.qt_bus import EVENT_BUS


class BaseManager(QObject):
    """
    애플리케이션의 공통 상태(State)와 데이터를 보관/관리하는 매니저의 기본 클래스
    여러 ViewModel에 주입(Injection)되어 공통의 진실 공급원(Single Source of Truth) 역할을 한다.

    질문: 
        - "컴포넌트간의 결합도를 낮추고 이벤트를 전달하는 것"은 이벤트 버스를 사용해도 할 수 있는데 왜 또 매니저 파일을 만드나?

    답: 
        - [이벤트 버스]
            - 특징: 배달원. 메세지를 전달만 할 뿐 데이터를 저장하지 않는다.
            - 범위: 전역. import를 통해 어디에서든 쓸 수 있지만 프로젝트가 커지면 발생과 연결을 추적하기 힘든 "이벤트 스파게티" 현상 발생
            - 사용: 앱 공통 일회성 사건(Event)
                - 예:
                    - "로그 출력"
                    - "에러 발생"
                    - "작업 시작/완료"
                    - "Notification 팝업 띄우기"
            - 비유: 사내 방송

        - [매니저]
            - 특징: 데이터 저장소. 데이터를 저장하고, 이벤트를 발생시킨다.
            - 범위: 범위 제한. 필요한 뷰모델의 생성자로 주입된다. 일종의 핫라인으로 추적이 쉽다.
            - 사용: 앱 공통 비즈니스 상태(State)
                - 예:
                    - 전역 설정 데이터 (현재 다크 모드인지, 언어 설정이 무엇인지 등)
                    - 로그인 성공한 유저의 세션 정보 (유저 이름, 토큰 등)
                    - 워커의 진행 상태 백분율 (Progress)
                    - 로드된 데이터 리스트 캐싱
            - 비유: 사내 게시판


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
