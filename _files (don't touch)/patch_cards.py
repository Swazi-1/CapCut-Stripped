"""CapCut Lite: hide the home-screen AI rows and the sidebar AI section, and blank one heading (.po).

Patches in VECreator.dll. Each one is found by a byte signature or an exact C string (not a fixed offset),
so it also works after a CapCut update if the code is unchanged:
 1  creative card filter   CreativeCardCategoryViewModel::isCardFeatureEnabled: first 3 bytes -> xor eax,eax ; ret
 2  old AI section         getter of ccpc_homepage_creative_area.enable: -> false (section and heading gone)
 3  sidebar promo banner   QML key home_page_banner -> xome_page_banner (both copies)
 4  sidebar AI section     web-tab config keys homepage_web_tab_configs_new and homepage_web_tab_configs: h -> x
 5  home EditPilot card    getter of edit_pilot_card_config.enable: first 3 bytes -> xor eax,eax ; ret
 6  home tool row          key home_page_tools: h -> x (the server list is then not found)
 7  home tool fallback     HomepageToolCategoryModel::maybeApplyFallbackResources: first byte -> ret (no default tools)
Text: Resources\\po\\*.po, msgid homepage_ai_creative_suite_title is set to a single space (the heading).
(Patching the heading code in the DLL makes CapCut refuse to start, so the text is blanked instead.)

Known leftover: with patches 6 and 7 the home tool row is empty and shows the generic text
"loading failed, Click to try again" (msgid loading_unsuccessful_n, used by many lists). Not changed here.

usage: patch_cards.py check|apply|revert [dll]     (CapCut must be closed for apply/revert)
Exit codes: 0 ok, 2 patch 1 signature not found / not unique (nothing changed), 3 unexpected bytes.
Patches 2-7 are optional: a patch that is not found is skipped and the others still apply.
apply saves the untouched DLL once as CapCut\\_orig\\Apps\\<version>\\VECreator.dll.orig."""
import glob, mmap, os, re, shutil, struct, sys

# ---- patch 1 (card filter) and patch 2 (old AI section): 3-byte swap "mov [rsp+8],rbx" -> "xor eax,eax ; ret"
RX_ORIG3 = rb"\x48\x89\x5c"
ORIG3 = bytes([0x48, 0x89, 0x5C])
RX_NEW3 = rb"\x31\xc0\xc3"
NEW3 = bytes([0x31, 0xC0, 0xC3])
PROLOGUE = (rb"\x48\x89\x5c\x24\x08\x48\x89\x74\x24\x18\x57\x48\x81\xec\x80\x00\x00\x00"  # prologue
            rb"\x48\x8b\x05....\x48\x33\xc4\x48\x89\x44\x24\x70\x48\x8b\xda"               # stack cookie
            rb"\x48\xc7\x44\x24\x40\x09\x00\x00\x00\x48\x8d\x05....\x48\x89\x44\x24\x48")   # len 9 + "smart_ads"
SIG2 = (rb"\x48\x89\x5c\x24\x08\x57\x48\x83\xec\x60\x48\x8b\x05....\x48\x33\xc4\x48\x89\x44\x24\x58\x33\xdb\x89\x5c\x24\x30\xe8....\x84\xc0\x0f\x84...."
        rb"\x48\x89\x5c\x24\x38\x48\x89\x5c\x24\x48\x48\xc7\x44\x24\x50\x0f\x00\x00\x00\x88\x5c\x24\x38\x8d\x4b\x30\xe8...."
        rb"\x48\xc7\x44\x24\x48\x22\x00\x00\x00\x48\xc7\x44\x24\x50\x2f\x00\x00\x00")

# ---- patch 3 (sidebar promo banner): QML string "home_page_banner" as UTF-16 with a 4-byte length prefix
SLOT_OLD = b"\x10\x00\x00\x00" + "home_page_banner".encode("utf-16-le")
SLOT_NEW = b"\x10\x00\x00\x00" + "xome_page_banner".encode("utf-16-le")

# ---- patch 4 (sidebar AI section): web-tab config keys, exact C strings (NUL-terminated), first letter h -> x
SIDEBAR_KEYS = [b"homepage_web_tab_configs_new\x00", b"homepage_web_tab_configs\x00"]

# ---- patch 5 (home EditPilot card): getter of edit_pilot_card_config.enable (default true): first 3 bytes -> xor eax,eax ; ret
EP_KEY = b"edit_pilot_card_config.enable"
ORIG5 = bytes([0x48, 0x83, 0xEC])

# ---- patch 6 (home tool row): key home_page_tools, first letter h -> x
TOOLROW_KEYS = [b"home_page_tools\x00"]

# ---- patch 7 (home tool fallback): HomepageToolCategoryModel::maybeApplyFallbackResources, first byte 0x40 -> ret (0xC3)
RX_ORIG7 = rb"\x40"
ORIG7 = b"\x40"
RX_NEW7 = rb"\xc3"
NEW7 = b"\xc3"
SIG7 = (rb"\x40\x53\x48\x83\xec\x30\x80\xb9\x90\x00\x00\x00\x00\x48\x8b\xd9\x75\x7e\x83\x79\x28\x01\x74\x78\xe8....\x48\x83\x78\x10\x00\x75\x6c"
        rb"\x48\x89\x7c\x24\x40\xba\x5c\x00\x00\x00\x48\x8d\x3d....\x48\x8b\xcf\xe8....\x48\x85\xc0\x74\x11\xba\x5c\x00\x00\x00"
        rb"\x48\x8b\xcf\xe8....\x48\x8d\x78\x01\x48\x8b\x15....\x48\x8d\x05....\x48\x89\x44\x24\x28\x4c\x8d\x05....\x4c\x8b\xcf"
        rb"\xc7\x44\x24\x20\x22\x00\x00\x00")  # the "0x22" is this function's log line; the creative card copy has 0x1e

# ---- heading text in the .po files
PO_RE = re.compile(rb'(msgid "homepage_ai_creative_suite_title"\r?\nmsgstr )"([^"\r\n]*)"')
PO_BLANK = b'" "'


def app_dir():
    base = os.path.join(os.environ["LOCALAPPDATA"], "CapCut", "Apps")
    vers = [d for d in glob.glob(os.path.join(base, "*")) if os.path.isdir(d) and re.fullmatch(r"\d+(\.\d+)+", os.path.basename(d))]
    vers.sort(key=lambda d: [int(x) for x in os.path.basename(d).split(".")])
    return vers[-1]


def backup_path(appdir):
    return os.path.normpath(os.path.join(os.path.dirname(appdir), "..", "_orig", "Apps", os.path.basename(appdir), "VECreator.dll.orig"))


def scan(path, rx=None, literal=None):
    """Offsets of a regex (rx) or of an exact byte string (literal) in the file. Read-only."""
    with open(path, "rb") as f, mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as m:
        if literal is not None:
            out, i = [], m.find(literal)
            while i >= 0:
                out.append(i)
                i = m.find(literal, i + 1)
            return out
        return [x.start() for x in re.finditer(rx, m, re.S)]


def put(path, off, expect, new):
    """Write `new` at `off` after checking that the file still has `expect` there."""
    with open(path, "r+b") as f:
        f.seek(off)
        old = f.read(len(expect))
        if old != expect:
            raise ValueError(f"unexpected bytes at 0x{off:x}: {old.hex()} (expected {expect.hex()})")
        f.seek(off)
        f.write(new)


def sig_patch(path, name, sig, rx_orig, orig, rx_new, new, mode, required=False):
    """Swap the first bytes of a signature (orig -> new). rx_orig/rx_new are the regex forms of those bytes."""
    hits = scan(path, sig)
    done = scan(path, rx_new + sig[len(rx_orig):])
    if mode == "check":
        print(f"  {name}: unpatched {len(hits)}, patched {len(done)}")
        return 0
    if mode == "apply":
        if done and not hits:
            print(f"  {name}: already applied")
            return 0
        if len(hits) != 1:
            print(f"  {name}: signature not found or not unique ({len(hits)} hits): skipped")
            return 2 if required else 0
        try:
            put(path, hits[0], orig, new)
        except ValueError as e:
            print(f"  {name}: {e}")
            return 3
        print(f"PATCHED {name} at file offset 0x{hits[0]:x}: {orig.hex()} -> {new.hex()}")
        return 0
    if mode == "revert":
        if len(done) == 1 and not hits:
            put(path, done[0], new, orig)
            print(f"REVERTED {name} at file offset 0x{done[0]:x}")
        elif len(hits) == 1:
            print(f"  {name}: already original")
        else:
            print(f"  {name}: not patched (or not unique): nothing changed")
        return 0
    return 1


def literal_patch(path, name, literals, mode):
    """Rename the first letter (h -> x) of each exact C string. A string is changed only if it occurs exactly once."""
    for lit in literals:
        label = lit[:-1].decode()
        old_first, new_first = lit[:1], b"x"
        renamed = new_first + lit[1:]
        hits = scan(path, literal=lit)
        done = scan(path, literal=renamed)
        if mode == "check":
            print(f"  {name} {label}: original {len(hits)}, renamed {len(done)}")
        elif mode == "apply":
            if done and not hits:
                print(f"  {name} {label}: already renamed")
            elif len(hits) != 1 or done:
                print(f"  {name} {label}: not found or not unique ({len(hits)} hits): skipped")
            else:
                try:
                    put(path, hits[0], old_first, new_first)
                    print(f"PATCHED {name} {label} at file offset 0x{hits[0]:x}: h -> x")
                except ValueError as e:
                    print(f"  {name} {label}: {e}")
        elif mode == "revert":
            if len(done) == 1 and not hits:
                put(path, done[0], new_first, old_first)
                print(f"REVERTED {name} {label} at file offset 0x{done[0]:x}")
            elif len(hits) == 1:
                print(f"  {name} {label}: already original")
            else:
                print(f"  {name} {label}: not renamed (or not unique): nothing changed")


def slot_patch(path, mode):
    """Patch 3: the QML banner key is stored as UTF-16 with a length prefix; change its first letter in each copy (1-4 copies)."""
    a = scan(path, literal=SLOT_OLD)
    b = scan(path, literal=SLOT_NEW)
    if mode == "check":
        print(f"  patch 3 (sidebar promo banner): original {len(a)}, renamed {len(b)}")
    elif mode == "apply":
        if 1 <= len(a) <= 4:
            for o in a:
                put(path, o + 4, b"h", b"x")
            print(f"PATCHED 3 (sidebar promo banner) at file offsets {[hex(o + 4) for o in a]}: h -> x")
        elif b and not a:
            print("  patch 3 (sidebar promo banner): already applied")
        else:
            print("  patch 3 (sidebar promo banner): key not found, skipped")
    elif mode == "revert":
        for o in b:
            put(path, o + 4, b"x", b"h")
        if b:
            print(f"REVERTED 3 (sidebar promo banner) at file offsets {[hex(o + 4) for o in b]}")


# QML string table of the tool panel: "WordWrap" entry, then "LoadFailed" (the status the 'loading failed' text waits for).
# Renaming L -> X makes the status lookup return nothing, so the text never shows.
_CTX = b"\x08\x00\x00\x00" + "WordWrap".encode("utf-16-le") + b"\x00\x00\x00\x00\x0a\x00\x00\x00"
PANEL_OLD = _CTX + "LoadFailed".encode("utf-16-le")
PANEL_NEW = _CTX + "XoadFailed".encode("utf-16-le")
PANEL_OFF = len(_CTX)


def panel_patch(path, mode):
    """Patch 8: hide the 'loading failed' text of the home tool row (QML status name, one letter, exactly one copy)."""
    name = "patch 8 (home tool-row text)"
    a = scan(path, literal=PANEL_OLD)
    b = scan(path, literal=PANEL_NEW)
    if mode == "check":
        print(f"  {name}: original {len(a)}, renamed {len(b)}")
    elif mode == "apply":
        if len(a) == 1 and not b:
            put(path, a[0] + PANEL_OFF, b"L", b"X")
            print(f"PATCHED {name} at file offset 0x{a[0] + PANEL_OFF:x}: L -> X")
        elif b and not a:
            print(f"  {name}: already applied")
        else:
            print(f"  {name}: key not found or not unique ({len(a)} hits), skipped")
    elif mode == "revert":
        if len(b) == 1 and not a:
            put(path, b[0] + PANEL_OFF, b"X", b"L")
            print(f"REVERTED {name} at file offset 0x{b[0] + PANEL_OFF:x}")
        elif a:
            print(f"  {name}: already original")


# Compiled QML (Qt 6.2 bytecode) of newTopToolPanel's 'visible' binding:
#   visible: listModel.count > 0 && !startProjectHover.visible && !homepageRefactorEnable
# The first two bytes become LoadFalse (0a) + Ret (02), so the row is hidden and the Column moves Projects up.
VIS_TAIL = bytes.fromhex("020000 3d68020000 3d69020000 1807 06 6407 500b")
VIS_OLD = bytes.fromhex("2f67") + VIS_TAIL
VIS_NEW = bytes.fromhex("0a02") + VIS_TAIL
# old patch 9 (function-name rename) had no effect; it is undone on apply/revert
H_OLD = b"\x1b\x00\x00\x00" + "updateNewTopToolPanelHeight".encode("utf-16-le")
H_NEW = b"\x1b\x00\x00\x00" + "xpdateNewTopToolPanelHeight".encode("utf-16-le")


def height_patch(path, mode):
    """Patch 9: make the empty tool row invisible (its 'visible' binding returns false), so Projects moves up."""
    name = "patch 9 (home tool-row hidden)"
    old_ren = scan(path, literal=H_NEW)
    if mode in ("apply", "revert") and len(old_ren) == 1:
        put(path, old_ren[0] + 4, b"x", b"u")
        print(f"  {name}: undid old function-name rename")
    a, b = scan(path, literal=VIS_OLD), scan(path, literal=VIS_NEW)
    if mode == "check":
        print(f"  {name}: original {len(a)}, patched {len(b)}")
    elif mode == "apply":
        if len(a) == 1 and not b:
            put(path, a[0], VIS_OLD[:2], VIS_NEW[:2])
            print(f"PATCHED {name} at file offset 0x{a[0]:x}: 2f 67 -> 0a 02")
        elif b and not a:
            print(f"  {name}: already applied")
        else:
            print(f"  {name}: not found or not unique ({len(a)} hits), skipped")
    elif mode == "revert" and len(b) == 1 and not a:
        put(path, b[0], VIS_NEW[:2], VIS_OLD[:2])
        print(f"REVERTED {name}")


# Patch 10: the home AI card row (QML root Item, Qt 6.2 cache) has the constant binding 'height: 136'.
# That binding record becomes 'visible: false' (name index 0x10 'height' -> 0x93 'visible', type Number 2 -> Boolean 1,
# value 0 = false). The row is hidden, has no height, and Projects moves up. Context = previous binding record.
ROW_PREV = bytes.fromhex("110000000800020001000000000000001200c00112009002")  # cardSpacing: 1
ROW_TAIL = bytes.fromhex("0000000000000000110050001100d000")  # value 0, rest of the height record


# v2: 'visible: false' stopped the row's server request, and that broke every online panel.
# Now the row stays visible (so it still loads) but is shrunk, clipped and disabled:
#   cardSpacing: 1  -> enabled: false   (name 0x11 -> 0xad, flags 0x0008 -> 0, value 1 -> 0)
#   height: 136     -> clip: true       (name 0x10 -> 0x83, type Number -> Boolean, value 0 -> 1)
# With no height binding the row is 0 px tall; clip hides the cards, enabled: false blocks mouse and hover.
ROW_V1 = ROW_PREV + b"\x93\x00\x00\x00\x00\x00\x01\x00" + ROW_TAIL  # old patch 10 (visible: false)
ROW_NEW = (bytes.fromhex("ad000000000001000000000000000000") + ROW_PREV[16:]
           + b"\x83\x00\x00\x00\x00\x00\x01\x00" + b"\x01\x00\x00\x00" + ROW_TAIL[4:])


def row_patch(path, mode):
    name = "patch 10 (home AI card row hidden)"
    old = ROW_PREV + b"\x10\x00\x00\x00\x00\x00\x02\x00" + ROW_TAIL
    v1 = scan(path, literal=ROW_V1)
    if mode in ("apply", "revert") and len(v1) == 1:
        put(path, v1[0], ROW_V1, old)
        print(f"  {name}: undid old visible:false version")
    new = ROW_NEW
    a, b = scan(path, literal=old), scan(path, literal=new)
    p = 0
    if mode == "check":
        print(f"  {name}: original {len(a)}, patched {len(b)}")
    elif mode == "apply":
        if len(a) == 1 and not b:
            put(path, a[0], old, new)
            print(f"PATCHED {name} at file offset 0x{a[0]:x}: cardSpacing->enabled:false, height:136->clip:true")
        elif b and not a:
            print(f"  {name}: already applied")
        else:
            print(f"  {name}: not found or not unique ({len(a)} hits), skipped")
    elif mode == "revert" and len(b) == 1 and not a:
        put(path, b[0], new, old)
        print(f"REVERTED {name}")


# Patch 11: the home Loader that holds the card row has 'height: active ? 136 : 0' (compiled QML).
# LoadInt 136 -> LoadInt 0, so the empty slot under Create project takes no space.
SLOT136_OLD = bytes.fromhex("2f7a060000500711880000004c0106180602")
SLOT136_NEW = bytes.fromhex("2f7a060000500711000000004c0106180602")


def slot136_patch(path, mode):
    name = "patch 11 (home card-row slot height)"
    a, b = scan(path, literal=SLOT136_OLD), scan(path, literal=SLOT136_NEW)
    if mode == "check":
        print(f"  {name}: original {len(a)}, patched {len(b)}")
    elif mode == "apply":
        if len(a) == 1 and not b:
            put(path, a[0] + 8, b"\x88", b"\x00")
            print(f"PATCHED {name} at file offset 0x{a[0] + 8:x}: 136 -> 0")
        elif b and not a:
            print(f"  {name}: already applied")
        else:
            print(f"  {name}: not found or not unique ({len(a)} hits), skipped")
    elif mode == "revert" and len(b) == 1 and not a:
        put(path, b[0] + 8, b"\x00", b"\x88")
        print(f"REVERTED {name}")


# Patch 12: editor EditPilot floating button. agent::AgentView::ensureFloatingViewShownAndRaised
# (identified by its own log string) starts with 'mov [rsp+8],rbx'; first byte 48 -> C3 (ret), so the
# floating EditPilot window is never shown.
FLOAT_OLD = bytes.fromhex("48895c24084889742410574883ec60488bd9e809fa32fd84c00f84db00000080bba600000000751fff151a870a04")
FLOAT_NEW = b"\xc3" + FLOAT_OLD[1:]


def float_patch(path, mode):
    name = "patch 12 (editor EditPilot button)"
    a, b = scan(path, literal=FLOAT_OLD), scan(path, literal=FLOAT_NEW)
    if mode == "check":
        print(f"  {name}: original {len(a)}, patched {len(b)}")
    elif mode == "apply":
        if len(a) == 1 and not b:
            put(path, a[0], b"\x48", b"\xc3")
            print(f"PATCHED {name} at file offset 0x{a[0]:x}: 48 -> c3")
        elif b and not a:
            print(f"  {name}: already applied")
        else:
            print(f"  {name}: not found or not unique ({len(a)} hits), skipped")
    elif mode == "revert" and len(b) == 1 and not a:
        put(path, b[0], b"\xc3", b"\x48")
        print(f"REVERTED {name}")


def pe_sections(m):
    """(name, virtual address, raw size, raw pointer, characteristics) of each PE section."""
    e = struct.unpack_from("<I", m, 0x3C)[0]
    nsec = struct.unpack_from("<H", m, e + 6)[0]
    osz = struct.unpack_from("<H", m, e + 20)[0]
    secs = []
    for i in range(nsec):
        o = e + 24 + osz + 40 * i
        name = m[o:o + 8].rstrip(b"\0").decode("ascii", "replace")
        vsize, va, rawsize, rawptr = struct.unpack_from("<IIII", m, o + 8)
        chars = struct.unpack_from("<I", m, o + 36)[0]
        secs.append((name, va, rawsize, rawptr, chars))
    return secs


def getter_patch(path, name, mode):
    """Patch 5: find the getter that reads the key edit_pilot_card_config.enable.
    The key string must occur once; the one rip-relative reference to it in .text is inside the getter;
    the getter starts at the closest 'sub rsp,0x68 ; mov rax,[rip+x]' (or the patched 'xor eax,eax ; ret' form) before it."""
    with open(path, "rb") as f, mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as m:
        lits, i = [], m.find(EP_KEY)
        while i >= 0:
            lits.append(i)
            i = m.find(EP_KEY, i + 1)
        if len(lits) != 1:
            print(f"  {name}: key not found or not unique ({len(lits)} hits): skipped")
            return 2 if mode == "apply" else 0
        secs = pe_sections(m)
        lsec = next(s for s in secs if s[3] <= lits[0] < s[3] + s[2])
        lrva = lsec[1] + (lits[0] - lsec[3])
        refs = []
        for sname, va, rawsize, rawptr, chars in secs:
            if sname != ".text":
                continue
            data = m[rawptr:rawptr + rawsize]
            for mt in re.finditer(rb"[\x05\x0d\x15\x1d\x25\x2d\x35\x3d]", data):
                p = mt.end()  # the disp32 starts right after the ModRM byte
                if p + 4 <= len(data) and va + p + 4 + struct.unpack_from("<i", data, p)[0] == lrva:
                    refs.append(rawptr + p)
        if len(refs) != 1:
            print(f"  {name}: {len(refs)} code references to the key (expected 1): skipped")
            return 2 if mode == "apply" else 0
        ref = refs[0]
        lo = max(0, ref - 0x400)
        starts = [lo + mt.start() for mt in re.finditer(rb"(\x48\x83\xec|\x31\xc0\xc3)\x68\x48\x8b\x05", m[lo:ref])]
        if not starts or b"\xcc\xcc" in m[starts[-1]:ref]:
            print(f"  {name}: getter start not found: skipped")
            return 2 if mode == "apply" else 0
        start = starts[-1]
        prefix = bytes(m[start:start + 3])
    state = "orig" if prefix == ORIG5 else "new" if prefix == NEW3 else None
    if state is None:
        print(f"  {name}: unexpected bytes {prefix.hex()} at 0x{start:x}: skipped")
        return 3 if mode == "apply" else 0
    if mode == "check":
        print(f"  {name}: getter at file 0x{start:x}, {'patched' if state == 'new' else 'unpatched'}")
        return 0
    if mode == "apply":
        if state == "new":
            print(f"  {name}: already applied")
            return 0
        put(path, start, ORIG5, NEW3)
        print(f"PATCHED {name} at file offset 0x{start:x}: {ORIG5.hex()} -> {NEW3.hex()}")
        return 0
    if mode == "revert":
        if state == "new":
            put(path, start, NEW3, ORIG5)
            print(f"REVERTED {name} at file offset 0x{start:x}")
        else:
            print(f"  {name}: already original")
        return 0
    return 1


def po_files(appdir):
    return glob.glob(os.path.join(appdir, "Resources", "po", "*.po"))


def po_apply(appdir):
    n = 0
    for p in po_files(appdir):
        data = open(p, "rb").read()
        m = PO_RE.search(data)
        if not m or m.group(2) == b" ":
            continue
        orig = os.path.normpath(os.path.join(os.path.dirname(appdir), "..", "_orig", "Apps", os.path.basename(appdir), "po-orig-" + os.path.basename(p)))
        os.makedirs(os.path.dirname(orig), exist_ok=True)
        if not os.path.exists(orig):
            shutil.copy2(p, orig)
        open(p, "wb").write(PO_RE.sub(lambda mm: mm.group(1) + PO_BLANK, data, count=1))
        n += 1
    print(f"  heading text blanked in {n} .po file(s)")


def po_revert(appdir):
    removed = os.path.normpath(os.path.join(os.path.dirname(appdir), "..", "_orig", "Apps", os.path.basename(appdir)))
    n = 0
    for p in po_files(appdir):
        orig = os.path.join(removed, "po-orig-" + os.path.basename(p))
        if os.path.exists(orig):
            shutil.copy2(orig, p)
            n += 1
    print(f"  heading text restored in {n} .po file(s)")


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "check"
    dll = sys.argv[2] if len(sys.argv) > 2 else os.path.join(app_dir(), "VECreator.dll")
    appdir = os.path.dirname(dll)
    if not os.path.exists(dll):
        print("VECreator.dll not found: nothing changed")
        return 2
    print(f"dll: {dll}")

    if mode == "check":
        hits1 = scan(dll, PROLOGUE)
        done1 = scan(dll, RX_NEW3 + PROLOGUE[len(RX_ORIG3):])
        sig_patch(dll, "patch 1 (card filter)", PROLOGUE, RX_ORIG3, ORIG3, RX_NEW3, NEW3, "check")
        sig_patch(dll, "patch 2 (old AI section)", SIG2, RX_ORIG3, ORIG3, RX_NEW3, NEW3, "check")
        slot_patch(dll, "check")
        literal_patch(dll, "patch 4 (sidebar AI section)", SIDEBAR_KEYS, "check")
        getter_patch(dll, "patch 5 (home EditPilot card)", "check")
        literal_patch(dll, "patch 6 (home tool row)", TOOLROW_KEYS, "check")
        sig_patch(dll, "patch 7 (home tool fallback)", SIG7, RX_ORIG7, ORIG7, RX_NEW7, NEW7, "check")
        panel_patch(dll, "check")
        height_patch(dll, "check")
        row_patch(dll, "check")
        slot136_patch(dll, "check")
        float_patch(dll, "check")
        return 0 if len(hits1) + len(done1) == 1 else 2

    if mode == "apply":
        hits1 = scan(dll, PROLOGUE)
        if len(hits1) == 1 and not os.path.exists(backup_path(appdir)):
            os.makedirs(os.path.dirname(backup_path(appdir)), exist_ok=True)
            shutil.copy2(dll, backup_path(appdir))
            print(f"  original saved to {backup_path(appdir)}")
        rc = sig_patch(dll, "patch 1 (card filter)", PROLOGUE, RX_ORIG3, ORIG3, RX_NEW3, NEW3, "apply", required=True)
        if rc:
            print("patch 1 signature not found or not unique: nothing changed")
            return rc
        for step in (
            lambda: sig_patch(dll, "patch 2 (old AI section)", SIG2, RX_ORIG3, ORIG3, RX_NEW3, NEW3, "apply"),
            lambda: slot_patch(dll, "apply"),
            lambda: literal_patch(dll, "patch 4 (sidebar AI section)", SIDEBAR_KEYS, "apply"),
            lambda: getter_patch(dll, "patch 5 (home EditPilot card)", "apply"),
            # patch 6 retired: renaming the server slot key broke every online panel ("No internet connection").
            # Patch 9 hides the row instead. Apply now undoes patch 6 if an older run left it in place.
            lambda: literal_patch(dll, "patch 6 (retired, undo)", TOOLROW_KEYS, "revert"),
            lambda: sig_patch(dll, "patch 7 (home tool fallback)", SIG7, RX_ORIG7, ORIG7, RX_NEW7, NEW7, "apply"),
            lambda: panel_patch(dll, "apply"),
            lambda: height_patch(dll, "apply"),
            lambda: row_patch(dll, "apply"),
            lambda: slot136_patch(dll, "apply"),
            lambda: float_patch(dll, "apply"),
        ):
            step()
        po_apply(appdir)
        return 0

    if mode in ("revert", "memory"):
        # memory: the DLL stays the signed original on disk (a changed file breaks its signature and the online
        # panels); capcut_lite.pyw writes the same bytes into memory at start. Only the .po heading is changed on disk.
        float_patch(dll, "revert")
        slot136_patch(dll, "revert")
        row_patch(dll, "revert")
        height_patch(dll, "revert")
        panel_patch(dll, "revert")
        sig_patch(dll, "patch 7 (home tool fallback)", SIG7, RX_ORIG7, ORIG7, RX_NEW7, NEW7, "revert")
        literal_patch(dll, "patch 6 (home tool row)", TOOLROW_KEYS, "revert")
        getter_patch(dll, "patch 5 (home EditPilot card)", "revert")
        literal_patch(dll, "patch 4 (sidebar AI section)", SIDEBAR_KEYS, "revert")
        slot_patch(dll, "revert")
        sig_patch(dll, "patch 2 (old AI section)", SIG2, RX_ORIG3, ORIG3, RX_NEW3, NEW3, "revert")
        sig_patch(dll, "patch 1 (card filter)", PROLOGUE, RX_ORIG3, ORIG3, RX_NEW3, NEW3, "revert")
        if mode == "memory":
            po_apply(appdir)
        else:
            po_revert(appdir)
        return 0

    return 1


if __name__ == "__main__":
    sys.exit(main())
