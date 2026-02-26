from typing import Dict, Optional, Tuple

from PySide6.QtCore import QObject, QThread

from core.events.qt_bus import EVENT_BUS


class BaseService(QObject):
    """
    비즈니스 로직을 담당하는 Service의 기본 클래스이다.
    공통적인 설정이나 리소스 관리, 스레드 관리를 수행한다.
    """

    def __init__(self):
        super().__init__()
        # 로그 소스 이름 설정 (클래스 이름 자동 사용)
        self.log_source = self.__class__.__name__

        # 비동기 작업용 워커 저장소
        # 키: worker_id, 값: (QThread, QObject)
        self._active_workers: Dict[str, Tuple[QThread, QObject]] = {}

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
    # [내부 전용] Thread & Worker Management
    # ==========================================================
    def _setup_worker_thread(
        self,
        worker: QObject,
        worker_id: Optional[str] = None,
        force_interrupt: bool = False,
    ) -> Optional[Tuple[QThread, QObject]]:
        """
        워커를 스레드에 배치하고 실행 준비를 마친다. (실행은 하지 않음)

        Args:
            worker:     실행할 워커 객체 (QObject 상속)
            worker_id:  워커 식별자 (중복 방지 및 관리용)
            force_interrupt:
                        '저리 비켜! 내가 할 거야.'
                        사용자가 똑같은 작업을 요청했을 때(예를 들어 똑같은 버튼을 연달아 계속 누를 경우)
                        이전 작업을 종료 시키고 새로운 명령을 수행할 지, 아니면 기존 작업을 유지할 지 이 파라미터를 통해 결정한다
                        True:   기존 실행 중인 같은 ID의 작업을 강제 종료(= 뒤따라 들어온 새로운 명령을 수행)
                        False:  기존 실행 중인 같은 ID의 작업을 계속 수행(= 뒤따라 들어온 새로운 명령을 무시)
        Returns:
            (thread, worker) 튜플. 실행 실패 시(중복 등) None 반환.
        """
        # 0. 기존 작업 확인 및 처리
        if worker_id and worker_id in self._active_workers:
            existing_thread, _ = self._active_workers[worker_id]

            # 스레드가 아직 살아있다면?
            if existing_thread.isRunning():
                if force_interrupt:
                    # [긴급] 기존 작업 강제 종료하고 내가 들어감
                    self.log_warning(
                        f"긴급 요청: 기존 작업({worker_id})을 중단하고 새 작업을 시작합니다."
                    )
                    # cleanup_worker를 부르면 딕셔너리에서 지우고 스레드도 끈다
                    self._cleanup_worker(worker_id=worker_id)
                else:
                    # [일반] 자리가 없으므로 포기
                    self.log_warning(
                        f"워커({worker_id})가 이미 실행 중입니다. 새로운 요청은 무시됩니다."
                    )
                    return None
            else:
                # 죽어있는 스레드라면 정리하고 진행
                self._cleanup_worker(worker_id=worker_id)

        # 1. 스레드 생성
        thread = QThread()

        # 2. 워커를 스레드로 이동
        worker.moveToThread(thread)

        # 3. 워커가 에러를 내면 로그로 남김
        if hasattr(worker, "worker_error_occurred"):
            worker.worker_error_occurred.connect(
                lambda msg: self.log_error(f"워커({worker_id}) 에러 발생: {msg}")
            )
            worker.worker_error_occurred.connect(
                lambda msg: self._cleanup_worker(worker_id=worker_id)
            )

        # 4. 생명주기 및 정리 '예약'
        # 스레드 시작 시 워커 동작 (호출자가 thread.started.connect(worker.run) 등을 추가로 할 수 있음.
        # 하지만 보통 worker.run이 슬롯이라면 여기서 연결해주는게 편함.
        # **주의**: Worker마다 실행 메서드 이름이 다를 수 있음(run, process, start 등).
        # 따라서 여기서는 '실행' 로직은 연결하지 않고, '정리' 로직만 연결함.

        # 워커가 일을 다 마치면(worker_task_finished 시그널) -> 자동 정리
        if hasattr(worker, "worker_task_finished"):
            # 워커 종료 -> 스레드 종료 요청 -> 객체 삭제 -> 딕셔너리 정리
            worker.worker_task_finished.connect(thread.quit)
            worker.worker_task_finished.connect(worker.deleteLater)
            thread.finished.connect(thread.deleteLater)
            # cleanup_worker를 통해 딕셔너리에서도 안전하게 제거
            worker.worker_task_finished.connect(
                lambda: self._cleanup_worker(
                    thread=thread, worker=worker, worker_id=worker_id
                )
            )

        # 5. 관리목록에 등록
        if worker_id:
            self._active_workers[worker_id] = (thread, worker)
            self.log_info(f"워커({worker_id}) 설정 완료. 대기 중...")

        return thread, worker

    def _cleanup_worker(
        self,
        thread: QThread = None,
        worker: QObject = None,
        worker_id: Optional[str] = None,
        force: bool = False,
    ):
        """
        스레드와 워커를 안전하게 종료하고 정리한다.
        """
        # 1. 대상 찾기
        target_thread = thread

        # ID로 조회
        if worker_id and worker_id in self._active_workers:
            stored_thread, stored_worker = self._active_workers[worker_id]

            # 파라미터가 없으면 저장된 놈을 타겟으로
            if target_thread is None:
                target_thread = stored_thread

            # [Race Condition 방지]
            # cleanup_worker가 호출된 시점에 이미 같은 ID로 "새로운 작업"이 시작되었을 수 있다.
            # 이 경우, 딕셔너리에 있는 스레드(새 작업)는 건드리지 않고, 종료 요청된 스레드(target_thread)만 조용히 정리해야 한다.
            # 만약 여기서 stored_thread를 건드리면, 방금 막 시작된 새 작업이 영문도 모른 채 강제 종료되는 대참사가 벌어진다.
            if target_thread != stored_thread:
                self.log_warning(
                    f"Cleanup 경고: ID({worker_id})의 활성 스레드가 변경되었습니다. 건너뜁니다."
                )
                return

        # 2. 스레드 정지
        # 스레드가 예기치 않게 먼저 죽어있더라도 (deleteLater 등으로 인해)
        # 앱이 크래시되지 않고 "이미 삭제된 스레드입니다" 로그만 남기고 안전하게 넘어가기 위해 try-except로 감싼다.
        try:
            if target_thread and target_thread.isRunning():
                self.log_info(
                    f"스레드 종료 요청: {worker_id if worker_id else 'Anonymous'}"
                )
                if force:
                    self.log_warning(f"비상 정지! {worker_id} 스레드 즉시 종료 시도")
                    target_thread.terminate()  # 강제 종료
                    target_thread.wait()  # 완전히 종료될 때까지 대기
                else:
                    # 정상적인 종료
                    target_thread.requestInterruption()
                    target_thread.quit()  # 이벤트 루프 종료 요청
                    if not target_thread.wait(1000):    # 1초 대기
                        self.log_warning(f"스레드가 응답하지 않습니다: {worker_id}")
        except RuntimeError:
            self.log_info(f"이미 삭제된 스레드입니다. (Cleanup): {worker_id}")

        # 3. 목록에서 제거
        if worker_id and worker_id in self._active_workers:
            del self._active_workers[worker_id]
            self.log_info(f"활성 워커 목록에서 제거됨: {worker_id}")

    # ==========================================================
    # [외부 접근] 워커 관리
    # ==========================================================
    def start_worker(
        self,
        worker: QObject,
        worker_id: Optional[str] = None,
        force_interrupt: bool = False,
    ) -> Optional[QThread]:
        """
        [편의 메서드] 워커 설정부터 실행까지 한 번에 수행한다.
        보편적인 워커 패턴 (worker.run 메서드 보유)을 따를 때 유용하다.

        Args:
            worker: 실행할 워커
            worker_id: 워커 식별자
            force_interrupt: 강제 실행 여부 (Emergency Stop 등 긴급 동작을 위한 워커 생성 시 사용)

        Returns:
            실행된 스레드 객체 (실패 시 None)
        """
        result = self._setup_worker_thread(worker, worker_id, force_interrupt)

        # 설정 실패(중복 실행 방지 등) 시 None 반환
        if result is None:
            return None

        thread, worker = result

        # 'run' 메서드가 있다면 스레드 시작 시 자동 실행 연결
        if hasattr(worker, "run") and callable(getattr(worker, "run")):
            thread.started.connect(worker.run)
        else:
            self.log_warning(
                f"워커({worker_id})에 'run' 메서드가 없어 자동 실행되지 않았습니다. 별도 연결이 필요할 수 있습니다."
            )

        thread.start()
        return thread

    def stop_worker(self, worker_id: str):
        """ID에 해당하는 워커와 스레드를 종료하고 정리한다."""
        self._cleanup_worker(worker_id=worker_id)

    def force_stop_worker(self, worker_id: str):
        """
        ID에 해당하는 워커와 스레드를 강제로 종료하고 정리
            프로그램 종료, 심각한 에러 발생 후 자동복구 루틴, 비상정지 등에 사용될 수 있다
        """
        self._cleanup_worker(worker_id=worker_id, force=True)

    def cleanup_all_workers(self):
        """
        관리 중인 모든 워커와 스레드를 정리
        서비스가 종료되거나 리셋될 때 "모든 활성 워커를 싹 정리"하는 메서드
        """
        if not self._active_workers:
            return

        self.log_info(f"모든 활성 워커 정리 시작 ({len(self._active_workers)}개)")
        # 딕셔너리 크기가 변하면 안 되므로 키 복사본으로 순회
        for worker_id in list(self._active_workers.keys()):
            self._cleanup_worker(worker_id=worker_id)
