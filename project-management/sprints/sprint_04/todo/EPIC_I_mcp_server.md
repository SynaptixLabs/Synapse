# Epic I — MCP server (~35V) · issue #14

> Up: [`../index.md`](../index.md) · Your second brain becomes a tool your coding agent calls.

## Tasks

- [ ] I1 `synapse/serve.py`: MCP **stdio** server, stdlib-only (newline-delimited JSON-RPC 2.0):
      `initialize` / `notifications/initialized` / `ping` / `tools/list` / `tools/call`.
      Tools: `query_graph(question, budget?)`, `get_note(id)`, `get_neighbors(id)`,
      `shortest_path(a, b)` — all over Epic G's query module + GraphService (read-only,
      no model calls, no keys).
- [ ] I2 Entry: `python -m synapse.serve`; registration one-liner documented:
      `claude mcp add synapse -- <venv-python> -m synapse.serve`.
- [ ] I3 Tests: protocol unit tests (feed JSON-RPC lines → assert responses: init handshake,
      tools/list shape, tools/call happy + unknown-tool + malformed-JSON never crashes the loop).
- [ ] I4 README section "Use your brain from Claude Code" + registration + example Q&A.

**DoD:** registered in Claude Code, a vault-only question answered with note ids cited ·
protocol tests green · zero network/model calls in the server.
