# core/di_container.py
"""
[의존성 주입(Dependency Injection) 컨테이너 안내서]

Q1. 이 파일은 왜 존재하는가?
앱이 커지면 ViewModel들은 여러 Manager(상태 저장소)와 Service(비즈니스 로직)를 필요로 한다.
만약 서로 다른 ViewModel들이 각자 독립적으로 Manager를 생성해버린다면, 화면마다 상태(진행률, 데이터 등)가 엇갈리는 최악의 상황이 발생한다.
이 파일(AppContainer)은 이런 파편화를 막기 위해, 시스템 전체에서 쓰일 '공통 부품들(Manager, ViewModel)'을 처음 시작할 때 딱 한 곳에서 조립해 주고, 똑같이 복제된 매니저를 필요한 곳에 정확히 나눠주는(주입하는) '부품 공장 도면' 역할을 한다.

Q2. 이것을 어떻게 활용하는가?
1. 새로 만든 공통 Manager가 있다면, 이 파일의 Manager 구역에 `providers.Singleton`으로 등록한다. (단 하나만 존재해야 하기 때문)
2. 새로운 ViewModel을 만들었다면 ViewModel 구역에 `providers.Factory`로 등록한다. (화면이 열릴 때마다 새로 찍어내야 하기 때문)
3. 등록할 때 ViewModel이 필요로 하는 Manager의 이름을 조립 라인(Factory 괄호 안)에 연결해 주기만 하면 끝이다.

이후부터는 `main.py`나 뷰모델 내부에서 Manager를 생성할 필요 없이 컨테이너가 알아서 끼워 넣어준다.

(참고: 프로그램 덩치가 거대해지면, 이 단일 공장(단일컨테이너)을 여러 개의 전문 공장(다중컨테이너)으로 쪼갤 수도 있다:
https://python-dependency-injector.ets-labs.org/examples/application-multiple-containers.html)
"""
from dependency_injector import containers, providers

from managers.base_manager import BaseManager
from view_models.main_window_vm import MainViewModel


class AppContainer(containers.DeclarativeContainer):
    """
    ViewModel과 그들이 의존하는 Manager(공통 상태/서비스)가 어떻게 결합되어야 하는지 명세해 놓은 '최상위 부품 공장'
    """
    
    # ==========================================================
    # 1. Managers (주로 싱글톤으로 유지됨)
    # ==========================================================
    # providers.Singleton: 요청할 때마다 새로 만들지 않고, 
    # 최초 1회 생성된 객체 공유 (공통 상태 유지에 필수)
    system_manager = providers.Singleton(BaseManager)
    
    # 향후 추가될 예시:
    # db_manager = providers.Singleton(DatabaseManager)
    # progress_manager = providers.Singleton(ProgressManager)

    # ==========================================================
    # 2. ViewModels (화면마다 새로 띄워야 하므로 Factory 패턴)
    # ==========================================================
    # providers.Factory: 요청할 때마다 새로운 인스턴스를 찍어냄.
    # 이때 괄호 안의 keyword argument(system_manager 등)가 해당 클래스의 __init__에 자동 주입됨.
    main_view_model = providers.Factory(
        MainViewModel,
        system_manager=system_manager  # MainViewModel의 __init__(self, system_manager) 에 매핑됨
    )
