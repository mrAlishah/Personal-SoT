# Personal-SoT — Claude Code

entrypoint: workspace/adapters/runtime_entrypoint.md

The repository root is the canonical SoT root. Before SoT-dependent work, read and follow the entrypoint and its referenced contracts using repository-relative paths.

Claude Code may perform canonical writes only when its actual filesystem/tool permissions allow them and the confirmed operation complies with the referenced safe-write contract. Otherwise it remains preview-only and reports the limitation.
