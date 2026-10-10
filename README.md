# Instagram Sync

برنامج Desktop شخصي لتنزيل ومزامنة الصور والفيديوهات من Instagram.

## السلوك الأساسي

- Manual Sync لأي حساب تكتبه.
- أول Sync ينزل المحتوى المتاح.
- بعد ذلك ينزل العناصر الجديدة فقط.
- يدعم Posts وReels وCarousel.
- SQLite محلية تمنع التكرار باستخدام `shortcode + item_index`.
- يدعم الحسابات العامة.
- يدعم الحسابات الخاصة التي **حساب Instagram المتصل مسموح له أصلًا برؤيتها**.

## تسجيل الدخول الآمن

البرنامج لا يقرأ Cookies من Chrome أو Edge أو Firefox.

عند الضغط على **Login to Instagram**:

1. يفتح Instagram داخل نافذة Browser مخصصة للتطبيق.
2. أنت تدخل بياناتك مباشرة داخل صفحة Instagram.
3. البرنامج نفسه لا يستقبل أو يخزن الـPassword.
4. بعد نجاح تسجيل الدخول، يأخذ Session من متصفح التطبيق نفسه فقط.
5. يحفظ Session محلية خارج Git لإعادة استخدامها.

لو حسابك عليه 2FA، تكمله داخل صفحة Instagram نفسها.

## Watch List

تضيف أنت الحسابات التي تريد متابعتها داخل البرنامج.

عند فتح التطبيق يحصل Check واحد فقط للـWatch List وينزل الجديد فقط.
لا يوجد Polling دوري، ولا يتم استخدام قائمة Following بالكامل.

## التشغيل

```powershell
git clone https://github.com/AlexandriaDeveloper/Instagram-Sync.git
cd Instagram-Sync

py -m venv .venv
.\.venv\Scripts\Activate.ps1

python -m pip install -U pip
pip install -e .
python -m instagram_sync
```

## Build Windows

```bat
build_windows.bat
```

## التوثيق

- `docs/ARCHITECTURE.md`
- `docs/AI_HANDOFF.md`
- `docs/SECURITY.md`
