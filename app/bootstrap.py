# app/bootstrap.py
"""
[부트스트랩 (Bootstrap)]

'부트스트랩'은 원래 '장화 끈을 스스로 당겨 일어선다'는 뜻인데,
프로그래밍에서는 '가장 기초적인 설정을 잡는 단계'를 말한다.

여기서는 "지금 우리가 Qt 환경인가? 아니면 그냥 테스트 환경인가?"를 판단하고,
그에 맞는 적절한 EventBus 부품을 꺼내주는 역할을 한다.
"""
import os


def is_qt_mode() -> bool:
    """
    현재 실행 환경이 Qt(GUI) 모드인지 확인한다.
    환경변수 'QT_MODE'가 '1'이면 GUI 모드라고 판단한다.
    (기본값은 '1' = True 이다)
    """
    return os.getenv("QT_MODE", "1") == "1"


def build_event_bus():
    """
    상황에 딱 맞는 EventBus를 공장에서 출고해준다.

    - Qt 모드면: QtEventBus (진짜 Signal/Slot 사용)
    - 아니면: SimpleEventBus (가짜 흉내내기 버전 사용)
    """
    if is_qt_mode():
        # 여기서 import를 하는 이유는?
        # 처음부터 import하면 Qt가 없는 환경에서 에러가 날 수 있기 때문이다.
        from core.events.qt_bus import EVENT_BUS

        return EVENT_BUS
    else:
        from core.events.simple_bus import SimpleEventBus

        return SimpleEventBus()
