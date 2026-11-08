# CapCut Stripped

**CapCut, minus the clutter.** No AI buttons everywhere, no "Try Pro" pop-ups every time you open it, and about half
the disk space. Editing and exporting work exactly like before.

| | Stock CapCut | CapCut Stripped |
|---|---|---|
| Program on disk | 1,849 MB | **about 540 MB** |
| Whole CapCut folder | about 2,180 MB | **about 1,080 MB** |
| AI buttons in the editor | everywhere | gone |
| Pro / Ultra pop-ups at start | yes | gone |

## Quick start

1. Install CapCut from [capcut.com](https://www.capcut.com). Open it once, then close it.
2. Download **CapCut-Stripped-Kit.zip** from [Releases](https://github.com/Swazi-1/CapCut-Stripped/releases/latest) and unzip it.
3. Double-click **`Make CapCut Stripped.bat`**. A progress bar runs for a few minutes.
4. Open CapCut with the new **CapCut Stripped** shortcut on your desktop. Done.

Tip: the first time you export, set **Codec** to **H.264**.

## What's gone

**In the editor:** EditPilot, the "Generate" sidebar row, the AI avatar tab, AI extend, the AI edit magic wand,
AI stylize, the AI clipper bar and the "No media? Create with these tools" cards.

**On the home screen:** the AI cards and AI section. Your projects sit right under "Create project".

**Ads:** the "Get 7 days free Pro" button and the start pop-ups ("CapCut Pro", "7-day free trial",
"CapCut Ultra is live" and friends).

**Under the hood:** built-in AI models, the AI agent, 24 extra languages (English stays), the auto-updater,
crash reports and old caches.

## What still works

Importing, cutting, text, transitions, effects, online stickers, audio, saved projects, and export in 1080p and 4K.
All of it was tested after stripping.

## How it works

- **Smaller:** the bat deletes the parts CapCut doesn't need, then compresses the rest with Windows' own file
  compression. CapCut reads the same files as before; they just take less space.
- **Cleaner:** the **CapCut Stripped** shortcut starts CapCut and hides the AI buttons and ads in memory while it
  runs. CapCut's own files stay original, so online stickers and effects keep working.

## Good to know

- **Use the shortcut.** Opening CapCut the normal way shows normal CapCut, AI stuff and all.
- **The shortcut needs [Python](https://www.python.org).** Without it CapCut still gets smaller, but the AI buttons
  and pop-ups stay.
- **CapCut already running?** Then the shortcut can't hide anything. Close CapCut fully and use the shortcut again.
- **No undo.** Removed parts are deleted for good. Want normal CapCut back? Uninstall it and install it fresh.
- **After a CapCut update,** run `Make CapCut Stripped.bat` again. The shortcut is made for CapCut **9.7.1.4203**;
  on other versions CapCut just starts normally.

## Optional: offline mode

**`Offline mode ON.bat`** blocks CapCut from the internet with Windows Firewall: no tracking, no updates. Windows asks
for permission, click Yes. Effects you've never used before can't download while it's on, so run
**`Offline mode OFF.bat`** when you need new ones.

## What's in the kit

| File | What it does |
|---|---|
| `Make CapCut Stripped.bat` | Strips and compresses CapCut, makes the desktop shortcut |
| `Offline mode ON.bat` / `OFF.bat` | Blocks / unblocks CapCut's internet |
| `READ ME FIRST.txt` | The short version of this page |
| `WHAT'S NEW.txt` | Changes in every version |
| `_files (don't touch)/` | The scripts that do the work |

---

Made and tested with CapCut 9.7.1.4203 on Windows (November 2026). Earlier versions of this project were called
"CapCut Lite". This project contains no CapCut code. CapCut is a ByteDance product; this project isn't affiliated
with them.
