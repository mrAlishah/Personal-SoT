# Connect ChatGPT, Codex, and Claude to a private GitHub repository

Use this guide after your private Personal-SoT repository exists on GitHub.

The key model is:

```text
GitHub account access
→ GitHub App installation/authorization
→ repository selection
→ AI client connection
→ Personal-SoT source locator
```

These are separate layers. Naming a repository in Personalization or project instructions does **not** grant access to it.

## Before you start

You need:

- a GitHub account that can read the private Personal-SoT repository;
- permission to install/authorize GitHub Apps for that account or organization, or an administrator who can approve the request;
- the private repository already created and populated;
- the AI client surface you intend to use.

For organization-owned repositories, GitHub organization policy, SSO, or administrator approval can add an extra authorization step.

## ChatGPT and Codex

### Recommended connection path

In ChatGPT, open:

```text
Settings
→ Plugins
→ GitHub
```

Depending on the account/workspace rollout, the interface may show a GitHub plugin/app connection. Install/connect it, sign in to the intended GitHub account, and continue to GitHub when prompted.

OpenAI's official GitHub App is:

```text
ChatGPT Codex Connector
https://github.com/apps/chatgpt-codex-connector
```

The GitHub App page identifies OpenAI as the developer and describes the app as bringing ChatGPT and Codex to GitHub repositories.

Prefer starting from the ChatGPT/Codex connection flow rather than installing a similarly named app manually, because the product flow carries the correct account/workspace context.

Official OpenAI reference:

```text
https://help.openai.com/en/articles/11145903-connecting-github-to-chatgpt
```

### Grant repository access

When GitHub asks where the app may be installed, choose the narrowest access that works.

For Personal-SoT, the recommended choice is conceptually:

```text
Only select repositories
→ <your-private-Personal-SoT-repository>
```

If the app is already installed:

1. return to ChatGPT `Settings → Plugins → GitHub`;
2. open the available repository-management option;
3. GitHub will open the app installation settings;
4. add/select the private Personal-SoT repository;
5. save the repository access.

A newly created private repository may not appear until it has been added to the existing GitHub App installation. OpenAI notes that repositories can take a few minutes to become available after authorization changes.

For an organization repository, an organization owner may need to approve the app or the specific repository.

### Read access versus write access

Do not infer write capability from a successful GitHub connection.

OpenAI documents the ChatGPT GitHub connection as repository access for reading/searching/analyzing code. Direct code edits, pushes, or PR workflows belong to Codex or another tool surface that actually exposes write capability.

Personal-SoT must still resolve the capabilities available in the current chat/task rather than assuming them.

### Test ChatGPT access

After granting access, first verify that ChatGPT can read the repository.

Then use the [ChatGPT Web setup](chatgpt_web.md) to add the Personalization locator and run:

```text
@do:sot
```

If the repository was previously returning 404, run `@do:sot` again after changing the app's repository access.

## Claude Web

### Connect GitHub from Claude

Anthropic's current Claude Web flow supports GitHub from chats and projects.

In a chat:

```text
+
→ Add from GitHub
```

In a Claude Project:

```text
Project knowledge
→ +
→ GitHub
```

Authenticate with GitHub when prompted, then select the repository/files needed for the project.

Anthropic's official reference:

```text
https://support.claude.com/en/articles/10167454-use-the-github-integration
```

### Grant access to a private repository

If Claude can see public repositories but cannot open the private Personal-SoT repository, follow Claude's GitHub App authorization flow and grant the app access to that repository.

Anthropic documents two normal choices:

```text
all repositories
or
specific repositories
```

For Personal-SoT, prefer the specific private repository unless you intentionally want broader access.

The official GitHub App published by Anthropic for the Claude GitHub integration is available at:

```text
Claude for GitHub
https://github.com/apps/claude-for-github
```

When possible, start from Claude's own `Add from GitHub` / project GitHub flow and follow the app link it provides.

