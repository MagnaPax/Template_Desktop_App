# app/app_engine.py
"""
[앱 엔진 (App Engine)]

애플리케이션의 '심장'이자 '시동 키' 역할을 하는 클래스이다.
프로그램이 시작될 때 가장 먼저 실행되어, 필요한 부품들을 올바른 순서대로 조립한다.

가장 중요한 역할:
    "생성 순서 보장"
    1. Qt 앱(QApplication) 먼저 만들기
    2. 그 다음 EventBus 만들기 (그래야 안전함)
    3. 마지막으로 LogListener 붙이기 (그래야 로그를 놓치지 않음)
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

from app.bootstrap import build_event_bus, is_qt_mode
from core.log_listener import LogListener


@dataclass
class AppContext:
    """
    앱 전체에서 공유해야 할 중요 객체들을 담아두는 보관함이다.
    """

    event_bus: object  # 이벤트 버스 (소통 창구)
    log_listener: Optional[LogListener] = None  # 로그 리스너 (기록 담당)


class AppEngine:
    def __init__(self):
        self.logger = logging.getLogger("AppEngine")
        self.ctx: Optional[AppContext] = None  # 보관함은 start() 후에 채워진다.
        self._qt_app = None  # Qt 애플리케이션 객체

    def start(self):
        """
        엔진 시동을 건다. 초기화 작업을 수행한다.
        """
        # 0) 로깅 설정 초기화 (유틸리티 로거 사용)
        # 중요: 앱이 시작될 때 가장 먼저 "로그 기록계"를 켜는 단계이다.
        # 여기서 '어디에 저장할지', '어느 정도 자세히 기록할지'를 결정해서 알려준다.
        import logging  # 로그 레벨 상수(DEBUG, INFO)를 쓰기 위해 가져옴

        from config.app_config import APP_CONFIG
        from utilities.logger import Logger

        # "Logger야, 우리 앱 이름은 이거고, 로그는 저기 저장해줘. 그리고 디버그 모드면 자세히 적어줘."
        Logger.initialize(
            app_name=APP_CONFIG.app_name,  # 앱 이름 (로그 파일 내부 기록용)
            log_dir=APP_CONFIG.paths.LOG_DIR,  # 로그 파일 저장 위치
            level=logging.DEBUG if APP_CONFIG.debug else logging.INFO,  # 기록 레벨 설정
            console=True,  # 개발 중에는 콘솔(검은 화면)에도 글씨가 나오게 함
        )

        # 1) Qt 모드라면, QApplication을 가장 먼저 만들어야 한다.
        #    이게 없으면 Qt 관련 기능(QObject 등)이 제대로 동작하지 않을 수 있다.
        if is_qt_mode():
            import sys

            from PySide6.QtWidgets import QApplication

            # 혹시 다른 곳에서 이미 만들었나 확인해보고, 없으면 새로 만든다.
            app = QApplication.instance()
            if not app:
                self._qt_app = QApplication(sys.argv)
            else:
                self._qt_app = app

        # 2) EventBus 생성
        #    Qt 앱이 준비된 후에 만들어야 안전하다. (bootstrap이 알아서 적절한 버스를 준다)
        bus = build_event_bus()

        # 3. LogListener 생성 및 연결
        listener = LogListener(bus)

        # 4. AppContext 생성
        self.ctx = AppContext(event_bus=bus, log_listener=listener)

        # 2-1) 스타일시트 적용
        if self._qt_app:
            from config.app_config import APP_CONFIG
            from styles.style_manager import apply_stylesheet

            try:
                apply_stylesheet(self._qt_app, APP_CONFIG.paths.STYLESHEET_PATH)
                self.logger.info(
                    f"스타일시트 적용 완료: {APP_CONFIG.paths.STYLESHEET_PATH}"
                )
            except Exception as e:
                self.logger.error(f"스타일시트 적용 실패: {e}")

    def exec(self):
        """
        앱을 본격적으로 실행한다. (이벤트 루프 진입)
        창을 끄기 전까지는 이 함수에서 멈춰있게 된다.
        """
        if self._qt_app:
            return self._qt_app.exec()
        return 0
