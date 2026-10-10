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

## Login Flow

```text
User clicks Login to Instagram
 -> dedicated QWebEngine dialog
 -> user authenticates directly with Instagram
 -> app-owned cookie store collects Instagram cookies
 -> ConnectSessionUseCase
 -> InstaloaderSessionWriter.test_login()
 -> username verified
 -> session saved under OS app-data
```

Password لا يمر داخل Business Logic ولا يحفظ.

## قواعد مهمة

1. OOP + SOLID.
2. لا Business Logic داخل UI.
3. التعليقات بالعربي.
4. لا تستخدم browser-cookie3 أو تقرأ Cookies متصفح المستخدم الأساسي.
5. لا تسجل Session/Cookies في Logs أو Git.
6. Private profiles تعمل فقط ضمن صلاحيات الحساب المتصل.
7. لا تجعل Watch List مساوية لقائمة Following.
8. لا تضف Polling دوري إلا بطلب صريح.
9. Ruff + Pytest + CI لازم يكونوا ناجحين قبل Definition of Done.
