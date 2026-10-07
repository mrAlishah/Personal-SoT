# Use Personal-SoT with ChatGPT Web

This guide connects an existing private GitHub-backed Personal-SoT to ChatGPT Web.

The key rule is:

```text
Personalization locator
≠ GitHub authorization
```

The locator tells ChatGPT which repository should be the canonical `sot`. GitHub authorization determines whether the current ChatGPT connection can actually read that private repository. You need both.

## Fast path

```text
private sot exists on GitHub
→ connect GitHub in ChatGPT
→ authorize the specific private repository
→ add the Personalization locator
→ @do:sot
→ @do:setup
```

## 1. Connect GitHub to ChatGPT

In ChatGPT Web, open:

```text
Settings
→ Plugins
→ GitHub
```

Connect the GitHub account that owns or can read your private Personal-SoT repository.

ChatGPT's GitHub availability can vary by plan, workspace, and product surface. Use a ChatGPT surface where the GitHub connection is actually available.

Official reference: https://help.openai.com/en/articles/11145903-connecting-github-to-chatgpt

## 2. Authorize the private repository

Opening a GitHub connection is not enough when repository access is restricted.

From the GitHub plugin/app settings in ChatGPT, open the available repository-management option. In GitHub, verify that the ChatGPT app is installed for the correct account or organization and that your private Personal-SoT repository is selected/approved.

For a newly created private repository, you may need to add it to the existing ChatGPT GitHub app installation.

If the repository belongs to an organization, organization policy may require an administrator to approve the app or repository.

Do not make the private repository public just to make ChatGPT see it.

## 3. Add the Personalization locator

Add this template to ChatGPT Personalization and replace only the repository placeholder:

```text
repo: <owner>/<private-repository>
ref: main
adapter: workspace/adapters/chatgpt_project_instructions.md

Before Personal-SoT-dependent work:

- Resolve the configured repo and ref using the repository access available in this chat.
- Read and follow the configured adapter.
- Resolve its declared entrypoint and follow referenced canonical contracts relative to the repository root.
- Treat this resolved repository as the canonical Personal-SoT source.
- Resolve capabilities from the tools actually available in the current chat; never infer write capability from read access.
- If required SoT files or capabilities are unavailable, report the limitation instead of guessing.
- `@do:sot` re-resolves and re-anchors the current chat according to the canonical runtime.
```

Keep the adapter as the exact raw repository path:

```text
workspace/adapters/chatgpt_project_instructions.md
```

Do **not** turn it into a Markdown link such as:

```text
workspace/adapters/chatgpt_project_[instructions.md](https://instructions.md/)
```

The Personalization text configures source selection. It does not grant GitHub permissions and it does not create write capability.

## 4. Re-anchor the chat

Run:

```text
@do:sot
```

A successful re-anchor should resolve the configured private repository and ref, read:

```text
workspace/adapters/chatgpt_project_instructions.md
```

then resolve its declared:

```text
workspace/adapters/runtime_entrypoint.md
```

and follow the referenced canonical contracts.

`@do:sot` is also the freshness boundary. If you just changed GitHub repository authorization, run it again rather than relying on an earlier 404/not-found result.

## 5. Finish setup

After `@do:sot` resolves successfully, run:

```text
@do:setup
```

ChatGPT must resolve capabilities from what the current chat actually exposes. Read access does not imply write access. If the current web connection cannot write or run local validation, it should still explain and preview safely, while stating that the write/validation was not performed there.

Use an authorized local agent such as Codex or another capable local client for repository writes and local validation when needed.

## Troubleshooting

### ChatGPT returns `404 Not Found`

If you can see the private repository in GitHub but ChatGPT gets 404, treat this first as a repository-authorization problem, not evidence that the repository does not exist.

Check:

1. ChatGPT is connected to the correct GitHub account.
2. The ChatGPT GitHub app is installed for the correct account/organization.
3. The specific private repository is selected in the app's repository access.
4. Any organization approval has been completed.
5. The current ChatGPT product surface exposes GitHub access.

Then run:

```text
@do:sot
```

again.

### Public repositories work but the private one does not

This strongly suggests the GitHub connection exists but the private repository is outside the app's authorized repository set. Update the GitHub app's repository access rather than changing the Personal-SoT locator.

### Personalization is present but ChatGPT still cannot read the repo

That is expected when provider authorization is missing. Personalization is configuration, not a credential.

Do not paste secrets, tokens, private keys, or broad private repository contents into the chat as a workaround.

### ChatGPT can read but cannot write

That is a capability boundary, not a broken SoT. Personal-SoT must not infer write permission from read access or from user confirmation. Use a capable authorized client for material writes.

## Safety

Keep the private repository private. Never place GitHub tokens, SSH private keys, recovery codes, one-time codes, passwords, or session cookies in Personalization or Personal-SoT.

Next: [Set up Personal-SoT](setup.md).
