# AI Handoff / Audit Guide

## تعريف المشروع

Instagram Sync هو Desktop Application شخصي بـPython + PySide6.

وظائفه:

- Manual Sync لحساب عام يكتبه المستخدم.
- Incremental Sync: تنزيل الجديد فقط بعد أول تنزيل.
- Posts / Reels / Carousel.
- Watch List محلية يختار المستخدم حساباتها بنفسه.
- Check واحد تلقائي للـWatch List عند فتح البرنامج.
- زر Check Watch List Now.
- لا يوجد Polling دوري أو Background Service.
- لا يوجد Login أو Browser Cookies أو Session Storage.

## قرار أمني/وظيفي مهم

صاحب المشروع قرر أن الاستخدام شخصي وأن تسجيل الدخول غير مطلوب.

لذلك:
- تم حذف `browser-cookie3`.
- تم حذف Browser Session Import.
- تم حذف Session files من منطق التشغيل.
- التطبيق يستهدف الحسابات العامة فقط.

لا تعيد Login أو Cookie Import إلا بطلب صريح مستقبلي من صاحب المشروع.

## Watch List

Watch List **ليست** كل الحسابات التي يعمل لها المستخدم Follow على Instagram.

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

## قواعد التطوير

1. OOP + SOLID.
2. لا Business Logic داخل UI.
3. التعليقات/Docstrings بالعربي.
4. لا Password/Cookies/Sessions.
5. لا تجعل Watch List مساوية لـInstagram Following.
6. لا تضف Polling دوري إلا بقرار صريح.
7. أي تعديل في Sync يحتاج Tests.
8. لا تعتبر التغيير مكتملًا إلا بعد Ruff + Pytest + CI أخضر.
