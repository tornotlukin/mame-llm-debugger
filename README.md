# MAME LLM Debugger

Drive MAME's debugger from an LLM. This adds a `remote` debugger module to MAME that
serves the debugger over TCP as line-delimited JSON, plus an MCP (Model Context Protocol)
server that exposes it as tools an LLM can call — set breakpoints, step, read and write
memory, disassemble, inspect registers, save/load states, screenshot.

It was built for reverse-engineering arcade ROMs: you ask the model *"find where the ghost
AI reads the maze"* and it can actually go and look, rather than guess.

## Why it is easy to adopt

The coupling to MAME is deliberately tiny: **two new files and three lines.**

| | |
|---|---|
| New files | `src/osd/modules/debugger/debugremote.cpp`, `debugremote_tcp.h` |
| Build entry | `scripts/src/osd/modules.lua` — **+2 lines** |
| Registration | `src/osd/modules/lib/osdobj_common.cpp` — **+1 line** |

Nothing else in the MAME tree is touched, which is what makes this survive upstream
releases. `install.py` applies all of it and can be re-run after every MAME upgrade.

## Requirements

- A MAME **source tree** you can build (this patches source; it cannot be added to a
  prebuilt `mame.exe`)
- Python 3.10+ with `pip install -r bridge/requirements.txt` (just the `mcp` package)
- An MCP-capable client (e.g. Claude Code)

## Install

```
python install.py /path/to/mame
```

Then rebuild MAME as you normally would. Verify the module is in your binary:

```
mame -showusage | grep debugger_port
```

Other modes:

```
python install.py /path/to/mame --check       report what is and isn't installed
python install.py /path/to/mame --uninstall   remove it and restore stock files
```

Installation is idempotent — running it twice is harmless. The edits are anchored to
MAME's existing `gdbstub` lines rather than applied as a context diff, so they keep working
when upstream shifts surrounding code.

## Use

**1. Start MAME with the remote debugger:**

```
mame <game> -debug -debugger remote -debugger_port 12345
```

> ⚠️ **Always pass `-debugger_port` explicitly.** MAME's default is **23946** (it is
> gdbstub's port), so if you omit it the listener opens there and your client's connection
> to 12345 is refused — which looks like the module isn't working when it is.

`launch/start_debugger.bat` is a Windows convenience wrapper — edit the variables at the top.

**2. Point your MCP client at the bridge.** Copy `.mcp.json.example` to `.mcp.json` in your
project and set the path:

```json
{
  "mcpServers": {
    "mame-debugger": {
      "type": "stdio",
      "command": "python",
      "args": ["/absolute/path/to/mame-llm-debugger/bridge/mcp_server.py"],
      "env": { "MAME_DEBUG_HOST": "localhost", "MAME_DEBUG_PORT": "12345" }
    }
  }
}
```

The bridge resolves its own imports from its file location, so it can live anywhere — it
does not need to sit inside your MAME tree.

**3. Check the connection** without an LLM in the loop:

```
python bridge/test_connection.py
```

The bridge connects to MAME lazily on the first tool call and reconnects automatically, so
the order you start things in does not matter.

## Tested MAME versions

| MAME | Status |
|------|--------|
| 0.289 | tested |
| 0.288 | tested |
| 0.286 | tested |

`debugremote.cpp` calls MAME internals (`debugger_console`, `debug_disasm_buffer`,
`device_state_entry`) that do occasionally change between releases. If a new release fails
to build, that is where to look — and please open an issue.

## Optional: hybrid mode — GUI and remote together

`optional/win32-ui/` embeds the TCP server **inside** MAME's native Windows debugger, so the
debugger window and the remote connection work at the same time:

```
mame <game> -debug -debugger windows -debugger_port 12345
```

You freeze the machine in the GUI on the exact frame you want; the LLM reads that same
stopped machine over the remote connection. Without it, `-debugger remote` replaces
`-debugger windows` and you get one or the other. It also adds text selection and copy to
the debugger views.

It ships as a patch because it *modifies existing MAME files* rather than adding new ones —
which also makes it the part most likely to conflict on a new release. **The MCP server does
not need it.** See `optional/win32-ui/README.md`.

## Layout

```
core/               the two files copied into MAME's debugger module directory
install.py          idempotent installer / uninstaller
bridge/             the MCP server (Python) — runs from anywhere
docs/
  INTEGRATION.md    exact manifest of every MAME touch-point, for manual install
  llm-debugger-reference.md   MAME debugger command syntax, written for an LLM
launch/             Windows convenience launcher
optional/win32-ui/  the optional UI patch
.mcp.json.example   MCP client configuration template
```

## Notes

MAME's debugger uses **hex by default** and has its own command syntax — it is not GDB.
`docs/llm-debugger-reference.md` exists so the model gets that right; point your client at
it if the model starts emitting GDB commands.

## License

BSD-3-Clause, matching MAME. See `LICENSE`.
