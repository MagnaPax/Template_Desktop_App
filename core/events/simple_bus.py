# core/events/simple_bus.py
"""
[Non-Qt 환경용 EventBus 구현체]

Qt 라이브러리(PySide6)가 없는 환경(예: 서버, 단위 테스트, 콘솔 앱)에서도
비즈니스 로직을 동일하게 돌리기 위해 만든 '가짜(Mock)' 이벤트 버스이다.

Qt의 Signal/Slot과 똑같은 사용법(connect, emit)을 가지지만,
내부적으로는 단순한 리스트(List)와 루프(Loop)로 동작한다.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, List

# Handler: 이벤트를 받을 함수나 메서드의 타입 (어떤 인자든 받고, 뭐든 리턴함)
Handler = Callable[..., Any]


class SimpleSignal:
    """
    Qt의 Signal을 흉내 낸 클래스이다.
    함수들을 리스트에 저장해뒀다가, emit()이 호출되면 순서대로 실행해준다.
    """

    def __init__(self):
        self._handlers: List[Handler] = []

    def connect(self, handler: Handler) -> None:
        """
        [구독하기]
        이벤트가 발생하면 실행될 함수(handler)를 등록한다.
        이미 등록된 함수는 중복해서 등록하지 않는다.
        """
        if handler not in self._handlers:
            self._handlers.append(handler)

    def disconnect(self, handler: Handler | None = None) -> None:
        """
        [구독 취소]
        더 이상 이벤트를 받지 않도록 함수를 목록에서 제거한다.
        handler가 None이면 모든 구독자를 다 지워버린다.
        """
        if handler is None:
            self._handlers.clear()
            return
        if handler in self._handlers:
            self._handlers.remove(handler)

    def emit(self, *args: Any, **kwargs: Any) -> None:
        """
        [방송하기]
        등록된 모든 함수들에게 신호를 보낸다.
        인자(*args, **kwargs)는 그대로 전달된다.
        """
        # 실행 중에 누가 구독을 취소해서 리스트 크기가 변할 수 있으므로,
        # 안전하게 복사본(list(...))을 만들어서 순회한다.
        for h in list(self._handlers):
            h(*args, **kwargs)


# =============================================================================
# 시그널 그룹 정의 (QtBus와 구조를 맞춤)
# =============================================================================
@dataclass
class _Log:
    message: SimpleSignal = SimpleSignal()


@dataclass
class _Data:
    sequence_activity_changed: SimpleSignal = SimpleSignal()
    sequence_data_loaded: SimpleSignal = SimpleSignal()


@dataclass
class _System:
    system_error_occurred: SimpleSignal = SimpleSignal()
    system_notification_received: SimpleSignal = SimpleSignal()


# =============================================================================
# 메인 클래스
# =============================================================================
class SimpleEventBus:
    """
    Qt가 없을 때 대신 사용하는 이벤트 버스이다.
    사용법은 QtEventBus와 99% 동일하게 만들어서,
    코드를 고치지 않고도 환경을 오갈 수 있게 한다.
    """

    def __init__(self):
        # 각 그룹별로 SimpleSignal들을 생성하여 배치한다.
        self.system = _System()
        self.log = _Log()
        self.data = _Data()

        # 전체 관리를 위한 리스트
        self._signal_groups = [self.system, self.log, self.data]

    def disconnect_all(self, signal_name: str | None = None) -> None:
        """
        모든 연결을 끊어버린다. (초기화나 종료 시 유용)
        """
        # 모든 그룹을 돈다.
        for group in self._signal_groups:
            # 그룹 내의 모든 속성(변수)을 확인한다.
            for attr in dir(group):
                sig = getattr(group, attr, None)

                # 속성이 SimpleSignal 타입인 경우에만 처리한다.
                if isinstance(sig, SimpleSignal):
                    # 특정 이름만 원했으면 이름 체크, 아니면 통과
                    if signal_name is None or attr == signal_name:
                        sig.disconnect()  # 싹둑
