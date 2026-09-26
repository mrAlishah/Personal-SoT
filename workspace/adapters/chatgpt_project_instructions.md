# Personal-SoT — ChatGPT project

client_name: ChatGPT
discovery_surface: workspace/adapters/chatgpt_project_instructions.md
entrypoint: workspace/adapters/runtime_entrypoint.md

Treat the connected/synced repository root as the canonical SoT root. Before SoT-dependent work, read and follow the entrypoint and its referenced contracts using repository-relative paths.

Resolve capabilities from the tools actually available in this chat. When repository write capability is unavailable, complete the canonical guided flow and preview but state that nothing was written and validation was not run here.
