#!/usr/bin/env python3
"""
Install (or remove) the MAME LLM debugger module into a MAME source tree.

    python install.py <path-to-mame-source>
    python install.py <path-to-mame-source> --check
    python install.py <path-to-mame-source> --uninstall

What it does — the entire coupling is 2 new files plus 3 lines:

  1. copies core/debugremote.cpp and core/debugremote_tcp.h into
     src/osd/modules/debugger/
  2. adds both to the build in scripts/src/osd/modules.lua          (+2 lines)
  3. registers the module in src/osd/modules/lib/osdobj_common.cpp  (+1 line)

Insertions are anchored to the existing gdbstub lines rather than applied as a
context diff, so upstream moving code around does not break installation. Running
it twice is safe: already-applied edits are detected and skipped.

Then rebuild MAME and run:  mame <game> -debug -debugger remote -debugger_port 12345
"""

import argparse
import shutil
import sys
from pathlib import Path

CORE_FILES = ("debugremote.cpp", "debugremote_tcp.h")

DEST_SUBDIR = Path("src/osd/modules/debugger")
MODULES_LUA = Path("scripts/src/osd/modules.lua")
OSDOBJ_CPP = Path("src/osd/modules/lib/osdobj_common.cpp")

# (file, anchor substring, lines to insert, marker that means "already installed")
LUA_ANCHOR = "debuggdbstub.cpp"
LUA_INSERT = (
    'MAME_DIR .. "src/osd/modules/debugger/debugremote.cpp",',
    'MAME_DIR .. "src/osd/modules/debugger/debugremote_tcp.h",',
)
# Matches BOTH inserted lines (debugremote.cpp and debugremote_tcp.h) so that
# --uninstall removes the pair, not just the first one.
LUA_MARKER = "debugremote"

REG_ANCHOR = "REGISTER_MODULE(m_mod_man, DEBUG_GDBSTUB);"
REG_INSERT = ("REGISTER_MODULE(m_mod_man, DEBUG_REMOTE);",)
REG_MARKER = "DEBUG_REMOTE"


def leading_ws(line: str) -> str:
    return line[: len(line) - len(line.lstrip())]


def patch_file(path: Path, anchor: str, insert: tuple, marker: str, remove: bool):
    """Insert (or remove) lines after the anchor line. Returns a status string."""
    if not path.exists():
        return f"MISSING   {path}  (not a MAME source tree?)"

    text = path.read_text(encoding="utf-8", errors="surrogateescape")
    newline = "\r\n" if "\r\n" in text else "\n"
    lines = text.splitlines()

    present = any(marker in ln for ln in lines)

    if remove:
        if not present:
            return f"skip      {path}  (nothing to remove)"
        kept = [ln for ln in lines if marker not in ln]
        path.write_text(newline.join(kept) + newline, encoding="utf-8",
                        errors="surrogateescape")
        return f"REMOVED   {path}  (-{len(lines) - len(kept)} lines)"

    if present:
        return f"ok        {path}  (already installed)"

    idx = next((i for i, ln in enumerate(lines) if anchor in ln), None)
    if idx is None:
        return (f"FAILED    {path}\n"
                f"          anchor not found: {anchor!r}\n"
                f"          MAME may have restructured this file - see docs/INTEGRATION.md "
                f"to apply the edit by hand.")

    ws = leading_ws(lines[idx])
    for offset, payload in enumerate(insert):
        lines.insert(idx + 1 + offset, ws + payload)

    path.write_text(newline.join(lines) + newline, encoding="utf-8",
                    errors="surrogateescape")
    return f"PATCHED   {path}  (+{len(insert)} lines after {anchor!r})"


def main():
    ap = argparse.ArgumentParser(description="Install the MAME LLM debugger module.")
    ap.add_argument("mame_root", help="path to the MAME source tree")
    ap.add_argument("--uninstall", action="store_true", help="remove the module")
    ap.add_argument("--check", action="store_true",
                    help="report status without changing anything")
    args = ap.parse_args()

    root = Path(args.mame_root).expanduser().resolve()
    here = Path(__file__).resolve().parent

    if not (root / MODULES_LUA).exists():
        sys.exit(f"error: {root} does not look like a MAME source tree "
                 f"(no {MODULES_LUA})")

    dest = root / DEST_SUBDIR
    print(f"MAME tree: {root}")
    print()

    if args.check:
        lua = (root / MODULES_LUA).read_text(encoding="utf-8", errors="surrogateescape")
        reg = (root / OSDOBJ_CPP).read_text(encoding="utf-8", errors="surrogateescape")
        for name in CORE_FILES:
            print(f"{'present' if (dest / name).exists() else 'ABSENT ':8}  {dest / name}")
        print(f"{'present' if LUA_MARKER in lua else 'ABSENT ':8}  build entry in {MODULES_LUA}")
        print(f"{'present' if REG_MARKER in reg else 'ABSENT ':8}  registration in {OSDOBJ_CPP}")
        return

    # 1. the two new source files
    for name in CORE_FILES:
        target = dest / name
        if args.uninstall:
            if target.exists():
                target.unlink()
                print(f"REMOVED   {target}")
            else:
                print(f"skip      {target}  (absent)")
        else:
            dest.mkdir(parents=True, exist_ok=True)
            shutil.copy2(here / "core" / name, target)
            print(f"COPIED    {target}")

    # 2 & 3. the three integration lines
    print(patch_file(root / MODULES_LUA, LUA_ANCHOR, LUA_INSERT, LUA_MARKER,
                     args.uninstall))
    print(patch_file(root / OSDOBJ_CPP, REG_ANCHOR, REG_INSERT, REG_MARKER,
                     args.uninstall))

    print()
    if args.uninstall:
        print("Uninstalled. Rebuild MAME to drop the module.")
    else:
        print("Installed. Now rebuild MAME, then launch with:")
        print("    mame <game> -debug -debugger remote -debugger_port 12345")


if __name__ == "__main__":
    main()
