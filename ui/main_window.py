from typing import Generic, TypeVar


from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QLabel, QMenuBar
from PySide6.QtGui import QIcon, QAction, QKeySequence

from config.app_config import APP_CONFIG
from core.events.qt_bus import EVENT_BUS

# 제네릭 타입 정의
T = TypeVar("T")

class MainWindow(QMainWindow, Generic[T]):
    """
    메인 윈도우 UI 클래스
    
    특징:
    - QMainWindow 상속
    - ViewModel과 바인딩
    - 메뉴바 및 상태바 포함
    """
    def __init__(self, view_model: T):
        super().__init__()
        self.view_model = view_model
        
        # 로그 소스 이름 설정
        self.log_source = self.__class__.__name__
        
        self.init_ui()
        self.init_bindings()
        
    def init_ui(self):
        """UI 초기화"""
        self.setObjectName("main_window")
        self.setWindowTitle(APP_CONFIG.app_name)
        self.resize(1024, 768)
        
        # 아이콘 설정
        icon_path = APP_CONFIG.paths.APP_ICON
        
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))
        
        # Central Widget 설정
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 기본 레이아웃 및 위젯 (테스트용)
        layout = QVBoxLayout(central_widget)
        
        label = QLabel("Main Window Initialized")
        layout.addWidget(label)
        
        # 메뉴바 설정
        self._setup_menu_bar()
        
        # 상태바 설정
        self.statusBar().showMessage("Ready")
        
        self.log_info("메인 윈도우 UI 초기화 완료")

    def _setup_menu_bar(self):
        """메뉴바 및 액션 구성"""
        menu_bar = self.menuBar()
        menu_bar.setObjectName("menu_bar")
        
        # [File] 메뉴
        file_menu = menu_bar.addMenu("&File")
        
        # [File] 메뉴 - Exit 액션
        exit_action = QAction("&Exit", self)
        exit_action.setShortcut(QKeySequence("Ctrl+Q"))
        exit_action.setStatusTip("Exit application")
        exit_action.triggered.connect(self.close)
        
        file_menu.addAction(exit_action)
        
        # [Help] 메뉴
        help_menu = menu_bar.addMenu("&Help")
        
        # [Help] 메뉴 - About 액션
        about_action = QAction("&About", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    def init_bindings(self):
        """ViewModel 시그널 바인딩"""
        pass

    def _show_about(self):
        self.log_info("About 메뉴 클릭됨")
        # TODO: About 다이얼로그 표시

    # --- 로깅 헬퍼 메서드 ---
    def log(self, message: str, level: str = "INFO"):
        """EventBus를 통해 로그를 전송한다."""
        EVENT_BUS.log.message.emit(self.log_source, message, level)

    def log_info(self, message: str):
        self.log(message, "INFO")
        
    def log_warning(self, message: str):
        self.log(message, "WARNING")
        
    def log_error(self, message: str):
        self.log(message, "ERROR")

    def log_debug(self, message: str):
        self.log(message, "DEBUG")
