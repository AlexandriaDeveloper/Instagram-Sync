# Instagram Sync

برنامج Desktop شخصي لتنزيل ومزامنة الصور والفيديوهات من **الحسابات العامة** على Instagram.

## السلوك الأساسي

- لا يوجد Login داخل البرنامج.
- لا يتم قراءة Cookies من Chrome أو Edge أو أي متصفح.
- Manual Sync لأي حساب عام تكتبه.
- أول Sync ينزل المحتوى المتاح.
- بعد ذلك ينزل العناصر الجديدة فقط.
- يدعم Posts وReels وCarousel.
- SQLite محلية تمنع التكرار باستخدام `shortcode + item_index`.

## Watch List

يمكنك إضافة حسابات عامة محددة إلى Watch List داخل البرنامج.

**هذه القائمة مستقلة تمامًا عن الأشخاص الذين تعمل لهم Follow على Instagram.**

عند كل مرة تفتح فيها البرنامج:

1. يحصل Check واحد فقط للحسابات الموجودة في Watch List.
2. ينزل الجديد فقط.
3. يحدث Last Check.
4. يتوقف الـWorker.

لا يوجد Check كل 15 أو 30 دقيقة، ولا Background Polling.

يمكنك أيضًا الضغط على **Check Watch List Now** في أي وقت.

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

## الاختبارات

```powershell
pip install -e .[dev]
ruff check src tests
pytest -q
```

## حدود النسخة الحالية

Instagram قد يطلب Login لبعض المحتوى أو يغير سلوكه مع الحسابات العامة.
في هذه النسخة قررنا عمدًا عدم إضافة Login لأن الاستخدام شخصي والهدف هو البساطة والأمان.
