# Install Personal-SoT

This guide is the beginner path for installing Personal-SoT on Windows, macOS, or Linux.

Use it when you are creating a **new private Personal-SoT installation**. If you already have a private `myPersonal-SoT` repository and only want to use it on another computer, jump to [Existing private installation](#existing-private-installation).

## Fast path

```text
install Git + Python 3
→ create an empty private GitHub repository
→ clone mrAlishah/Personal-SoT
→ run install.bat / install.sh with --github
→ connect your AI client to the private sot
→ Web clients: install/authorize the required GitHub App + select the private repo
→ @do:sot
→ @do:setup
```

If this is your first install, follow the steps below in order.

## What you need

Before installing:

- **Git**
- **Python 3.10 or newer**
- a GitHub account if you want the GitHub Private option
- an **empty private GitHub repository** for a new GitHub-backed installation
- or an **empty local folder already synced by Google Drive Desktop** for the Drive option

Personal-SoT uses only the Python standard library for the bootstrap installer. No `pip install` step is required.

## 1. Check the prerequisites

### Windows

Use **Windows Terminal / PowerShell**.

Install:

- [Git for Windows](https://git-scm.com/download/win)
- [Python for Windows](https://www.python.org/downloads/windows/)

Then open a **new** PowerShell window and run:

```powershell
git --version
py -3 --version
```

`install.bat` prefers `py -3`, then falls back to `python`. It is fine if `python --version` and `py -3 --version` show different Python 3 versions; the installer uses `py -3` when the Python launcher is available.

A full Windows restart is normally not required after installing Python or Git. Opening a new terminal is usually enough for PATH changes.

### macOS

Check:

```bash
git --version
python3 --version
```

If Git is missing, macOS can install the Command Line Tools:

```bash
xcode-select --install
```

If Python 3 is missing, install a current Python 3 from [python.org](https://www.python.org/downloads/macos/) or with Homebrew:

```bash
brew install python
```

### Linux

Check:

```bash
git --version
python3 --version
```

Debian/Ubuntu:

```bash
sudo apt update
sudo apt install git python3
```

Fedora:

```bash
sudo dnf install git python3
```

Use your distribution's normal package manager on other Linux distributions.

## 2. Create the private destination

For a new GitHub-backed installation, create a repository on GitHub and set it to **Private**.

Leave it completely empty:

- do not initialize it with a README
- do not add a `.gitignore`
- do not add a license

You can verify an empty repository with:

```bash
git ls-remote https://github.com/<you>/myPersonal-SoT.git
```

An empty repository returns no refs. If you see `HEAD` or `refs/heads/main`, the repository already contains a commit.

HTTPS is the simplest beginner choice because Git Credential Manager can handle GitHub sign-in. SSH also works if your SSH key and agent are already configured.

## 3. Clone `sot public`

Run:

```bash
git clone https://github.com/mrAlishah/Personal-SoT.git
cd Personal-SoT
```

The installer must start from:

- the public `mrAlishah/Personal-SoT` clone
- branch `main`
- a clean working tree

## 4. Install to a private GitHub repository

Using the explicit `--github` form is the clearest path.

### Windows PowerShell

```powershell
Set-Location D:\Projects\Personal-SoT
.\install.bat --github https://github.com/<you>/myPersonal-SoT.git
```

### macOS / Linux

```bash
cd /path/to/Personal-SoT
./install.sh --github https://github.com/<you>/myPersonal-SoT.git
```

Do **not** pass the URL as a bare argument:

```text
install.bat https://github.com/<you>/myPersonal-SoT
```

That form is invalid. Use `--github <URL>`.

### Interactive alternative

You can also run the installer without arguments:

Windows:

```powershell
.\install.bat
```

macOS/Linux:

```bash
./install.sh
```

Then choose:

```text
1. GitHub private repository
```

and paste the empty private repository URL when asked.

## 5. Google Drive alternative

The destination must be an empty **local folder** that is already synchronized by Google Drive Desktop or equivalent. A browser sharing URL is not a writable destination.

Windows:

```powershell
.\install.bat --drive "G:\My Drive\Personal-SoT"
```

macOS/Linux:

```bash
./install.sh --drive "/path/to/synced/Personal-SoT"
```

## What the installer does

For the GitHub Private path, the installer:

```text
checks the public clone
→ runs validators and Doctor
→ verifies the private destination is accessible and empty
→ renames public origin to upstream
→ adds the private repository as origin
→ pushes main to the private repository
→ runs the checks again
```

After a successful GitHub installation, the remote roles should be:

```text
origin   → your private repository
upstream → mrAlishah/Personal-SoT
```

Verify:

```bash
git remote -v
git status --short --branch
```

## 6. Connect your AI client and finish setup

For an authorized local client such as Codex or Claude Code, open the resulting private `sot` repository/folder.

For **ChatGPT/Codex or Claude Web + a private GitHub repository**, connecting GitHub is a separate authorization step. The installer can create and push the private `sot`, but it cannot install an AI provider's GitHub App or grant that app access to your private repository.

Use [GitHub access for ChatGPT, Codex, and Claude](github_ai_connections.md) to install/connect the correct provider app and select the private repository.

Then:

- ChatGPT Web: use [ChatGPT Web setup](chatgpt_web.md) for the copyable Personalization locator.
- Claude Web: add the repository to the Claude Project and use the Claude Project instruction shown in the GitHub access guide.

Then run:

```text
@do:sot
@do:setup
```

`@do:sot` re-resolves the configured private source using the access actually available in that chat. `@do:setup` then finishes user-specific configuration. The installer itself only prepares and verifies the private installation destination.

## Existing private installation

If your private `myPersonal-SoT` repository already contains your real Personal-SoT, **do not use the initial installer with that non-empty repository as the destination**.

On the new computer, clone the private repository directly:

```bash
git clone https://github.com/<you>/myPersonal-SoT.git
cd myPersonal-SoT
```

A clone only brings the `origin` remote. Add the public product as `upstream` if it is not already configured locally:

```bash
git remote add upstream https://github.com/mrAlishah/Personal-SoT.git
git remote -v
```

Expected roles:

```text
origin   → your existing private repository
upstream → mrAlishah/Personal-SoT
```

Then open that private repository in your AI client and run:

```text
@do:sot
@do:setup
```

## Troubleshooting

### Windows: `UnicodeEncodeError` / `cp1252`

Current `install.bat` enables UTF-8 for the Python processes it launches, so Doctor can print symbols such as `✓`, `✗`, and `⚠` even when the Windows locale defaults to `cp1252`.

If you are running an older checkout that does not yet contain that fix, use this temporary PowerShell workaround:

```powershell
$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"
.\install.bat --github https://github.com/<you>/myPersonal-SoT.git
```

### `unrecognized arguments: https://github.com/...`

Use:

```powershell
.\install.bat --github https://github.com/<you>/myPersonal-SoT.git
```

not a bare URL argument.

### More than one Python is installed on Windows

Check:

```powershell
python --version
python3 --version
py -3 --version
```

`install.bat` uses `py -3` first. If that reports a supported Python 3 version, the presence of another `python.exe` is not itself a problem.

### The private GitHub repository is not empty

The initial GitHub installer intentionally refuses a destination that already has commits. For a brand-new install, use a new empty private repository. If the repository already contains your Personal-SoT, use the [existing private installation](#existing-private-installation) path instead.

### GitHub asks for credentials

For HTTPS, complete the GitHub/Git Credential Manager sign-in flow. For SSH, keep the SSH key passphrase and use `ssh-agent` rather than removing the passphrase just to avoid repeated prompts.

### ChatGPT Web gets `404 Not Found` for the private repository

A Personalization locator does not grant GitHub access. If the repository exists but ChatGPT returns 404, first check that the ChatGPT GitHub connection is using the correct GitHub account or organization and that the specific private repository is selected in the GitHub app's repository access.

Do not make the private repository public as a workaround. After fixing repository authorization, run `@do:sot` again so the chat re-resolves the source.

See [GitHub access for ChatGPT, Codex, and Claude](github_ai_connections.md) and [ChatGPT Web setup](chatgpt_web.md) for the full checklist.

### `The public clone has local changes`

Do not install from a modified public clone. Check:

```bash
git status --short --branch
```

Use a clean `main` clone of `mrAlishah/Personal-SoT` for the initial installation.

## Safety

Never put passwords, API tokens, private keys, recovery codes, one-time codes, session cookies, or payment credentials into Personal-SoT.

Next: [Set up Personal-SoT](setup.md).
