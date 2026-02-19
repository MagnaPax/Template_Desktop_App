# core/events/qt_bus.py
"""
[Qt 전용 EventBus 구현체]

PySide6(Qt)의 'Signal/Slot' 메커니즘을 사용하여 구현된 실제 이벤트 버스이다.
Qt 애플리케이션(GUI가 있는 앱) 환경에서 동작한다.

이 파일은 'EventBus'라는 껍데기와 '_EventBusBackend'라는 알맹이로 나뉜다.
이렇게 나눈 이유는 'Lazy Initialization(지연 초기화)' 때문이다.
QObject는 QApplication이 생성되기 전에 만들어지면 안 되는데,
이 구조를 통해 Import 시점이 아닌, 실제 사용 시점에 QObject를 생성하여 안전성을 확보했다.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from PySide6.QtCore import QMetaMethod, QObject, Signal

# =============================================================================
# 1. 시그널 그룹 클래스 정의
# =============================================================================
# 각 클래스는 관련된 이벤트들을 묶어서 관리하는 역할을 한다.
# QObject를 상속받아야 Signal을 정의하고 사용할 수 있다.


class SystemSignals(QObject):
    """시스템 상태(에러, 알림 등)와 관련된 시그널 모음"""

    system_error_occurred = Signal(str)  # 치명적인 에러 발생 시 (메시지)
    system_notification_received = Signal(str)  # 일반적인 시스템 알림 시 (메시지)


class LogSignals(QObject):
    """로그 출력과 관련된 시그널 모음"""

    # (발생위치, 로그내용, 로그레벨)
    # 예: emit("MainEngine", "초기화 완료", "INFO")
    message = Signal(str, str, str)


class DataSignals(QObject):
    """데이터 처리 및 비즈니스 로직 관련 시그널 모음"""

    # (작업이름, 진행중여부) - 예: emit("Scan", True)
    sequence_activity_changed = Signal(str, bool)
    # (데이터리스트) - 데이터 로드 완료 시
    sequence_data_loaded = Signal(list)


# =============================================================================
# 2. 실제 백엔드 (Real QObject)
# =============================================================================
class _EventBusBackend(QObject):
    """
    실제 시그널 객체들을 보유하고 있는 '진짜' 이벤트 버스이다.
    이 객체가 생성될 때 하위 시그널 그룹들도 함께 생성된다.
    """

    def __init__(self):
        super().__init__()
        # 위에서 정의한 시그널 그룹들을 인스턴스화하여 멤버로 가짐
        self.system = SystemSignals()
        self.log = LogSignals()
        self.data = DataSignals()

        # 나중에 한꺼번에 연결을 끊거나 관리하기 위해 리스트에 담아둠
        self._signal_groups = [self.system, self.log, self.data]

    def disconnect_all(self, signal_name: str | None = None) -> None:
        """
        연결된 모든 시그널(또는 특정 이름의 시그널)의 연결을 해제한다.
        리소스 정리나, 화면이 닫힐 때 사용한다.
        """
        # ✅ 중요: 이 객체(self)가 아니라, 멤버로 가진 그룹 객체(self.system 등)를 뒤져야 한다.
        for group in self._signal_groups:
            meta = group.metaObject()
            if meta is None:
                continue

            # 해당 그룹이 가진 모든 메서드를 검사
            for i in range(meta.methodCount()):
                m = meta.method(i)
                # 메서드 타입이 'Signal'인 것만 찾음
                if m.methodType() != QMetaMethod.MethodType.Signal:
                    continue

                # 시그널 이름을 가져옴 (예: 'message', 'error')
                sig_name = m.name().data().decode("utf-8")

                # 사용자가 특정 이름을 요청했으면 그것만, 아니면 전부 다
                if signal_name is None or sig_name == signal_name:
                    sig = getattr(group, sig_name, None)
                    if sig is not None:
                        try:
                            # 실제 연결 끊기 시도
                            sig.disconnect()
                        except (TypeError, RuntimeError):
                            # 연결된 게 없는데 끊으려 하면 에러가 날 수 있음. 안전하게 무시.
                            pass


# =============================================================================
# 3. 껍데기 (Proxy Class)
# =============================================================================
class EventBus:
    """
    [외부 공개용 클래스]

    이 클래스는 QObject를 상속받지 않았다!
    그래서 언제 어디서 import 해도 안전하다. (충돌 없음)

    실제 기능은 '_qobject' 속성에 접근하는 순간 생성된 백엔드 객체가 대신 처리한다.
    """

    def __init__(self):
        # 내부적으로 진짜 QObject를 담을 변수 (처음엔 비어있음)
        self._backend: Optional[_EventBusBackend] = None

    @property
    def _qobject(self) -> _EventBusBackend:
        """
        진짜 객체가 필요할 때, 그때서야 생성하는 '게으른(Lazy)' 속성이다.
        """
        if self._backend is None:
            # 이 코드가 실행될 때는 이미 앱(QApplication)이 켜진 후일 것이다.
            self._backend = _EventBusBackend()
        return self._backend

    def __getattr__(self, name: str):
        """
        사용자가 bus.log.message 처럼 접근하면,
        자동으로 백엔드 객체(_qobject)에게 그 요청을 토스한다.
        마치 투명인간처럼 행동한다.
        """
        return getattr(self._qobject, name)

    def disconnect_all(self, signal_name: str | None = None):
        """백엔드에게 연결 해제 명령을 전달한다."""
        self._qobject.disconnect_all(signal_name)


# =============================================================================
# 전역 인스턴스
# =============================================================================
if TYPE_CHECKING:
    # IDE(VSCode 등)에게는 "이거 사실 _EventBusBackend 야"라고 알려줘서 자동완성을 돕는다.
    EVENT_BUS = _EventBusBackend()
else:
    # 실행 시에는 안전한 껍데기(EventBus)를 내보낸다.
    EVENT_BUS = EventBus()
