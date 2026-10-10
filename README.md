# Instagram Sync

برنامج Desktop شخصي لتنزيل ومزامنة الصور والفيديوهات من حسابات Instagram التي يحق لك الوصول إليها.

## الفكرة

- أول مرة: البرنامج يقرأ المحتوى المتاح في الحساب وينزله.
- بعد ذلك: كل عملية **Sync** تنزل العناصر الجديدة فقط.
- كل عنصر يتم تعريفه بمفتاح ثابت: `shortcode + item_index`.
- قاعدة SQLite محلية تحفظ ما تم تنزيله، لذلك لا نعتمد على اسم الملف فقط.
- يدعم Posts وReels وCarousel.
- لا يخزن كلمة مرور Instagram.
- يمكن استيراد جلسة تسجيل الدخول من متصفح محلي مسجل فيه Instagram.

## حدود الاستخدام

استخدم البرنامج للحسابات العامة أو المحتوى الذي لديك صلاحية للوصول إليه.
البرنامج لا يتجاوز Private Account أو 2FA أو صلاحيات Instagram.

## المتطلبات

- Python 3.11 أو أحدث.
- Windows 10/11 هو الهدف الأساسي.
- Chrome / Edge / Firefox أو متصفح مدعوم إذا أردت استيراد Session.

## التشغيل من الكود

```powershell
git clone https://github.com/AlexandriaDeveloper/Instagram-Sync.git
cd Instagram-Sync

py -m venv .venv
.\.venv\Scripts\Activate.ps1

python -m pip install -U pip
pip install -e .
python -m instagram_sync
```

## طريقة الاستخدام

1. اكتب اسم الحساب المطلوب مزامنته.
2. اختر مجلد الحفظ.
3. لو الحساب عام، جرّب **Sync Now** مباشرة.
4. لو تحتاج تسجيل الدخول:
   - سجل دخولك إلى Instagram في متصفحك الطبيعي.
   - اختر المتصفح من البرنامج.
   - اضغط **Connect from Browser**.
   - البرنامج يستورد Cookies الخاصة بـInstagram محليًا، يتحقق من الجلسة، ثم يحفظ Session محلية.
5. اضغط **Sync Now**.

## بناء EXE على Windows

```bat
build_windows.bat
```

الناتج:

```text
dist\InstagramSync\InstagramSync.exe
```

## أين توجد البيانات؟

البرنامج لا يضع قاعدة البيانات أو Session داخل Git.

بيانات التطبيق توضع في مجلد Application Data الخاص بنظام التشغيل، وتشمل:

- SQLite database.
- Instagram session file.

ملفات الصور والفيديوهات تذهب فقط إلى مجلد التنزيل الذي تختاره.

## المعمارية

```text
presentation
    |
composition (Dependency Injection)
    |
application (use cases + ports)
    |
domain
    ^
    |
infrastructure (implements ports)
```

التفاصيل موجودة في:

- `docs/ARCHITECTURE.md`
- `docs/AI_HANDOFF.md`
- `docs/SECURITY.md`

## الاختبارات

```powershell
pip install -e .[dev]
ruff check src tests
pytest -q
```

GitHub Actions يشغل نفس الفحوصات تلقائيًا مع كل Push وPull Request.
