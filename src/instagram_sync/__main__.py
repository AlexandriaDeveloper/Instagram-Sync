"""نقطة تشغيل التطبيق عند استخدام: python -m instagram_sync."""

from instagram_sync.presentation.main_window import run_app


def main() -> None:
    """تشغيل واجهة البرنامج وإنهاء العملية بنفس كود خروج Qt."""
    raise SystemExit(run_app())


if __name__ == "__main__":
    main()
