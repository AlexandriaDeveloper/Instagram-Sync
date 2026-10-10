# Architecture

## الهدف

المشروع يستخدم **Clean / Hexagonal Architecture** بشكل مبسط حتى يظل مفهومًا وقابلًا للتعديل.

## قاعدة الاعتماد

الاتجاه الأساسي:

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

- `domain` لا يعتمد على أي Framework.
- `application` يعتمد على Domain وعلى Interfaces صغيرة اسمها Ports.
- `infrastructure` ينفذ Ports باستخدام Instaloader وSQLite وurllib وbrowser_cookie3.
- `presentation` هي PySide6 فقط.
- `composition.py` هو المكان الذي يجمع الأجزاء عبر Dependency Injection.

## المجلدات

### domain

قواعد ونماذج البيانات فقط:

- `MediaIdentity`
- `RemoteMedia`
- `SyncRequest`
- `SyncResult`
- `SessionInfo`

### application

حالات الاستخدام والعقود:

- `SyncProfileUseCase`
- `ConnectBrowserSessionUseCase`
- `MediaSource`
- `MediaCatalog`
- `BinaryDownloader`
- `BrowserSessionImporter`

### infrastructure

التفاصيل التقنية القابلة للاستبدال:

- `InstaloaderMediaSource`
- `SQLiteMediaCatalog`
- `UrlLibBinaryDownloader`
- `InstaloaderBrowserSessionImporter`

### presentation

- `MainWindow`
- `SyncWorker`
- `SessionWorker`

لا يوجد SQL أو parsing لـInstagram داخل UI.

## SOLID

### S — Single Responsibility

كل Class له مسؤولية رئيسية واحدة:
قراءة Instagram، حفظ Metadata، تنزيل Binary، تنسيق Sync، أو عرض UI.

### O — Open/Closed

يمكن إضافة Adapter جديد دون تعديل `SyncProfileUseCase`.
مثال: تغيير Downloader أو Database.

### L — Liskov Substitution

أي Implementation يحقق Port يمكن حقنه مكان Implementation آخر.

### I — Interface Segregation

بدل Interface ضخم، توجد Interfaces صغيرة:
`MediaSource`, `MediaCatalog`, `BinaryDownloader`, `BrowserSessionImporter`.

### D — Dependency Inversion

Application Layer لا يعتمد على Instaloader أو SQLite مباشرة.

## تدفق المزامنة

```text
UI
 -> SyncRequest
 -> SyncProfileUseCase
 -> MediaSource
 -> لكل عنصر:
      MediaCatalog.contains?
        yes -> skip
        no  -> BinaryDownloader.download
             -> MediaCatalog.record_media
 -> finish_run
 -> UI result
```

## لماذا المفتاح shortcode + item_index؟

- `shortcode` يعرف الـPost/Reel.
- Carousel يحتوي أكثر من عنصر داخل نفس shortcode.
- لذلك `item_index` يميز كل صورة/فيديو داخل Carousel.

## مكان التعديل حسب المطلوب

- تغيير قواعد Sync: `application/sync_profile.py`
- تغيير Instagram provider: `infrastructure/instagram_source.py`
- تغيير DB: Adapter جديد داخل `infrastructure`
- تغيير UI: `presentation/main_window.py`
- تغيير Dependency wiring: `composition.py`
