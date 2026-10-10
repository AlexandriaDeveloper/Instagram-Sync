# Security Notes

## المبادئ

1. البرنامج لا يطلب أو يخزن Password لـInstagram.
2. Session يتم استيرادها من المتصفح المحلي بعد أن يسجل المستخدم الدخول بنفسه.
3. Session file تحفظ خارج Repository.
4. `.gitignore` يمنع Sessions وDatabases وDownloads من الدخول إلى Git.
5. اسم Target Profile يتم التحقق منه لمنع Path Traversal.
6. الملف ينزل أولًا كـ`.part` ولا يتحول للاسم النهائي إلا بعد اكتماله.
7. لا يوجد Telemetry أو Analytics أو Server خاص بالمشروع.
8. لا يوجد Licensing أو Payment أو حساب مركزي لأن المشروع شخصي.

## بيانات حساسة

البيانات الحساسة الوحيدة المحتملة هي Session المحلية.

لا يجب:

- رفعها إلى Git.
- مشاركتها مع شخص آخر.
- تسجيل Cookie values في Logs.

## حدود الأمان

البرنامج يعتمد على Instagram وInstaloader، لذلك تغييرات المنصة قد تكسر القراءة أو Session.
هذا ليس تجاوزًا للحماية؛ البرنامج يعمل فقط ضمن صلاحية الجلسة الحالية.

## Audit Checklist

- تأكد أن Git لا يحتوي ملفات `.session`.
- تأكد أن Git لا يحتوي Cookies أو Passwords.
- راجع Dependencies قبل التحديث.
- شغل `ruff check src tests`.
- شغل `pytest -q`.
- راجع أي تغيير في `browser_session.py` بعناية لأنه يتعامل مع Cookies محلية.
