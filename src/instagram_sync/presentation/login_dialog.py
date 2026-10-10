"""نافذة تسجيل الدخول المعزولة عن النافذة الرئيسية."""

from __future__ import annotations

from PySide6.QtCore import QUrl
from PySide6.QtWebEngineCore import QWebEnginePage, QWebEngineProfile
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class InstagramLoginDialog(QDialog):
    """متصفح خاص بالتطبيق لتسجيل الدخول مباشرة في Instagram.

    التطبيق لا يقرأ Password ولا Cookies من متصفح المستخدم الأساسي.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        """إنشاء Browser Profile مؤقت وتجميع Cookies الخاصة بـInstagram فقط."""
        super().__init__(parent)
        self.setWindowTitle("Login to Instagram")
        self.resize(980, 760)

        self._cookies: dict[str, str] = {}

        # Profile بدون اسم يكون Off-the-Record ولا يحفظ Cookies المتصفح بشكل دائم.
        self._web_profile = QWebEngineProfile(self)
        self._web_page = QWebEnginePage(self._web_profile, self)
        self._web_view = QWebEngineView(self)
        self._web_view.setPage(self._web_page)

        cookie_store = self._web_profile.cookieStore()
        cookie_store.cookieAdded.connect(self._on_cookie_added)

        self._status = QLabel(
            "Sign in to Instagram here. When login is complete, "
            "the button below will activate."
        )

        email_link_help = QLabel(
            "If Instagram sends a login link by email, copy the link address "
            "and paste it here so it opens inside this app."
        )
        self._email_link = QLineEdit()
        self._email_link.setPlaceholderText(
            "Paste the Instagram login link from your email"
        )
        self._email_link.returnPressed.connect(self._open_email_login_link)

        open_email_link_button = QPushButton("Open Email Login Link")
        open_email_link_button.clicked.connect(self._open_email_login_link)

        email_link_row = QHBoxLayout()
        email_link_row.addWidget(self._email_link, 1)
        email_link_row.addWidget(open_email_link_button)

        self._accept_button = QPushButton("Use This Instagram Session")
        self._accept_button.setEnabled(False)
        self._accept_button.clicked.connect(self.accept)

        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)

        buttons = QHBoxLayout()
        buttons.addStretch()
        buttons.addWidget(self._accept_button)
        buttons.addWidget(cancel_button)

        layout = QVBoxLayout(self)
        layout.addWidget(self._status)
        layout.addWidget(email_link_help)
        layout.addLayout(email_link_row)
        layout.addWidget(self._web_view, 1)
        layout.addLayout(buttons)

        self._web_view.setUrl(QUrl("https://www.instagram.com/accounts/login/"))

    def _open_email_login_link(self) -> None:
        """فتح رابط Instagram المنسوخ من البريد داخل Browser Profile نفسه."""
        url = QUrl(self._email_link.text().strip())
        host = url.host().lower().rstrip(".")

        is_instagram_host = (
            host == "instagram.com" or host.endswith(".instagram.com")
        )
        if (
            not url.isValid()
            or url.scheme().lower() != "https"
            or not is_instagram_host
        ):
            QMessageBox.warning(
                self,
                "Invalid Instagram link",
                "Paste a secure https:// link that belongs to instagram.com.",
            )
            return

        self._status.setText(
            "Opening the email login link inside the app. "
            "Complete any Instagram verification shown below."
        )
        self._web_view.setUrl(url)

    def _on_cookie_added(self, cookie) -> None:
        """حفظ Cookies التابعة لـInstagram داخل الذاكرة فقط."""
        domain = cookie.domain().lower()
        if "instagram.com" not in domain:
            return

        name = bytes(cookie.name()).decode("utf-8", errors="ignore")
        value = bytes(cookie.value()).decode("utf-8", errors="ignore")
        self._cookies[name] = value

        # sessionid يظهر بعد نجاح تسجيل الدخول الفعلي بما فيه 2FA إن وجد.
        if name == "sessionid" and value:
            self._accept_button.setEnabled(True)
            self._status.setText(
                "Instagram login detected. You can now use this session."
            )

    def instagram_cookies(self) -> dict[str, str]:
        """إرجاع نسخة من Cookies المجمعة للـUse Case بعد قبول المستخدم."""
        return dict(self._cookies)
