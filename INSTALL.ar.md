<div dir="rtl">

# التثبيت

**[English](INSTALL.md)**

يشتغل على ماك وويندوز مع Premiere Pro 2026 و Claude Code. مجرب على ماك (Apple Silicon). طريقة ويندوز تحت مكتوبة كاملة، بس ما انجربت على جهاز ويندوز بعد.

> ⚠️ **لازم يكون عندك اشتراك Claude مدفوع** (Pro أو Max، أو حساب API من Anthropic). الأداة تشتغل داخل Claude Code، وهو مو موجود في الخطة المجانية.

## 1. البرامج الأساسية

**ماك**

</div>

```bash
brew install ffmpeg node python
```
```bash
python3 -m venv ~/.prep-venv && ~/.prep-venv/bin/pip install -r requirements.txt
```

<div dir="rtl">

وتشغّل سكربتات الأداة بـ `~/.prep-venv/bin/python`.

**ويندوز** (من PowerShell)

</div>

```powershell
winget install --id Gyan.FFmpeg -e; winget install --id OpenJS.NodeJS.LTS -e; winget install --id Python.Python.3.12 -e
```

<div dir="rtl">

سكّر PowerShell وافتحه من جديد، وبعدها:

</div>

```powershell
py -3 -m venv $HOME\.prep-venv; & $HOME\.prep-venv\Scripts\python.exe -m pip install -r requirements.txt
```

<div dir="rtl">

وتشغّل سكربتات الأداة بـ `$HOME\.prep-venv\Scripts\python.exe`.

**أداة التفريغ تنختار تلقائياً:** على ماك Apple Silicon تستخدم `mlx-whisper`، وعلى باقي الأجهزة `faster-whisper`. لو عندك كرت NVIDIA شغال تستخدمه، وإلا تشتغل على المعالج وتكون أبطأ.
أول تفريغ ينزّل الموديل (حوالي 1.5 جيجا)، مرة وحدة بس.

## 2. الأداة نفسها

</div>

```bash
git clone https://github.com/ISMAIL-debug-ctrl/prep ~/.claude/skills/prep
```

<div dir="rtl">

على ويندوز:

</div>

```powershell
git clone https://github.com/ISMAIL-debug-ctrl/prep $HOME\.claude\skills\prep
```

<div dir="rtl">

بعدها Claude Code يعرض لك أمر `/prep`.

## 3. جسر بريمير

هذا اللي يخلي Claude يوصل لبريمير ويشتغل داخله. اسمه [adobe-premiere-pro-mcp](https://www.npmjs.com/package/adobe-premiere-pro-mcp)، برنامج من طرف ثالث برخصة MIT، فاقرأ عنه قبل ما تثبته. النسخة المستخدمة: 1.2.8.

**أنت تشغّل هالأوامر بنفسك:**

</div>

```bash
npm install -g adobe-premiere-pro-mcp@1.2.8 --ignore-scripts
```
```bash
premiere-pro-mcp --install-cep
```
```bash
premiere-pro-mcp --doctor
```

<div dir="rtl">

**اختياري:** يطفي إرسال بيانات الاستخدام المجهولة:

</div>

```bash
mkdir -p ~/.premiere-mcp-bridge && printf '{\n  "telemetry": false,\n  "updateCheck": false\n}\n' > ~/.premiere-mcp-bridge/config.json
```

<div dir="rtl">

**على ويندوز:** طريقة التثبيت الخاصة بالجسر هي `npm run setup:win` من المستودع حقه (تفاصيلها في ملف QUICKSTART عندهم). وفي لوحة الجسر داخل بريمير، خلّ Temp Directory يكون `%TEMP%\premiere-mcp-bridge`، واستخدم نفس المجلد لـ `PREMIERE_TEMP_DIR` في ملف `.mcp.json`.

**تسجيل الجسر لـ Claude Code:** انسخ `mcp.example.json` وسمّه `.mcp.json` في المجلد اللي تشغّل منه Claude، أو أضف نفس الإعداد بأمر `claude mcp add`.

**تشغيل الجسر:**
1. سكّر بريمير وافتحه من جديد، وافتح أي مشروع.
2. من القائمة: `Window > Extensions > MCP Bridge (CEP)` واضغط Start.
3. ارجع لـ Claude وقل له: "تأكد إن بريمير متصل". لو قال **connected**، جاهز.

**لو قائمة Extensions مختفية عندك:** الأمر `node tools/open_bridge_panel.js` يفتح لوحة الجسر عن طريق لوحة ثانية مفتوحة في بريمير.

## دافنشي ريزولف (بدل بريمير)

الأداة تشتغل داخل دافنشي عن طريق [MCP دافنشي](https://github.com/samuelgursky/davinci-resolve-mcp) من المجتمع (رخصة MIT، طرف ثالث، فاقرأ عنه قبل التثبيت):

</div>

```bash
npx davinci-resolve-mcp setup
```

<div dir="rtl">

- **دافنشي ستوديو (المدفوع):** من Preferences > System > General خلّ External scripting using على **Local**.
- **دافنشي المجاني:** التحكم الخارجي ميزة في ستوديو بس. ملف الشرح حق الـMCP فيه طريقة بديلة بسكربت يشتغل من داخل دافنشي (Workspace > Scripts).

افتح دافنشي وقل لـClaude: "تأكد إن دافنشي متصل".

## ملاحظات ويندوز
- المسارات اللي تنعطى لسكربتات بريمير تكون بشرطة للأمام: `C:/Users/you/Videos/shoot`
- أداة `tools/open_bridge_panel.js` تستخدم على ويندوز المجلد `%TEMP%\premiere-mcp-bridge`، أو `PREMIERE_TEMP_DIR` لو محدده.
- كل الملفات اللي تكتبها السكربتات بترميز UTF-8، فالأسماء العربية ما تخرب.

</div>
