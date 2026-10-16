# /prep — raw footage to a Premiere project, ready to edit

**[العربية ↓](#arabic)**

A Claude Code skill by **Ismail — [ISMAILX](https://ismailx.com)**. Hand it a folder of raw footage and it builds a Premiere Pro project
with three sequences:

| Sequence | What it is |
|---|---|
| **Assembly** | every camera and every mic in sync, untouched — camera audio kept but disabled |
| **Rough Cut** | only what will never be used is gone: setup, countdowns, "cut" calls, abandoned takes, talk not for the viewer, the tail |
| **Tight** | silences removed for pace across all mics at once; every moment that needs a human call is left alone with a `DECIDE` marker |

You open Premiere and start editing — or pick which of the three you continue from.

## What makes it different
- **Real multi-camera, multi-mic sync.** Audio cross-correlation measured in up to 15 windows per file, accepted only within one
  frame; separate recorders become the sync base. Tested on a 3-camera, 3-recorder, 46-minute show.
- **It never decides your edit.** The rough cut only removes the obvious; when in doubt it keeps. The tight cut is rhythm only.
- **Every step is proven.** Clip positions are read back from Premiere in ticks and compared with the plan — zero mismatches or it fixes them.
- **Your files are safe.** Originals are never renamed, moved or touched; every stage is a new sequence; other open projects are never touched.

Real run: 45:56 of raw footage → Rough Cut 33:24 → Tight 28:19 with 78 `DECIDE` markers, overnight, no editor in the room.

## Install
See [`INSTALL.md`](INSTALL.md). In short: ffmpeg + Python (numpy, mlx-whisper) + Premiere Pro + the `premiere-pro` MCP bridge, then
clone this repo into `~/.claude/skills/prep`.

## Use
In Claude Code:
```
/prep  /path/to/footage  "Video name"
```

## Inside
| | |
|---|---|
| `SKILL.md` | the workflow Claude follows, step by step, with every trap already hit |
| `scripts/` | probe · sync · phrases (transcription) · cutlist · tight / tight_plan · verify_rebuild |
| `premiere/` | ExtendScript run through the bridge: build a cut from kept ranges, dump a sequence, batch build, fix, markers |
| `tools/open_bridge_panel.js` | opens the bridge panel when Premiere's Extensions menu is missing |

The rough-cut approach follows the Editing Lair workflow (editinglair.com/roughcut).

## Limits
- Runs on macOS and Windows. Proven on macOS / Apple Silicon / Premiere Pro 2026; the Windows path (faster-whisper, Windows temp folder) is written but not yet run on a Windows PC.
- Building a long Tight in Premiere is slow (≈ 40 min for a 30-minute show) — it runs unattended, but it is not instant.
- Transcripts of several people talking over each other are rough; they are used to find takes, not to quote.

MIT licence.

---

<a id="arabic"></a>
<div dir="rtl">

# /prep — من فوتج خام إلى مشروع بريمير جاهز للمونتاج

سكل لـ Claude Code من **إسماعيل — [ISMAILX](https://ismailx.com)**. تعطيه مجلد الفوتج الخام، ويطلع لك مشروع Premiere Pro فيه ثلاث تايم لاينات:

| التايم لاين | وش فيه |
|---|---|
| **Assembly** | كل الكاميرات والمايكات متزامنة وما انلمس فيها شي، وصوت الكاميرات موجود بس معطّل |
| **Rough Cut** | انشال بس اللي مستحيل ينستخدم: التجهيز قبل التصوير، العدّ، "كت"، الإعادات، الكلام اللي مو للمشاهد، والذيل بعد النهاية |
| **Tight** | انشالت السكتات عشان الإيقاع يصير أسرع، وأي لحظة تحتاج قرار منك ما تنلمس وعليها ماركر `DECIDE` |

تفتح بريمير وتبدأ تمنتج، وأنت تختار تكمل من أي تايم لاين.

## وش يميزها
- **سينك حقيقي لأكثر من كاميرا وأكثر من مايك.** تقيس الصوت في أكثر من نقطة بكل ملف، وما تقبل إلا لو التطابق داخل فريم واحد. ولو عندك مسجلات صوت منفصلة، هي تصير أساس السينك. انجربت على حلقة فيها 3 كاميرات و3 مايكات ومدتها 46 دقيقة.
- **ما تقرر مونتاجك عنك.** الرف كت يشيل الواضح بس، ولو شكّت تخلي. والـTight إيقاع بس، ما يلمس المحتوى.
- **كل خطوة متأكد منها.** تقرأ مكان كل كليب من بريمير وتقارنه بالخطة. لو فيه فرق ولو فريم، تصلحه.
- **ملفاتك بأمان.** الملفات الأصلية ما تنلمس ولا تنتقل ولا يتغير اسمها، كل مرحلة تايم لاين جديد، وأي مشروع ثاني مفتوح ما ينلمس.

**تجربة حقيقية:** 45:56 فوتج خام ← رف كت 33:24 ← Tight 28:19 مع 78 ماركر `DECIDE`. اشتغلت بالليل وأنا نايم.

## التثبيت
الخطوات كاملة في [`INSTALL.md`](INSTALL.md). باختصار تحتاج:
- ffmpeg و Node و Python
- Premiere Pro
- جسر `premiere-pro` (MCP) اللي يخلي Claude يشتغل داخل بريمير
- وبعدها تنسخ هالمستودع في `~/.claude/skills/prep`

## الاستخدام
داخل Claude Code:
```
/prep  /path/to/footage  "اسم الفيديو"
```

## يشتغل على
- **ماك:** مجرب بالكامل (Apple Silicon مع Premiere Pro 2026).
- **ويندوز:** الطريقة مكتوبة كاملة في ملف التثبيت، بس ما انجربت على جهاز ويندوز بعد. لو طلع لك خطأ، أرسله.

## حدود لازم تعرفها
- بناء الـTight داخل بريمير بطيء، حوالي 40 دقيقة لحلقة نص ساعة. يشتغل لحاله وأنت مو موجود، بس مو فوري.
- لما أكثر من شخص يتكلمون فوق بعض، التفريغ يطلع تقريبي. يكفي لتحديد اللقطات، مو للكابشن.

الرخصة MIT: استخدمها وعدّل عليها بحرية، بشرط يبقى اسمي.

</div>

