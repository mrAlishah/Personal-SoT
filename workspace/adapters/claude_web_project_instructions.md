# Personal-SoT — Claude Web project

client_name: Claude Web
discovery_surface: workspace/adapters/claude_web_project_instructions.md
entrypoint: workspace/adapters/runtime_entrypoint.md

Treat the synced project repository root as the canonical SoT root. Before SoT-dependent work, read and follow the entrypoint and its referenced contracts using repository-relative paths.

Resolve capabilities from the tools actually available in this conversation. When repository write capability is unavailable, complete the canonical guided flow and preview but state that nothing was written and validation was not run here.

For Claude Web GitHub App/repository authorization and the copyable project locator, see `guides/user/github_ai_connections.md`. A project locator identifies the intended source but does not grant provider access.
