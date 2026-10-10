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
- `infrastructure` ينفذ Ports باستخدام Instaloader وSQLite وurllib.
- `presentation` هي PySide6 فقط.
- `composition.py` يجمع الأجزاء عبر Dependency Injection.

## قرار عدم تسجيل الدخول

هذه النسخة **لا تحتوي Login أو Browser Cookie Import أو Session Storage**.

السبب:
- البرنامج للاستخدام الشخصي.
- الهدف الأساسي تنزيل ومزامنة الحسابات العامة.
- إزالة قراءة Cookies تقلل التعقيد ونطاق المخاطر الأمنية.

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
