from view_models.base_view_model import BaseViewModel

class MainViewModel(BaseViewModel):
    """
    메인 윈도우의 비즈니스 로직과 상태를 관리하는 ViewModel
    """
    def __init__(self):
        super().__init__()
        self.log_info("MainViewModel 초기화됨")
