# AI Handoff / Audit Guide

## تعريف المشروع

Instagram Sync هو Desktop Application شخصي بـPython + PySide6.

وظائفه:

- Manual Sync لحساب يكتبه المستخدم.
- Incremental Sync: تنزيل الجديد فقط بعد أول تنزيل.
- Posts / Reels / Carousel.
- Browser Session محلية بدون Password.
- Watch List محلية يختار المستخدم حساباتها بنفسه.
- Check واحد تلقائي للـWatch List عند فتح البرنامج.
- زر Check Watch List Now.
- لا يوجد Polling دوري أو Background Service.

## نقطة مهمة جدًا

Watch List **ليست** كل الحسابات التي يعمل لها المستخدم Follow على Instagram.

التطبيق لا يستدعي `get_followees()` لبناء Watch List.
فقط الحسابات التي يضيفها المستخدم صراحةً من واجهة البرنامج تدخل المزامنة التلقائية عند الفتح.

## Data Flow

```text
App opens
 -> MainWindow
 -> one-shot QTimer
 -> SyncWatchListUseCase
 -> SQLiteWatchListRepository.list_profiles()
 -> SyncProfileUseCase لكل حساب مختار
 -> SQLiteMediaCatalog يمنع التكرار
 -> Download الجديد فقط
 -> SQLiteWatchListRepository.mark_checked()
 -> Worker ينتهي
```

## قاعدة البيانات

### media

تحتوي Metadata للعناصر المنزلة، مع Unique:

```text
profile + shortcode + item_index
```

### sync_runs

Audit لكل عملية Sync.

### watch_profiles

- profile (PK)
- added_at
- last_checked_at

## أهم الملفات

- `application/sync_profile.py`: مزامنة حساب واحد.
- `application/watch_list.py`: إدارة Watch List.
- `application/sync_watch_list.py`: Check واحد للقائمة.
- `infrastructure/sqlite_watch_list.py`: تخزين القائمة.
- `presentation/main_window.py`: startup one-shot + UI.
- `docs/ARCHITECTURE.md`: شرح الطبقات.
- `docs/SECURITY.md`: قواعد الأمان.

## قواعد التطوير

1. OOP + SOLID.
2. لا Business Logic داخل UI.
3. التعليقات/Docstrings بالعربي.
4. لا Password/Cookies داخل Git أو Logs.
5. لا تجعل Watch List مساوية لـInstagram Following.
6. لا تضف Polling دوري إلا بقرار صريح من صاحب المشروع.
7. أي تعديل في Sync يحتاج Tests.
8. لا تعتبر التغيير مكتملًا إلا بعد Ruff + Pytest + CI أخضر.
