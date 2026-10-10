# Architecture

## الهدف

المشروع يستخدم Clean / Hexagonal Architecture بشكل مبسط، مع فصل واضح بين واجهة المستخدم ومنطق التطبيق والتقنيات الخارجية.

## قاعدة الاعتماد

```text
presentation
    |
composition
    |
application  ---> domain
    ^
    |
infrastructure
```

قاعدة مهمة: طبقة `application` لا تعتمد مباشرة على PySide6 أو SQLite أو Instaloader أو نظام الملفات.

## تقسيم Presentation

```text
presentation/
├── main_window.py
├── login_dialog.py
└── workers.py
```

- `main_window.py`: تجميع المدخلات وعرض الحالة والنتائج فقط.
- `login_dialog.py`: نافذة تسجيل Instagram المعزولة.
- `workers.py`: تشغيل عمليات المزامنة خارج UI Thread وإرجاع النتائج عبر Signals.

## Session Management

```text
MainWindow
 -> ManageSessionUseCase
 -> SessionStore Port
 -> LocalSessionStore
 -> local session file
```

الواجهة لا تتعامل مع `session_path` أو حذف الملفات مباشرة.

## تسجيل الدخول

```text
InstagramLoginDialog (QWebEngine)
  -> Cookie Store الخاص بالتطبيق
  -> ConnectSessionUseCase
  -> SessionWriter Port
  -> InstaloaderSessionWriter
  -> test_login()
  -> local .session file
```

التطبيق لا يقرأ Browser Cookies الخارجية ولا يخزن Password.

## المزامنة

```text
UI
 -> SyncWorker
 -> SyncProfileUseCase
 -> MediaSource / MediaCatalog / BinaryDownloader Ports
 -> InstaloaderMediaSource
 -> SQLiteMediaCatalog
 -> UrlLibBinaryDownloader
```

لو لا توجد Session يعمل على المحتوى العام المتاح.
لو توجد Session يمكنه قراءة المحتوى الخاص الذي يسمح به الحساب المتصل.

## Watch List

Watch List هي الحسابات التي يضيفها المستخدم صراحةً فقط.

عند فتح البرنامج:

```text
QTimer.singleShot
 -> WatchSyncWorker
 -> SyncWatchListUseCase
 -> SyncProfileUseCase لكل حساب
 -> تنزيل الجديد فقط
 -> ينتهي الـWorker
```

لا يوجد Polling دوري.

## SOLID

- **SRP**: التسجيل، المزامنة، التخزين، التنزيل، Watch List، والواجهة مقسمة لمسؤوليات مستقلة.
- **OCP**: يمكن استبدال Adapters خلف Ports بدون تعديل Use Cases الأساسية.
- **LSP**: أي تنفيذ يحقق Protocol المطلوب يمكن استخدامه مكان التنفيذ الحالي.
- **ISP**: Ports صغيرة منفصلة مثل `MediaSource` و`SessionStore` و`BinaryDownloader`.
- **DIP**: Application تعتمد على Protocols، بينما Composition Root يربطها بالتنفيذات الحقيقية.

## نقطة التجميع

`composition.py` هو Composition Root الوحيد المسؤول عن إنشاء الـUse Cases وربطها بالـAdapters الحقيقية.
