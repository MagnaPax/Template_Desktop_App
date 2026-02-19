# logging/log_listener.py
"""
[로그 리스너 (Log Listener)]

EventBus에서 날아오는 '로그 이벤트(log.message)'를 잡아서,
실제 '로거(Logger)'에게 전달하는 중재자(Mediator) 역할이다.

장점:
    1. Logger는 EventBus나 Qt를 몰라도 된다. (순수 파이썬 로거 유지)
    2. EventBus는 로깅이 어떻게 되는지 몰라도 된다. (그저 신호만 보낼 뿐)
    3. 이 녀석이 중간에서 둘을 이어준다. -> 결합도 감소!
"""
from __future__ import annotations

from typing import Any

# TODO: 실제 프로젝트의 logger 모듈 위치로 수정이 필요할 수 있다.
# 지금은 표준 logging 모듈을 가져와서 사용한다.


class LogListener:
    def __init__(self, bus: Any):
        """
        리스너를 생성하면서 EventBus에 귀를 기울인다(connect).

        Args:
            bus (Any): EventBus 객체 (QtBus든 SimpleBus든 상관없음)
        """
        # [중요] 여기서 'LogListener'라는 이름의 로거를 달라고 요청한다.
        # utilities.logger.get_logger를 사용해야 우리가 설정한(Logger.initialize) 로거의 설정을 물려받을 수 있다.
        # 그냥 logging.getLogger("Name")을 쓰면 설정되지 않은 '쌩' 로거를 받게 되어 로그가 증발한다.
        from utilities.logger import get_logger

        self.logger = get_logger("LogListener")
        self._bus = bus

        # 핵심!
        # 버스의 log.message 채널에 내 귀(on_log_message)를 연결한다.
        # 이제 누가 버스에 대고 "로그 남겨줘!"라고 외치면 on_log_message가 실행된다.
        self._bus.log.message.connect(self.on_log_message)

        self.logger.info("LogListener initialized (로그 리스너가 시작되었다)")

    def on_log_message(self, source: str, message: str, level: str):
        """
        실제 로그 이벤트가 발생했을 때 호출되는 함수(Slot)이다.

        Args:
            source (str): 로그를 보낸 녀석 (예: "MainView", "ScannerSvc")
            message (str): 로그 내용
            level (str): 중요도 ("DEBUG", "INFO", "ERROR" 등)
        """
        level_upper = level.upper()

        # 보기 좋게 포맷팅: "[보낸곳] 내용"
        formatted_message = f"[{source}] {message}"

        # 레벨에 맞춰서 실제 로거에게 기록을 명령한다.
        if level_upper == "DEBUG":
            self.logger.debug(formatted_message)
        elif level_upper == "INFO":
            self.logger.info(formatted_message)
        elif level_upper == "WARNING":
            self.logger.warning(formatted_message)
        elif level_upper == "ERROR":
            self.logger.error(formatted_message)
        elif level_upper == "CRITICAL":
            self.logger.critical(formatted_message)
        else:
            # 듣도 보도 못한 레벨이 오면 그냥 INFO로 처리하면서 레벨 이름을 앞에 붙여준다.
            self.logger.info(f"[{level}] {formatted_message}")
