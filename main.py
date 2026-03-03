# main.py
"""
[메인 엔트리 포인트]

애플리케이션의 시작점이다.
"""
import sys
from dependency_injector.wiring import Provide, inject

from app.app_engine import AppEngine
from ui.main_window import MainWindow
from view_models.main_window_vm import MainViewModel
from core.di_container import AppContainer


@inject
def main(
    # 컨테이너에서 main_view_model 팩토리를 찾아서 자동으로 넘겨줍니다.
    main_vm: MainViewModel = Provide[AppContainer.main_view_model]
):
    """
    앱의 진입 함수이다.
    """
    # 1. 앱 엔진 생성 (심장 이식)
    engine = AppEngine()

    # 2. 엔진 시동 
    engine.start()  # 초기화 (EventBus, LogListener 등)

    # 3. Window 생성 & 주입받은 ViewModel 사용
    main_window = MainWindow(main_vm)
    main_window.show()

    # 4. 실제 이벤트 루프 진입
    sys.exit(engine.exec())


if __name__ == "__main__":
    # 프로그램이 시작될 때 단 한 번 컨테이너를 생성
    container = AppContainer()
    
    # 생성된 컨테이너와 현재 모듈(main.py)을 연결(Wiring)
    # 이 과정이 있어야 @inject 와 Provide 가 정상적으로 작동합니다.
    container.wire(modules=[__name__])
    
    main()
