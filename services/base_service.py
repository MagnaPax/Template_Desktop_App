from typing import Dict, Optional, Tuple

from PySide6.QtCore import QObject, QThread

from core.events.qt_bus import EVENT_BUS


class BaseService(QObject):
    """
    비즈니스 로직 및 Worker 스레드 라이프사이클을 관리하는 Service이다.
    공통적인 설정이나 리소스 관리, 스레드 관리를 수행한다.
    단일 종료 경로(Single Exit Path)와 Race Condition 방어 로직을 포함한다.
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

    def log_info(self, message: str): self.log(message, "INFO")
    def log_warning(self, message: str): self.log(message, "WARNING")
    def log_error(self, message: str): self.log(message, "ERROR")
    def log_debug(self, message: str): self.log(message, "DEBUG")

    # ==========================================================
    # [내부 전용] Thread Setup
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
            thread: 백그라운드 작업을 실행할 컨테이너 (실행은 아직 안 된 상태)
            worker: 비즈니스 로직을 담고 있는 실제 작업자 객체
            * 실행 실패 시(중복 요청 무시 등) None 반환
        """
        # 1. 기존 작업(중복 ID) 확인 및 처리
        if worker_id and worker_id in self._active_workers:
            existing_thread, _ = self._active_workers[worker_id]

            # 같은 ID의 작업이 이미 실행 중이라면?
            if existing_thread.isRunning():
                if force_interrupt:
                    # [긴급] 저리 비켜! 내가 할 거야.
                    self.log_warning(f"긴급 요청: 기존 작업({worker_id})을 중단하고 새 작업을 시작합니다.")
                    self.stop_worker(worker_id)
                else:
                    # [일반] 기존의 작업에게 양보
                    self.log_warning(f"워커({worker_id})가 이미 실행 중입니다. 새로운 요청은 무시됩니다.")
                    return None
            else:
                # 죽어있는 스레드일 경우 정리를 위해 종료 요청
                self._finalize_worker_dict(worker_id, existing_thread)

        # 2. 스레드 생성, 워커를 스레드로 이동
        thread = QThread()
        worker.moveToThread(thread)

        # 3. 종료 시그널 연결
        # 워커가 무사히 끝나면 스레드 이벤트 루프를 종료한다.
        if hasattr(worker, "worker_finished"):
            worker.worker_finished.connect(thread.quit)
            
        # 에러가 발생해도 스레드는 종료해야 한다.
        if hasattr(worker, "worker_failed"):
            worker.worker_failed.connect(
                lambda msg: self.log_error(f"[{worker_id}] 워커 실패: {msg}")
            )
            worker.worker_failed.connect(thread.quit)

        # 4. [단일 종료 경로] 메모리 및 딕셔너리 정리
        # 스레드가 완전히 끝났을 때만 객체를 메모리에서 지운다. (C++ 충돌 방지)
        thread.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        
        # 딕셔너리 정리는 Race Condition 방어를 위해 대상 스레드 객체를 람다로 넘긴다.
        if worker_id:
            thread.finished.connect(
                lambda wid=worker_id, t=thread: self._finalize_worker_dict(wid, t)
            )
            self._active_workers[worker_id] = (thread, worker)

        self.log_info(f"[{worker_id if worker_id else 'Anonymous'}] 스레드 설정 완료 및 시작.")
        return thread, worker

    def _finalize_worker_dict(self, worker_id: str, target_thread: QThread):
        """
        스레드 종료 시 호출되어 딕셔너리에서 워커를 제거한다. (Race Condition 방어)
        """
        if worker_id in self._active_workers:
            stored_thread, _ = self._active_workers[worker_id]
            
            # [Race Condition 방어]
            # 강제 종료 등으로 딕셔너리가 이미 새 스레드로 덮어씌워졌다면,
            # 현재 끝난 스레드(target_thread)는 딕셔너리를 건드리지 않는다.
            if stored_thread is target_thread:
                del self._active_workers[worker_id]
                self.log_debug(f"[{worker_id}] 활성 워커 목록에서 안전하게 제거되었습니다.")
            else:
                self.log_debug(f"[{worker_id}] 딕셔너리 활성 스레드가 변경되었습니다. 정리를 건너뜁니다.")

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
        워커 설정 & 실행
        보편적인 워커 패턴 (worker.run 메서드 보유)을 따를 때 유용하다.

        Args:
            worker:         실행할 워커
            worker_id:      워커 식별자
            force_interrupt:강제 실행 여부 (Emergency Stop 등 기존 작업을 강제 중단시키고 새 작업으로 대체할 때 사용)

        Returns:
            thread:         실행된 스레드 객체 (실패 시 None)
        """
        result = self._setup_worker_thread(worker, worker_id, force_interrupt)
        
        # 설정 실패(중복 실행 방지 등) 시 None 반환
        if result is None:
            return None
            
        thread, worker = result
        
        # 'run' 메서드가 있다면 자동 실행 연결
        if hasattr(worker, "run") and callable(getattr(worker, "run")):
            thread.started.connect(worker.run)
        else:
            self.log_warning(f"[{worker_id}] 워커에 'run' 메서드가 없어 자동 연결되지 않았습니다.")

        thread.start()
        return thread

    def stop_worker(self, worker_id: str):
        """ID에 해당하는 워커와 스레드를 안전하게 중단 요청한다."""
        if worker_id not in self._active_workers:
            return

        thread, worker = self._active_workers[worker_id]

        self.log_info(f"[{worker_id}] 종료 요청 중...")
        
        # 1. Thread 자체에 협력적 중단 요청 (가장 안전)
        thread.requestInterruption()

        # 2. Worker 내부 특수 자원 해제 로직 호출
        if hasattr(worker, "stop_custom_resources"):
            worker.stop_custom_resources()
            
        # 3. 이벤트 루프 종료 요청
        try:
            thread.quit()
        except RuntimeError:
            self.log_info(f"[{worker_id}] 이미 삭제된 스레드이다.")

        # thread.finished 시그널 발생 시 _finalize_worker_dict가 깔끔하게 정리한다.

    def force_stop_worker(self, worker_id: str):
        """
        응답이 없을 때 사용하는 비상 정지.
        메모리 누수나 데드락 위험이 있으므로 최후 수단으로만 사용한다.
        """
        if worker_id not in self._active_workers:
            return
            
        thread, _ = self._active_workers[worker_id]
        self.log_warning(f"[{worker_id}] 비상 정지 (terminate) 시도!")
        
        try:
            thread.terminate()
            thread.wait() # 완전히 죽을 때까지 대기
        except RuntimeError:
            pass

    def cleanup_all_workers(self):
        """서비스가 종료되거나 리셋될 때 "모든 활성 워커를 싹 정리"하는 메서드"""
        if not self._active_workers:
            return

        # 딕셔너리 크기가 변하면 안 되므로 키 복사본으로 순회
        self.log_info(f"모든 활성 워커({len(self._active_workers)}개) 정리 시작.")
        for worker_id in list(self._active_workers.keys()):
            self.stop_worker(worker_id)
