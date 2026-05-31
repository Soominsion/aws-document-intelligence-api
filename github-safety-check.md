# GitHub Safety Check

Run this review before every push, especially before making a repository public.

## Files That Must Not Be Committed

- `.env` and other local environment files
- `.venv/`
- `.cache/`
- Hugging Face model weights and cache files
- `__pycache__/`
- `*.pem`
- `*.key`
- `*.log`
- AWS credential files
- AWS access keys or secret keys inside source or documentation

The repository `.gitignore` already excludes these common patterns. This review confirms that they are not tracked accidentally.

## 1. Review Local Changes

```powershell
git status
git status --short --ignored
```

Ignored local files appear with `!!` in the second command. Expected examples:

```text
!! .cache/
!! .venv/
!! app/__pycache__/
```

## 2. Review Every Tracked File

```powershell
git ls-files
```

Confirm that the output does not contain `.env`, `.venv/`, `.cache/`, model files, Python cache files, private keys, or logs.

Use this PowerShell check to highlight tracked paths that look unsafe:

```powershell
git ls-files | Select-String -Pattern '(^|/)\.env(?!\.example$)($|\.)|(^|/)\.venv/|(^|/)\.cache/|huggingface|pytorch_model|model\.safetensors|(^|/)__pycache__/|\.pyc$|\.pem$|\.key$|\.log$|(^|/)\.aws/'
```

No output is the expected result. The committed `.env.example` template is intentionally allowed.

## 3. Search Tracked Content for Credential Patterns

```powershell
git grep -n -E 'AKIA[0-9A-Z]{16}|ASIA[0-9A-Z]{16}|aws_access_key_id|aws_secret_access_key|BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY' -- . ':!github-safety-check.md'
```

No output is the expected result. The guide itself is excluded because it contains the search terms as examples.

Also inspect references to security-sensitive words:

```powershell
git grep -ni -E 'secret|credential|access[_-]?key|private[_-]?key' -- . ':!github-safety-check.md'
```

This broader search may return documentation such as this file. Read each match and confirm that it is an instruction or placeholder, not a real secret.

## 4. Review Staged Content Before Commit

```powershell
git add .
git status --short
git diff --cached --stat
git diff --cached
```

Read the staged diff before committing. If an unsafe file appears, stop and remove it from the staged set:

```powershell
git restore --staged <path>
```

## 5. Review GitHub After Push

Open the GitHub repository and inspect the file tree. Confirm that local environments, caches, credentials, keys, and logs are absent.

If a real credential is ever committed, removing the file in a later commit is not enough. Revoke or rotate the credential immediately, then clean the Git history if needed.
