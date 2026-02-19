# core/events/interfaces.py
"""
[인터페이스 (Interface) 정의]

이 파일은 '구현(Code)'이 아니라 '규칙(Rule)'을 담고 있다.
"EventBus라면 응당 이런 기능은 있어야 한다!"라는 약속이다.

프로토콜(Protocol)을 사용해서 정의했으므로,
이 규칙을 지키는 클래스는 QtBus든 SimpleBus든 상관없이
EventBusLike 타입으로 취급받을 수 있다.
"""
from __future__ import annotations

from typing import Any, Callable, Protocol

# Handler: 이벤트를 처리할 함수 (인자도 맘대로, 리턴도 맘대로)
Handler = Callable[..., Any]


class SignalLike(Protocol):
    """
    '시그널처럼 동작하는 녀석'의 규칙이다.
    Qt의 Signal 객체나 SimpleBus의 SimpleSignal 객체 모두 이 규칙을 따른다.
    """

    def connect(self, handler: Handler) -> None:
        """이벤트가 터지면 실행할 함수를 등록한다."""
        ...

    def disconnect(self, handler: Handler | None = None) -> None:
        """등록된 함수를 빼버린다."""
        ...

    def emit(self, *args: Any, **kwargs: Any) -> None:
        """이벤트를 터뜨린다(방송한다)."""
        ...


class EventBusLike(Protocol):
    """
    '이벤트 버스처럼 동작하는 녀석'의 규칙이다.
    """

    # 주의: Protocol에서는 멤버 변수(system, log 등)까지 강제하기는 조금 복잡해서,
    # 여기서는 핵심 메서드인 disconnect_all 만 명시했다.
    # 실제로 사용할 때는 bus.log.message.emit() 처럼 접근하게 된다.

    def disconnect_all(self, signal_name: str | None = None) -> None:
        """
        모든 연결을 끊는 비상 스위치 같은 기능이다.
        종료할 때나 초기화할 때 쓴다.
        """
        ...
