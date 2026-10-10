# AI Handoff / Audit Guide

## 1. تعريف المشروع

**Instagram Sync** هو Desktop Application شخصي مكتوب بـPython + PySide6.
وظيفته تنزيل Media من Instagram ثم مزامنة الجديد فقط في التشغيلات التالية.

المشروع ليس SaaS، ولا يحتوي Licensing أو Payments أو Telemetry.

## 2. الحالة الحالية

الإصدار المستهدف: **1.0.0**

المزايا الأساسية:

- Posts.
- Reels.
- Carousel.
- Incremental Sync.
- SQLite local catalog.
- Sync history.
- Browser Session import.
- No password storage.
- Windows build script.
- Unit tests.
- GitHub Actions CI.

## 3. Source of Truth

حالة تنزيل العنصر لا تعتمد على وجود اسم ملف فقط.

قاعدة SQLite هي Source of Truth وتستخدم:

```text
(profile, shortcode, item_index)
```

كـUnique Identity.

## 4. Data Flow

```text
User Input
  -> Presentation
  -> SyncRequest
  -> SyncProfileUseCase
  -> MediaSource (Instagram)
  -> MediaCatalog.contains()
  -> BinaryDownloader
  -> MediaCatalog.record_media()
  -> SyncResult
  -> Presentation
```

## 5. Login Flow

```text
User logs into Instagram in browser
  -> chooses browser in app
  -> browser_cookie3 reads local Instagram cookies
  -> Instaloader test_login()
  -> verified username returned
  -> Instaloader session saved under OS app-data
  -> future sync loads local session
```

Password is never requested by this app.

## 6. Database Schema

### media

- id
- profile
- shortcode
- item_index
- media_type
- post_date
- filename
- downloaded_at

Unique:
`profile + shortcode + item_index`

### sync_runs

- id
- profile
- started_at
- finished_at
- downloaded_count
- skipped_count
- status
- error

## 7. أهم الملفات

| File | Purpose |
|---|---|
| `domain/models.py` | Domain models |
| `application/ports.py` | Interfaces / Ports |
| `application/sync_profile.py` | Incremental sync use case |
| `application/connect_session.py` | Browser session use case |
| `infrastructure/instagram_source.py` | Instaloader adapter |
| `infrastructure/browser_session.py` | Browser cookie import |
| `infrastructure/sqlite_catalog.py` | SQLite adapter |
| `infrastructure/http_downloader.py` | File download adapter |
| `presentation/main_window.py` | PySide6 UI |
| `composition.py` | Dependency injection wiring |

## 8. قواعد التطوير

أي AI أو مطور يكمل المشروع يجب أن يلتزم بـ:

1. OOP + SOLID.
2. عدم وضع Business Logic في UI.
3. Dependencies الخارجية تبقى داخل Infrastructure.
4. أي Class/Function جديدة يكون لها تعليق/Docstring عربي يشرح الهدف.
5. لا تحفظ Password أو Cookies في Git أو Logs.
6. لا تكسر Unique Identity للمزامنة بدون Migration مدروسة.
7. أضف Tests لأي تغيير في منطق Sync.
8. شغل CI قبل اعتبار التغيير مكتملًا.

## 9. Audit سريع

ابدأ بهذا الترتيب:

1. `README.md`
2. `docs/ARCHITECTURE.md`
3. `docs/SECURITY.md`
4. `application/ports.py`
5. `application/sync_profile.py`
6. `infrastructure/*`
7. `presentation/main_window.py`
8. `tests/*`

ثم شغل:

```powershell
pip install -e .[dev]
ruff check src tests
pytest -q
```

## 10. Known Constraints

- Instagram قد يغير Endpoints أو Rate Limits.
- Session من المتصفح تعتمد على صلاحيات نظام التشغيل والمتصفح.
- إجمالي عدد Media غير معروف قبل القراءة، لذلك UI يستخدم Busy Progress أثناء Sync.
- لا يوجد Auto Scheduler؛ المزامنة Manual فقط.
- لا يوجد Cloud backup.

## 11. Definition of Done

التغيير يعتبر مكتملًا فقط إذا:

- الكود في الطبقة الصحيحة.
- لا توجد أسرار في Git.
- Ruff ينجح.
- Pytest ينجح.
- CI أخضر.
- Documentation تحدثت لو تغير Architecture أو Data Flow.
