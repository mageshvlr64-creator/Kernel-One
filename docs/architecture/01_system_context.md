# System Context

> The outermost view: what's inside the system boundary vs. outside it.

## Actors

| Actor | Interaction |
|---|---|
| Analyst / Restricted User / Administrator / Operator / SecurityOfficer / Auditor | Via the Workbench UI (`ui/`) or directly via `api/` |
| Local model runtimes (vLLM/Ollama/llama.cpp) | Inside the deployment boundary, treated as internal dependencies, not external actors |
| Object storage (MinIO), Database (PostgreSQL) | Internal dependencies |
| **No external actor** | Per REQ-NET-001, there is deliberately no cloud API, external identity provider, or third-party service in the V1 system context — this is the architectural expression of "sovereignty" |

## Boundary diagram

```
                    [ Deployment boundary — network mode enforced here ]
                    +------------------------------------------------+
  User (browser) -->|  UI  -->  API  -->  Agent Kernel / Tool Gateway |
                    |            |              |                    |
                    |         Database    Inference Gateway          |
                    |            |              |                    |
                    |      Object Storage   Local Models              |
                    +------------------------------------------------+
                          (nothing crosses this boundary outward
                           except in `restricted` mode's explicit allowlist)
```

## Why this matters architecturally

Every other architecture file in this directory zooms into one aspect of what's inside this
boundary — none of them introduce a new external actor, since REQ-NET-001/002 fix the system
context for all deployment modes.
