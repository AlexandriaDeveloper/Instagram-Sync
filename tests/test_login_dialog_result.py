"""اختبار نتيجة نافذة Qt حقيقية بدون متصفح أو اتصال بإنستجرام."""

from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from PySide6.QtWidgets import QApplication, QDialog

from instagram_sync.presentation import main_window


@pytest.fixture(scope="module")
def qt_app():
    # الوضع offscreen يسمح بالتحقق من Qt في CI بدون فتح نافذة للمستخدم.
    import os

    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    app = QApplication.instance() or QApplication([])
    yield app


@pytest.mark.parametrize("accepted", [False, True])
@pytest.mark.parametrize("verification_fails", [False, True])
def test_login_handles_dialog_result_and_restores_button(
    monkeypatch, qt_app, accepted, verification_fails,
):
    cookies = Mock(return_value={"sessionid": "test-only-session"})

    class LoginDialog(QDialog):
        def __init__(self, parent):
            super().__init__()

        def exec(self):
            result = QDialog.DialogCode.Accepted if accepted else QDialog.DialogCode.Rejected
            return int(result)

        def instagram_cookies(self):
            return cookies()

    monkeypatch.setattr(main_window, "InstagramLoginDialog", LoginDialog)
    use_case = Mock()
    use_case.execute.return_value = SimpleNamespace(username="example")
    if verification_fails:
        use_case.execute.side_effect = RuntimeError("Session verification failed")
    factory = Mock(return_value=use_case)
    monkeypatch.setattr(main_window, "build_connect_session_use_case", factory)
    critical = Mock()
    monkeypatch.setattr(main_window.QMessageBox, "critical", critical)
    window = SimpleNamespace(
        _login_button=Mock(), _log=Mock(), _settings=Mock(),
        _account_label=Mock(), _disconnect_button=Mock(),
    )

    main_window.MainWindow._login_to_instagram(window)

    if not accepted:
        factory.assert_not_called()
        cookies.assert_not_called()
        window._login_button.setEnabled.assert_not_called()
        window._settings.setValue.assert_not_called()
        critical.assert_not_called()
        return

    factory.assert_called_once_with()
    use_case.execute.assert_called_once_with({"sessionid": "test-only-session"})
    assert [call.args for call in window._login_button.setEnabled.call_args_list] == [
        (False,), (True,),
    ]
    if verification_fails:
        critical.assert_called_once_with(
            window, "Instagram login failed", "Session verification failed",
        )
        window._settings.setValue.assert_not_called()
        window._disconnect_button.setEnabled.assert_not_called()
    else:
        critical.assert_not_called()
        window._settings.setValue.assert_called_once_with("username", "example")
        window._account_label.setText.assert_called_once_with("Connected as @example")
        window._disconnect_button.setEnabled.assert_called_once_with(True)