If the repository belongs to an organization and SSO is enforced, GitHub may require you to grant organization access separately. Anthropic documents this under the Claude entry in GitHub account applications; if the button says `Request` instead of `Grant`, an organization administrator must approve it.

### Add Personal-SoT to a Claude Project

After Claude can access the repository:

1. add the private repository to the Claude Project;
2. select the Personal-SoT files/folders needed by the project;
3. use Claude's `Sync` / `Sync now` control after repository updates;
4. add the following project instruction, replacing the repository placeholder:

```text
repo: <owner>/<private-repository>
ref: main
adapter: workspace/adapters/claude_web_project_instructions.md

Before Personal-SoT-dependent work:

- Resolve the configured repo and ref using the repository access available in this conversation.
- Read and follow the configured adapter.
- Resolve its declared entrypoint and follow referenced canonical contracts relative to the repository root.
- Treat this resolved repository as the canonical Personal-SoT source.
- Resolve capabilities from the tools actually available in the current conversation; never infer write capability from read access.
- If required SoT files or capabilities are unavailable, report the limitation instead of guessing.
- `@do:sot` re-resolves and re-anchors the current conversation according to the canonical runtime.
```

Keep the adapter as this exact raw repository path:

```text
workspace/adapters/claude_web_project_instructions.md
```

The project instruction selects the intended source. It does not replace GitHub App authorization.

## Do not confuse the Claude GitHub Apps

Anthropic publishes multiple GitHub Apps for different workflows.

### `Claude for GitHub`

```text
https://github.com/apps/claude-for-github
```

Use the Claude Web/integration flow when you want Claude chats/projects to read repository files.

### `Claude`

```text
https://github.com/apps/claude
```

GitHub describes this app as running Claude Code from Pull Requests and Issues to respond to review feedback, fix CI errors, or modify code. This is a repository-development workflow and is not the same as simply connecting a private repository to a Claude Web Project.

### `Claude Github MCP Connector`

```text
https://github.com/apps/claude-github-mcp-connector
```

GitHub describes this as the app tied to Anthropic's remote GitHub MCP connector for Claude Cowork and other Claude surfaces. It is separate from the Claude App used by Claude Code.

Install only the app required by the Claude surface/workflow you actually use.

## Verify repository access in GitHub

For either provider, repository access is ultimately controlled by the installed GitHub App and GitHub account/organization policy.

In GitHub, review the installed app and confirm that:

```text
correct account/organization
+ correct GitHub App
+ private repository selected
+ no pending organization approval
= provider can attempt repository access
```

If your organization uses SSO, IP allow lists, or app restrictions, complete those provider-specific approvals too.

## Troubleshooting

### The repository exists but the AI client reports 404/not found

Treat this first as an authorization problem:

- confirm the AI client is connected to the correct GitHub account;
- confirm the expected GitHub App is installed on the correct account/organization;
- confirm the private repository is included in the app's repository access;
- complete any SSO or administrator approval;
- retry/re-sync the AI client after changing authorization.

Do not make the repository public as a workaround.

### Public repos work, private repo does not

The provider connection is likely present, but the private repository is not in the app's authorized repository set or requires organization approval.

### The repo was created after the app was installed

Return to the GitHub App installation settings and add the new repository. Existing app installations do not necessarily gain access to newly created private repositories automatically.

### The AI can read but cannot write

That is not an installation failure. Read and write are separate capabilities. Personal-SoT must use the capabilities actually available in the current client.

### The repository was updated but Claude Project shows old content

Use Claude's repository `Sync` / `Sync now` action before relying on the project copy.

## Safety

Use the narrowest repository scope that supports your workflow.

Never place GitHub tokens, app private keys, SSH private keys, passwords, recovery codes, one-time codes, or session cookies in Personal-SoT, Personalization, or Claude Project instructions.

Next:

- ChatGPT Web: [configure Personalization and re-anchor](chatgpt_web.md)
- General setup: [Set up Personal-SoT](setup.md)
