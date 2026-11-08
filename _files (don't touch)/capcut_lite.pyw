"""CapCut Lite launcher.
VECreator.dll stays the signed original on disk. This starts CapCut, waits until CapCut.exe has loaded
VECreator.dll, pauses the process for a moment, writes the CapCut Lite byte changes into its memory and lets it run.
Every old byte is checked first; if anything differs (e.g. CapCut updated) nothing is written and CapCut runs stock.
Log: capcut_lite.log next to this file."""
import ctypes, ctypes.wintypes as W, os, sys, time, subprocess, glob

# (rva, original bytes, new bytes) for VECreator.dll 9.7.1.4203 (built by diffing patch_cards.py output with the original)
TABLE = [
    (0x11b9bd0, "4883ec", "31c0c3"),   # 5  home EditPilot card getter
    # 14 editor media sidebar "Generate" (AI) row: MediaTreeViewModel::updateTabs builds the parent key list. The AI key is moved
    # to the last slot and the list end pointer is pulled back one slot, so it is not added (two branches, 5 and 4 keys).
    (0x2f3bffa, "42e4520c", "e2e3520c"),
    (0x2f3c00e, "cee3520c", "e6e3520c"),
    (0x2f3c022, "d2e3520c", "1ae4520c"),
    (0x2f3c0be, "d8", "c0"),
    (0x2f3c0fc, "40e3520c", "e0e2520c"),
    (0x2f3c110, "cce2520c", "e4e2520c"),
    (0x2f3c124, "d0e2520c", "18e3520c"),
    (0x2f3c1c7, "60", "48"),
    (0x2ddb848, "e8330fd9fd", "9090909090"),  # 15 editor top tab bar: do not add the "AI avatar" tab (id 0xc): nop the vector-insert call
    # 16 media panel "No media? Create with these tools" row: text, 2px line, the 3 cards (Generate / AI avatars / Record): visible = false
    (0xb93d838, "2fcf", "0a02"),
    (0xb93db80, "2fed", "0a02"),
    (0xb93de50, "2f01", "0a02"),
    (0xb93e098, "2f15", "0a02"),
    (0xb93e3a8, "2f33", "0a02"),
    # 16 the two CutLine rules beside that text get zero width (right/left anchor = the other edge, same object as the opposite anchor)
    (0xb93dcc1, "f5", "f3"),
    (0xb93dd61, "f9", "f7"),
    (0xb9382e8, "2fcc", "0a02"),       # 17 media panel bottom "AI clipper / Start clipping / Try free" bar (roughCutEnter): visible = false (bottom inset becomes 0)
    (0xb177b10, "2fa2", "0a02"),       # 18 on-clip "AI extend" edge handle (left, unit 0xb161020): visible = false
    (0xb24d230, "2fd6", "0a02"),       # 18 same handle, second timeline unit (0xb231550)
    (0x289a46a, "0f84ea030000", "e9eb03000090"),  # 18 timeline toolbar "AI extend" button: availability check jumps to the hidden path (je -> jmp 0x289a85a)
    (0x289aa12, "0f84d4030000", "e9d503000090"),  # 19 timeline toolbar "AI edit" (wand) button: availability check jumps to the hidden path (je -> jmp 0x289adec)
    (0x380af62, "4883470810", "9090909090"),  # 20 clip inspector (right panel) "AI stylize" tab: skip the vector push of that tab (video_aigc block)
    (0xd8b2b98, "2f57", "0a02"),       # 21 title bar "Get 7 days free Pro" button (Loader ccProButton): active = false
    (0x1b18b00, "48895c", "31c0c3"),   # 22 CustomisePopupManager::showPopup (server-configured launch/edit popups, e.g. the Pro offer): return at once
    (0x4ef6240, "48895c", "31c0c3"),   # 23 HomePageViewModel::tryShowSplashScreen (the 'CapCut Pro / 7-day free trial' popup on start, SplashScreen.qml): return at once
    (0x4ec55f0, "48895c", "31c0c3"),   # 23 the splash show function itself (also called from the async VIP-check callback 0x4eed36b): return at once
    (0x5573500, "48895c", "31c0c3"),   # 24 commerce_splash_modal (Lynx 'CapCut Ultra is live' offer) show: return at once
    (0x56bf850, "48895c", "31c0c3"),   # 24 StartUpFeatureIntroDialogModel::showDialog (startup intro / splash popup requests): return at once
    (0x6eeb890, "48895c", "31c0c3"),   # 26 the only builder of SplashScreen.qml (Pro / free-trial / Ultra start pop-up; also called from async callback 0x4ece068): return at once
    (0xc7c3990, "2e1f180602", "0600180602"),  # 13 editor EditPilot pill window: width = fixedWidth -> 0
    (0xc7c39d8, "2e20180602", "0600180602"),  # 13 height = fixedHeight -> 0 (window is transparent, so it is gone)
    (0xd55ff88, "2e21180602", "0600180602"),  # 27 second EditPilot pill window ("Omni Agent" unit 0xd55d790): width = fixedWidth -> 0
    (0xd55ffd0, "2e22180602", "0600180602"),  # 27 same, height = fixedHeight -> 0
    (0x4ed5830, "48895c", "31c0c3"),   # 2  old AI section
    (0x54f3fa0, "48895c", "31c0c3"),   # 1  card filter
    (0x5563f70, "40", "c3"),           # 7  home tool fallback
    (0xd1ce40c, "68", "78"),           # 3  sidebar promo banner (copy 1)
    (0xd26011c, "68", "78"),           # 3  sidebar promo banner (copy 2)
    (0xd2eebb8, "2f67", "0a02"),       # 9  tool row hidden
    (0xd2f5038, "88", "00"),           # 11 card-row slot height 136 -> 0
    (0xd2f50e0, "14", "00"),           # 28 new home layout: tool container topMargin 20 -> 0
    (0xd2f5635, "40", "10"),           # 28 new home layout: Projects header topMargin 64 -> 16 (Projects right under Create project)
    (0xd3b7344, "4c", "58"),           # 8  "loading failed" text
    (0xd3b7d30, "11", "ad"),           # 10 card row hidden
    (0xd3b7d34, "08", "00"),
    (0xd3b7d36, "02", "01"),
    (0xd3b7d38, "01", "00"),
    (0xd3b7d48, "10", "83"),
    (0xd3b7d4e, "02", "01"),
    (0xd3b7d50, "00", "01"),
    (0xd772df8, "68", "78"),           # 4  sidebar AI section key
    (0xd772e18, "68", "78"),           # 4  sidebar AI section key
]
MODULE = "vecreator.dll"
LOG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "capcut_lite.log")

k32 = ctypes.WinDLL("kernel32", use_last_error=True)
psapi = ctypes.WinDLL("psapi", use_last_error=True)
ntdll = ctypes.WinDLL("ntdll")
k32.OpenProcess.restype = W.HANDLE
k32.OpenProcess.argtypes = [W.DWORD, W.BOOL, W.DWORD]
k32.CreateToolhelp32Snapshot.restype = W.HANDLE
k32.CreateToolhelp32Snapshot.argtypes = [W.DWORD, W.DWORD]
k32.Process32FirstW.argtypes = k32.Process32NextW.argtypes = [W.HANDLE, ctypes.c_void_p]
k32.WaitForSingleObject.argtypes = [W.HANDLE, W.DWORD]
k32.ReadProcessMemory.argtypes = [W.HANDLE, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)]
k32.WriteProcessMemory.argtypes = k32.ReadProcessMemory.argtypes
k32.VirtualProtectEx.argtypes = [W.HANDLE, ctypes.c_void_p, ctypes.c_size_t, W.DWORD, ctypes.POINTER(W.DWORD)]
k32.FlushInstructionCache.argtypes = [W.HANDLE, ctypes.c_void_p, ctypes.c_size_t]
k32.QueryFullProcessImageNameW.argtypes = [W.HANDLE, W.DWORD, W.LPWSTR, ctypes.POINTER(W.DWORD)]
k32.CloseHandle.argtypes = [W.HANDLE]
psapi.EnumProcessModulesEx.argtypes = [W.HANDLE, ctypes.c_void_p, W.DWORD, ctypes.POINTER(W.DWORD), W.DWORD]
psapi.GetModuleBaseNameW.argtypes = [W.HANDLE, ctypes.c_void_p, W.LPWSTR, W.DWORD]
ntdll.NtSuspendProcess.argtypes = ntdll.NtResumeProcess.argtypes = [W.HANDLE]

ACCESS = 0x0400 | 0x0010 | 0x0020 | 0x0008 | 0x0800 | 0x1000 | 0x100000  # query, vm read/write/op, suspend/resume, synchronize


class PE32(ctypes.Structure):
    _fields_ = [("dwSize", W.DWORD), ("cntUsage", W.DWORD), ("th32ProcessID", W.DWORD), ("th32DefaultHeapID", ctypes.c_size_t),
                ("th32ModuleID", W.DWORD), ("cntThreads", W.DWORD), ("th32ParentProcessID", W.DWORD), ("pcPriClassBase", W.LONG),
                ("dwFlags", W.DWORD), ("szExeFile", W.WCHAR * 260)]


def log(msg):
    try:
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(time.strftime("%Y-%m-%d %H:%M:%S ") + msg + "\n")
    except OSError:
        pass


def pids(exe_name):
    snap = k32.CreateToolhelp32Snapshot(2, 0)
    out, e = [], PE32()
    e.dwSize = ctypes.sizeof(PE32)
    ok = k32.Process32FirstW(snap, ctypes.byref(e))
    while ok:
        if e.szExeFile.lower() == exe_name.lower():
            out.append(e.th32ProcessID)
        ok = k32.Process32NextW(snap, ctypes.byref(e))
    k32.CloseHandle(snap)
    return out


def image_path(h):
    buf, n = ctypes.create_unicode_buffer(1024), W.DWORD(1024)
    return os.path.normcase(buf.value) if k32.QueryFullProcessImageNameW(h, 0, buf, ctypes.byref(n)) else ""


def module_base(h, name):
    arr, need = (ctypes.c_void_p * 1024)(), W.DWORD()
    if not psapi.EnumProcessModulesEx(h, arr, ctypes.sizeof(arr), ctypes.byref(need), 3):
        return None
    buf = ctypes.create_unicode_buffer(260)
    for m in arr[:min(need.value // ctypes.sizeof(ctypes.c_void_p), 1024)]:
        if m and psapi.GetModuleBaseNameW(h, m, buf, 260) and buf.value.lower() == name:
            return m
    return None


def read(h, addr, n):
    buf, got = ctypes.create_string_buffer(n), ctypes.c_size_t()
    if not k32.ReadProcessMemory(h, ctypes.c_void_p(addr), buf, n, ctypes.byref(got)) or got.value != n:
        return None
    return buf.raw


def apply_table(h, base, table):
    """Process must be suspended. Returns 'patched', 'already' or an error text. Writes nothing unless every entry matches."""
    items = [(base + rva, bytes.fromhex(o), bytes.fromhex(n)) for rva, o, n in table]
    cur = [read(h, a, len(o)) for a, o, n in items]
    if all(c == o for c, (a, o, n) in zip(cur, items)):
        pass
    elif all(c == n for c, (a, o, n) in zip(cur, items)):
        return "already"
    else:
        bad = [hex(rva) for (rva, _, _), c, (a, o, n) in zip(table, cur, items) if c not in (o, n)]
        return "bytes differ at " + ", ".join(bad[:5]) + " (other CapCut version?): nothing written"
    done = []
    for a, o, n in items:
        old = W.DWORD()
        if not k32.VirtualProtectEx(h, ctypes.c_void_p(a), len(n), 0x40, ctypes.byref(old)):
            err = ctypes.get_last_error()
            for a2, o2, n2 in reversed(done):  # undo, so the process never runs half-patched
                k32.WriteProcessMemory(h, ctypes.c_void_p(a2), o2, len(o2), None)
            return f"VirtualProtectEx failed ({err}) at 0x{a - base:x}: undone"
        wrote = ctypes.c_size_t()
        ok = k32.WriteProcessMemory(h, ctypes.c_void_p(a), n, len(n), ctypes.byref(wrote))
        k32.VirtualProtectEx(h, ctypes.c_void_p(a), len(n), old.value, ctypes.byref(W.DWORD()))
        if not ok or wrote.value != len(n):
            for a2, o2, n2 in reversed(done):
                k32.WriteProcessMemory(h, ctypes.c_void_p(a2), o2, len(o2), None)
            return f"write failed at 0x{a - base:x}: undone"
        done.append((a, o, n))
    k32.FlushInstructionCache(h, None, 0)
    if any(read(h, a, len(n)) != n for a, o, n in items):
        return "verify after write failed"
    return "patched"


def watch_and_patch(exe_path, table, module=MODULE, timeout=90, known=()):
    """Wait for a new process of exe_path, then for its module, then patch it. Returns a result text."""
    exe_path = os.path.normcase(os.path.abspath(exe_path))
    name = os.path.basename(exe_path)
    seen = set(known)
    end = time.time() + timeout
    while time.time() < end:
        for pid in pids(name):
            if pid in seen:
                continue
            seen.add(pid)
            h = k32.OpenProcess(ACCESS, False, pid)
            if not h:
                continue
            if image_path(h) != exe_path:
                k32.CloseHandle(h)
                continue
            try:
                while time.time() < end:
                    base = module_base(h, module)
                    if base:
                        ntdll.NtSuspendProcess(h)
                        try:
                            res = apply_table(h, base, table)
                        finally:
                            ntdll.NtResumeProcess(h)
                        return f"pid {pid}: {res}"
                    if k32.WaitForSingleObject(h, 0) == 0:
                        log(f"pid {pid} exited before loading {module}; still watching")
                        break
                    time.sleep(0.001)
            finally:
                k32.CloseHandle(h)
        time.sleep(0.002)
    return f"timed out waiting for {name} / {module}"


def main():
    root = os.path.join(os.environ["LOCALAPPDATA"], "CapCut", "Apps")
    vers = sorted(d for d in glob.glob(os.path.join(root, "*", "CapCut.exe")))
    if not vers:
        log("CapCut not found")
        return 1
    target = vers[-1]
    ver = os.path.basename(os.path.dirname(target))
    table = TABLE if ver == "9.7.1.4203" else []
    running = [p for p in pids("CapCut.exe")]
    if running:
        log(f"CapCut already running (pids {running}); starting it without patching")
    if not table:
        log(f"version {ver} has no patch table: starting stock CapCut")
    starter = os.path.join(root, "CapCut.exe")
    subprocess.Popen([starter if os.path.exists(starter) else target], cwd=os.path.dirname(starter), close_fds=True,
                     creationflags=0x00000008 | 0x00000200)  # detached, new process group
    if table and not running:
        log(f"{ver}: " + watch_and_patch(target, table, known=running))
    return 0


if __name__ == "__main__":
    sys.exit(main())
