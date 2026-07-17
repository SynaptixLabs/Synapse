# Epic P — GitHub coding agents × the brain (MCP) (~45V) · GATED: founder go + founder account steps

> Up: [`../index.md`](../index.md) · Founder ask 2026-07-17 (repo Agents tab + "seems we can
> use MCP for that"). The loop: agents fixing Synapse issues consult Synapse's OWN brain
> through the MCP server shipped in sprint 04.

## Design

- **Claude GitHub Action** (`@claude` on issues/PRs): workflow with `mcp_config` wiring
  `synapse serve` over the SELF-ingested brain (built at session start — deterministic,
  keyless, ~seconds). The agent asks the brain ("what does the PRD say about X?") instead
  of grepping.
- **Copilot coding agent**: repo MCP configuration pointing at the same server; assign an
  issue → agent PRs → branch protection (PR + 3 CI checks + review) already gates it.
- `AGENTS.md` + `.claude/` house rules ride into every agent session for free (scaffold
  synergy — the repo already "speaks agent").
- Delegation policy in CONTRIBUTING: `agent-ready` label = well-scoped + test-covered
  (#1, #2, #3); design-first issues (#13, #16) stay human/JANUS-led; agent PRs get the
  same GBU treatment as any contributor.

## Founder gates (account-level, not code)
- [ ] Install the Claude GitHub app OR add `ANTHROPIC_API_KEY` repo secret (your billing)
- [ ] Enable Copilot coding agent (plan/org setting) if desired

## Tasks
- [ ] P1 `claude.yml` workflow + MCP config (self-brain at session start)
- [ ] P2 `agent-ready` labels on #1/#2/#3 + CONTRIBUTING delegation policy
- [ ] P3 Copilot MCP config JSON + docs
- [ ] P4 pilot: delegate issue #3, review the PR through the normal gate
