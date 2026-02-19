# ui/widgets/base_widget.py
"""
모든 커스텀 위젯의 베이스 클래스 (BaseView 상속)
- 데이터 업데이트(update_data) 인터페이스 제공
- 안전한 업데이트 및 로깅 통합
- 활성화/비활성화 상태 관리
"""

from typing import Any, Generic, Optional

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QWidget

from ui.base_view import BaseView, T  # T는 ViewModel 타입


class BaseWidget(BaseView[T], Generic[T]):
    """
    모든 커스텀 위젯의 베이스 클래스

    특징:
    1. BaseView 상속: ViewModel 연동 및 로깅(EventBus) 기능 내장
    2. 공통 인터페이스: update_data() 추상 메서드 제공
    3. 안전한 업데이트: 에러 발생 시 자동으로 로그 남기고 시그널 방출

    사용법:
        class MyWidget(BaseWidget[MyViewModel]):
            def init_ui(self):
                # UI 구성
                ...

            def update_data(self, data):
                # 데이터 반영
                ...
    """

    # 시그널 정의
    error_occurred = Signal(str)  # 에러 발생: (error_message)
    data_updated = Signal(object)  # 데이터 업데이트 완료: (data)

    def __init__(
        self, view_model: Optional[T] = None, parent: Optional[QWidget] = None
    ):
        """
        BaseWidget 초기화

        Args:
            view_model: 연결할 ViewModel (없으면 None)
            parent: 부모 위젯
        """
        # 부모 클래스(BaseView) 초기화 -> 내부에서 init_ui(), init_bindings() 호출됨
        super().__init__(view_model)

        if parent:
            self.setParent(parent)

        # 내부 상태
        self._is_enabled = True  # 위젯 활성화 상태
        self._last_data = None  # 마지막 업데이트 데이터

    def init_ui(self):
        """
        BaseView의 추상 메서드 구현 (기본값)
        서브클래스에서 구체적인 UI를 구성하려면 이 메서드를 오버라이드해야 함.
        """
        pass

    def update_data(self, data: Any) -> None:
        """
        데이터 업데이트 (서브클래스에서 구현 권장)

        Args:
            data: 업데이트할 데이터
        """
        raise NotImplementedError(
            f"{self.__class__.__name__}에서 update_data()를 구현해야 합니다"
        )

    def safe_update_data(self, data: Any) -> bool:
        """
        안전한 데이터 업데이트 (에러 처리 및 로깅 포함)
        """
        # 비활성화 상태면 업데이트 안함
        if not self._is_enabled:
            return False

        try:
            # 서브클래스의 update_data() 호출
            self.update_data(data)

            # 성공 시 저장 및 시그널 방출
            self._last_data = data
            self.data_updated.emit(data)
            return True

        except Exception as e:
            # 에러 발생 시 처리
            error_msg = f"{self.__class__.__name__} 업데이트 실패: {str(e)}"

            # 1. 시그널 방출 (상위 위젯 알림용)
            self.error_occurred.emit(error_msg)

            # 2. 통합 로깅 시스템 사용 (BaseView 기능)
            self.log_error(error_msg)

            return False

    def get_last_data(self) -> Optional[Any]:
        """마지막으로 업데이트된 데이터 반환"""
        return self._last_data

    def set_enabled(self, enabled: bool):
        """위젯 활성화/비활성화"""
        self._is_enabled = enabled
        self.setEnabled(enabled)

    def is_widget_enabled(self) -> bool:
        """활성화 상태 확인"""
        return self._is_enabled

    def clear_widget(self):
        """위젯 초기화 (필요시 오버라이드)"""
        self._last_data = None


# ============================================
# 테스트 코드
# ============================================
if __name__ == "__main__":
    import sys

    from PySide6.QtWidgets import QApplication, QLabel, QVBoxLayout

    # 1. 더미 ViewModel (BaseView 상속을 위해 필요)
    class DummyViewModel:
        pass

    # 2. 테스트용 위젯
    class TestWidget(BaseWidget[DummyViewModel]):
        def init_ui(self):
            layout = QVBoxLayout()
            self.label = QLabel("대기 중...")
            self.label.setStyleSheet("font-size: 20px; padding: 20px;")
            layout.addWidget(self.label)
            self.setLayout(layout)

        def update_data(self, data: Any):
            self.label.setText(f"받은 데이터: {data}")
            # 일부러 에러 내보기 테스트
            if data == "ERROR":
                raise ValueError("강제 에러 발생!")

    # 3. 앱 실행
    app = QApplication(sys.argv)

    # ViewModel 없이 생성 테스트 (Optional 지원 확인)
    widget = TestWidget(view_model=None)

    widget.setWindowTitle("BaseWidget (PySide6) 테스트")
    widget.resize(400, 200)
    widget.show()

    # 4. 테스트 로직
    print("--- 테스트 시작 ---")

    # 정상 케이스
    widget.safe_update_data("정상 데이터")

    # 에러 케이스 (로그가 EventBus로 가는지 확인은 못하지만, 에러 안 죽는지 확인)
    widget.safe_update_data("ERROR")

    sys.exit(app.exec())
