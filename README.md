# CapCut Stripped

Make the CapCut desktop app (Windows) smaller and cleaner, without breaking editing or exporting.

It removes:
- the AI extras (AI models, the AI agent, local AI engines, speech/auto-caption engine)
- 24 extra UI languages (English is kept)
- the auto-updater, crash reporting and background push service
- the "Join Pro" / subscription pop-ups and store panels
- downloaded caches, and stops some of them from coming back

On CapCut 9.7.1 this took the program from **1,849 MB to 1,179 MB**. Import, timeline editing, cut/split, text,
transitions, audio, opening saved projects and export at 1080p and 4K (H.264) were all tested afterwards.

**Nothing is deleted.** Removed parts are moved to `%LOCALAPPDATA%\CapCut\_removed\`, so you can always undo.

## How to use

1. Install CapCut from capcut.com like you normally would. Open it once, then close it.
2. Download **CapCut-Lite-Kit.zip** from [Releases](https://github.com/Swazi-1/CapCut-Lite/releases/latest) and unzip it.
3. Double-click **`Make CapCut Lite.bat`**. A window opens, works for a few seconds and tells you when it's finished.
4. Open CapCut with the **CapCut Lite** shortcut on your desktop and edit as usual. The first time you export, set **Codec** to **H.264**.

Works for any Windows user name. Make CapCut Lite and Undo don't need admin rights.

### Optional: offline mode

**`Offline mode ON.bat`** blocks CapCut's internet with Windows Firewall: no tracking, no updates, no AI cloud calls.
Windows asks for permission; click Yes. Effects and transitions you've never used can't download while it's on.
**`Offline mode OFF.bat`** turns it off again.

### After a CapCut update

Updates bring the removed parts back. Run `Make CapCut Lite.bat` again.

### Something broken?

Run **`Undo - normal CapCut.bat`** and CapCut is back to how it was.

## What's in here

| File | What it does |
|---|---|
| `Make CapCut Lite.bat` | Strips CapCut |
| `Undo - normal CapCut.bat` | Puts everything back |
| `Offline mode ON.bat` / `OFF.bat` | Blocks / unblocks CapCut's internet |
| `_files (don't touch)/lite.ps1` | Does the moving and restoring |
| `_files (don't touch)/lite-manifest.txt` | The list of what gets removed |
| `_files (don't touch)/offline.ps1` | Creates / removes the firewall rules |
| `_files (don't touch)/capcut_lite.pyw` | The CapCut Lite shortcut: starts CapCut and hides the AI and Pro clutter |
| `_files (don't touch)/patch_cards.py` | Home-screen AI cards setting |
| `WHAT'S NEW.txt` | Changes since the first version |

## Notes

- Made and tested with CapCut **9.7.1.4203** (November 2026). Newer versions should work: anything that's missing is
  skipped safely, but new extras CapCut adds later won't be removed.
- Some parts can't be removed because CapCut won't start without them (the built-in browser, telemetry and
  cloud-upload libraries). Offline mode is the way to stop those from going online.
- The **CapCut Lite** desktop shortcut (needs Python) also hides the AI cards and buttons, the "Get 7 days free Pro"
  button and the Pro / Ultra start pop-ups. It changes CapCut only in memory while it runs; CapCut's files on disk
  stay original, so online stickers and effects keep working. It only acts on CapCut 9.7.1.4203; on other versions
  CapCut just starts normally. See `WHAT'S NEW.txt` for the full list.
- This project contains no CapCut code. CapCut is a ByteDance product; this project isn't affiliated with them.
