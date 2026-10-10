# Security Notes

## تسجيل الدخول

التطبيق يحتاج Session عند الوصول إلى حساب Private.

التصميم الحالي يتجنب قراءة Cookies المتصفح الأساسي تمامًا:

- لا توجد مكتبة browser-cookie3.
- لا يقرأ Chrome أو Edge أو Firefox.
- يفتح Instagram داخل QWebEngine مخصص للتطبيق.
- المستخدم يكتب Password و2FA مباشرة داخل صفحة Instagram.
- كود التطبيق لا يخزن Password.
- بعد نجاح الدخول، يتم حفظ Session محلية فقط.

ملف Session حساس لأنه يمثل جلسة الحساب، لذلك:

- محفوظ خارج Repository.
- محجوب بواسطة .gitignore.
- لا يسجل محتواه في Logs.
- لا يجب مشاركته مع أي شخص.

## حدود الصلاحية

وجود Session لا يتجاوز Privacy في Instagram.

الحساب Private يعمل فقط إذا كان الحساب المتصل يستطيع بالفعل رؤية محتواه.
لا يوجد أي تجاوز لطلب Follow أو 2FA أو قيود الحساب.

## أمان الملفات

- اسم Target Profile يتم التحقق منه لمنع Path Traversal.
- التنزيل يذهب إلى .part أولًا ثم يتحول للاسم النهائي بعد النجاح.
- لا يوجد Telemetry أو Analytics أو Server مركزي.
