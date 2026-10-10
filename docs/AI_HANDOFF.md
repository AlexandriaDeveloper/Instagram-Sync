# AI Handoff / Audit Guide

## تعريف المشروع

Instagram Sync هو Desktop Application شخصي بـPython + PySide6.

## الوظائف

- Manual incremental sync.
- Posts / Reels / Carousel.
- Public profiles.
- Private profiles التي يملك الحساب المتصل صلاحية رؤيتها.
- Login داخل QWebEngine مخصص للتطبيق.
- لا توجد قراءة Cookies من المتصفحات الخارجية.
- Watch List يحددها المستخدم.
- Startup Check واحد فقط، بدون Polling دوري.

## الهيكل

```text
src/instagram_sync/
├── domain/
├── application/
├── infrastructure/
├── presentation/
│   ├── main_window.py
│   ├── login_dialog.py
│   └── workers.py
└── composition.py
```

### Presentation

- `main_window.py`: UI فقط.
- `login_dialog.py`: تسجيل الدخول داخل متصفح التطبيق.
- `workers.py`: Threads الخاصة بالمزامنة.

### Application

تحتوي Use Cases وPorts، ومنها:

- `SyncProfileUseCase`
- `SyncWatchListUseCase`
- `ConnectSessionUseCase`
- `ManageSessionUseCase`
- `ManageWatchListUseCase`

### Infrastructure

تنفيذات التقنيات الخارجية مثل:

- Instaloader
- SQLite
- HTTP downloader
- Local Session Store

## Login Flow

```text
User clicks Login to Instagram
 -> dedicated QWebEngine dialog
 -> user authenticates directly with Instagram
 -> app-owned cookie store collects Instagram cookies
 -> ConnectSessionUseCase
 -> SessionWriter Port
 -> InstaloaderSessionWriter.test_login()
 -> username verified
 -> session saved under OS app-data
```

Password لا يمر داخل Business Logic ولا يحفظ.

## Disconnect Flow

```text
MainWindow
 -> ManageSessionUseCase
 -> SessionStore Port
 -> LocalSessionStore
 -> remove local session file
```

ممنوع على UI حذف ملف Session مباشرة.

## قواعد مهمة

1. OOP + SOLID.
2. لا Business Logic داخل UI.
3. التعليقات التوضيحية داخل الكود تكون بالعربي قدر الإمكان.
4. لا تستخدم `browser-cookie3` أو تقرأ Cookies متصفح المستخدم الأساسي.
5. لا تسجل Session/Cookies في Logs أو Git.
6. Private profiles تعمل فقط ضمن صلاحيات الحساب المتصل.
7. لا تجعل Watch List مساوية لقائمة Following.
8. لا تضف Polling دوري إلا بطلب صريح.
9. أي تعامل جديد مع ملفات Session يمر عبر `SessionStore` وUse Case.
10. أي Adapter جديد يجب أن يحقق Port واضح بدل ربط Application بتنفيذ مباشر.
11. Ruff + Pytest + CI لازم يكونوا ناجحين قبل Definition of Done.
12. Windows build لازم ينجح بعد أي تغيير يؤثر على التشغيل أو PySide6.

## ملاحظات التدقيق

عند Audit راجع بالترتيب:

1. هل Presentation تستورد Infrastructure مباشرة؟ لو نعم فده يحتاج مراجعة.
2. هل Application تستورد PySide6 أو SQLite أو Instaloader؟ المفروض لا.
3. هل أي Password أو Cookies تُكتب في Logs أو Git؟ المفروض لا.
4. هل Watch List تعمل Check واحد عند الفتح فقط؟ نعم، ما لم يطلب المستخدم غير ذلك.
5. هل يوجد Adapter يمكن استبداله خلف Protocol بدون تعديل Use Case؟ ده مطلوب للحفاظ على DIP/OCP.
