# Security Notes

## المبادئ

1. البرنامج لا يطلب أو يخزن Password لـInstagram.
2. البرنامج لا يقرأ Cookies من أي متصفح.
3. لا يوجد Session Storage داخل التطبيق.
4. SQLite وDownloads فقط هي البيانات المحلية الأساسية.
5. اسم Target Profile يتم التحقق منه لمنع Path Traversal.
6. الملف ينزل أولًا كـ`.part` ولا يتحول للاسم النهائي إلا بعد اكتماله.
7. لا يوجد Telemetry أو Analytics أو Server خاص بالمشروع.
8. لا يوجد Licensing أو Payment لأن المشروع شخصي.

## حدود الأمان والوظيفة

التطبيق يستهدف الحسابات العامة فقط.

Instagram قد يغير Endpoints أو Rate Limits أو يطلب Login لبعض المحتوى العام.
لو حدث ذلك، يتم التعامل معه كتغيير وظيفي مستقبلي وليس سببًا لإعادة إدخال Cookie Reading تلقائيًا.

## Audit Checklist

- تأكد أن Dependencies لا تحتوي مكتبات Browser Cookie Reading.
- تأكد أن Git لا يحتوي Passwords أو Cookies أو Sessions.
- راجع Dependencies قبل التحديث.
- شغل `ruff check src tests`.
- شغل `pytest -q`.
