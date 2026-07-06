# AGENTS.md

## COROS Running Analysis Agent

This project has a custom opencode agent for analyzing COROS running data.

### Invocation

```
@coros <your question>
```

### What the agent can do

- Query live COROS data (runs, health, sleep, HRV, training load, recovery)
- Compute stats, trends, and comparisons on your running data
- Generate charts/visualizations with matplotlib

### Commands

```bash
python analysis.py    # Print full 2026 YTD analysis
```

### Agent config

- `opencode.json` — registers the `coros` MCP server and `coros` agent
- `.opencode/agents/coros.md` — agent prompt with context and instructions

### Restart required

After editing `opencode.json` or agent files, quit and restart opencode.
