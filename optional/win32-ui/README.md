# Optional: hybrid Win32 debugger — GUI and remote at the same time

This patch does two things, and the first is the significant one.

**1. Hybrid debugging.** It embeds the remote TCP server *inside* MAME's native Windows
debugger, so the GUI window and the remote connection run **simultaneously**. You can
freeze the machine yourself in the debugger window, step a frame, then have an LLM read
memory from that same stopped machine. Without this patch the two are mutually exclusive,
because `-debugger remote` replaces `-debugger windows`.

Launch it by selecting the **windows** debugger and giving it a port:

```
mame <game> -debug -debugger windows -debugger_port 12345
```

> ⚠️ **`-debugger_port` is effectively required here.** MAME's default is **23946**
> (gdbstub's port), so omitting it opens the listener somewhere your client is probably not
> looking — which reads exactly like "the GUI and remote debugger cannot coexist."

**2. Text selection and copy** in the debugger views — selection, select-all, Ctrl+C — plus
console-history wiring.

**The MCP server does not require this patch.** `-debugger remote` works on its own; you
simply don't get the GUI alongside it.

## Why this is a patch and not files

Unlike the core module — which is two *new* files — this **modifies existing MAME
sources**:

| File | Change |
|------|--------|
| `src/osd/modules/debugger/debugwin.cpp`          | ~64 lines: embedded TCP server polled in the Win32 message loop, console-history wiring |
| `src/osd/modules/debugger/win/debugviewinfo.cpp` | ~362 lines: selection model, copy, key handling |
| `src/osd/modules/debugger/win/debugviewinfo.h`   | ~22 lines: selection state members |

Shipping whole files would overwrite your copies and pin them to one MAME release. As a
patch it fails loudly instead of silently downgrading your tree.

Because it touches stock files, **this is the part most likely to break on a new MAME
release.** It has already needed fixing once, when 0.289 moved `metrics()` onto the owning
window (`metrics()` -> `m_owner.metrics()` inside `debugview_info`).

## Apply

```
cd /path/to/mame
git apply /path/to/mame-llm-debugger/optional/win32-ui/win32-ui-0.289.patch
```

Check before applying, and reverse it if you want it gone:

```
git apply --check  .../win32-ui-0.289.patch
git apply --reverse .../win32-ui-0.289.patch
```

Without git, `patch -p1 < win32-ui-0.289.patch` works too.

The patch is generated against **MAME 0.289**. On a different release expect to apply it
with fuzz or by hand.
