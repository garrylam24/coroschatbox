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

- `opencode.json` — registers the `coros` MCP server and agents (`coros_data`, `coros_coach`, `grill_me`)
- `.opencode/agents/*.md` — agent prompt files with context and instructions

### Available agents

| Agent | When to use |
|---|---|
| `@coros_data` | Simple data retrieval (mileage, sleep, HR, pace) |
| `@coros_coach` | Deep training diagnosis, HRV, race strategy |
| `@grill_me` | Accountability roasting — call me out for slacking |

### Restart required

After editing `opencode.json` or agent files, quit and restart opencode.
