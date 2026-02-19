# main.py
"""
[메인 엔트리 포인트]

애플리케이션의 시작점이다.
AppEngine을 생성하고 시작(Bootstrap 및 Exec)하는 역할만 담당한다.
"""
import sys

from app.app_engine import AppEngine
from ui.main_window import MainWindow
from view_models.main_window_vm import MainViewModel


def main():
    """
    앱의 진입 함수이다.
    """
    # 1. 앱 엔진 생성 (심장 이식)
    engine = AppEngine()

    # 2. 엔진 시동 및 주행 시작 (블로킹)
    #    start() 내부에서 bootstrap 수행 후 exec()로 이벤트 루프에 진입한다. -> 수정: start()에서 부트스트랩만 하고 exec는 별도로 함.
    #    계획 변경: AppEngine.start()는 초기화만 하고, 리턴값 없이 끝난다.
    #    실제 루프 진입은 engine.exec()로 하는 것이 더 명시적이다.

    engine.start()  # 초기화 (EventBus, LogListener 등)

    # ViewModel & Window 생성
    main_vm = MainViewModel()
    main_window = MainWindow(main_vm)
    main_window.show()

    # 3. 실제 이벤트 루프 진입
    sys.exit(engine.exec())


if __name__ == "__main__":
    main()
