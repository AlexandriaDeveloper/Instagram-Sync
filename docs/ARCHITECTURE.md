# Architecture

## الهدف

المشروع يستخدم Clean / Hexagonal Architecture بشكل مبسط حتى يظل مفهومًا وقابلًا للتعديل.

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

- `domain` لا يعتمد على Framework.
- `application` يعتمد على Domain وعلى Ports صغيرة.
- `infrastructure` ينفذ Ports باستخدام Instaloader وSQLite وurllib وbrowser_cookie3.
- `presentation` هي PySide6 فقط.
- `composition.py` يجمع الأجزاء عبر Dependency Injection.

## المزامنة اليدوية

```text
UI -> SyncProfileUseCase -> MediaSource
                       -> MediaCatalog
                       -> BinaryDownloader
```

المفتاح الفريد لكل عنصر:

```text
(profile, shortcode, item_index)
```

## Watch List

Watch List لا تُقرأ من قائمة Following في Instagram.

المستخدم هو الذي يضيف الحسابات صراحةً داخل البرنامج، وتخزن في:

```text
watch_profiles
- profile
- added_at
- last_checked_at
```

عند فتح البرنامج:

```text
QTimer.singleShot
 -> SyncWatchListUseCase
 -> list_profiles()
 -> SyncProfileUseCase لكل حساب مختار
 -> تنزيل الجديد فقط
 -> mark_checked()
 -> ينتهي الـWorker
```

لا يوجد Timer دوري ولا Polling كل 15 أو 30 دقيقة.

يوجد زر `Check Watch List Now` لعمل نفس الـCheck يدويًا عند الحاجة.

## SOLID

- SRP: كل Adapter وUse Case له مسؤولية واحدة.
- OCP: يمكن استبدال Instagram/SQLite/Downloader عبر Ports.
- LSP: أي Implementation يحقق Port يمكن حقنه مكان آخر.
- ISP: Interfaces صغيرة بدل Service ضخم.
- DIP: Application Layer تعتمد على Abstractions.
