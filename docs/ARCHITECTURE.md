# Architecture

## الهدف

المشروع يستخدم Clean / Hexagonal Architecture بشكل مبسط.

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

التطبيق لا يقرأ Browser Cookies الخارجية.

## المزامنة

```text
UI
 -> SyncProfileUseCase
 -> InstaloaderMediaSource (optional saved session)
 -> SQLiteMediaCatalog
 -> BinaryDownloader
```

لو لا توجد Session يعمل على المحتوى العام المتاح.
لو توجد Session يمكنه قراءة المحتوى الخاص الذي يسمح به الحساب المتصل.

## Watch List

Watch List هي الحسابات التي يضيفها المستخدم صراحةً فقط.

عند فتح البرنامج:

```text
QTimer.singleShot
 -> SyncWatchListUseCase
 -> SyncProfileUseCase لكل حساب
 -> تنزيل الجديد فقط
 -> ينتهي الـWorker
```
