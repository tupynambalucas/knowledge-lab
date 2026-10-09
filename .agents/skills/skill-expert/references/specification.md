# Agent Skills Specification

This document provides the complete format specification for Agent Skills, aligning with the
open standard adopted by Antigravity and compatible agent environments.

---

## 1. Directory Structure

A skill is a self-contained directory containing, at minimum, a `SKILL.md` file:

```plaintext
<skill-name>/
├── SKILL.md          # Required: metadata + core instructions (< 500 lines)
├── scripts/          # Optional: executable scripts and automation tools
├── references/       # Optional: in-depth documentation and domain guides
├── assets/           # Optional: templates, schemas, data tables, or mockups
└── ...               # Any additional files or directories
```

---

## 2. `SKILL.md` Format

The `SKILL.md` file MUST begin with a YAML frontmatter block delimited by `---` lines, followed by
Markdown content.

### Frontmatter Fields

The specification defines exactly six valid frontmatter fields. Any unrecognized or extra fields are
treated as validation errors:

| Field           | Required | Type   | Constraints & Description                                                                                                                                                                                                     |
| :-------------- | :------- | :----- | :---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `name`          | Yes      | String | 1-64 characters. Lowercase alphanumeric characters (`a-z`, `0-9`) and hyphens (`-`) only. Must not start or end with a hyphen. Must not contain consecutive hyphens (`--`). **Must match the parent directory name exactly**. |
| `description`   | Yes      | String | 1-1024 characters. Non-empty. Describes what the skill does and when the agent should use it. Use imperative phrasing and explicit keywords.                                                                                  |
| `license`       | No       | String | Short license identifier (e.g., `Apache-2.0`, `MIT`) or reference to a bundled file.                                                                                                                                          |
| `compatibility` | No       | String | 1-500 characters. Explains environment requirements (e.g., "Requires Python 3.11+ and uv").                                                                                                                                   |
| `metadata`      | No       | Map    | Arbitrary key-value mapping from string keys to string values for client-specific properties.                                                                                                                                 |
| `allowed-tools` | No       | String | Space-separated list of pre-approved tools the skill may use (e.g., `Bash(git:*) Read`).                                                                                                                                      |

### Minimal Frontmatter Example

```yaml
---
name: roll-dice
description: Roll dice using a random number generator. Use when asked to roll a die or generate a random dice roll.
---
```

### Full Frontmatter Example

```yaml
---
name: pdf-processing
description: Extract PDF text, fill forms, merge files. Use when handling PDFs or document extraction tasks.
license: Apache-2.0
compatibility: Requires Python 3.11+, uv, and poppler-utils
allowed-tools: Bash(uv:*) Read
metadata:
  version: "1.0"
  author: architecture-team
---
```

---

## 3. Progressive Disclosure Architecture

To prevent token context exhaustion, agents load skills in three progressive stages:

1. **Discovery (~100 tokens)**: At startup, agents load only the `name` and `description` of each
   available skill to determine relevance.
2. **Activation (< 5000 tokens)**: When a task matches the skill description, the agent loads the full
   `SKILL.md` body into context.
3. **Execution (On Demand)**: Files in `scripts/`, `references/`, or `assets/` are loaded only when the
   agent's execution requires them.

### Line and Token Budget

- `SKILL.md` MUST remain under **500 lines** and should be under **5,000 tokens**.
- Detailed technical manuals, extended schemas, or edge-case dictionaries must be extracted to
  separate files under `references/`.
- Always provide explicit triggers telling the agent _when_ to load each reference file (e.g.,
  "Read [api-errors.md](references/api-errors.md) if the response code is non-200").
- Keep file references one level deep from `SKILL.md`. Avoid deeply nested reference chains.

---

## 4. Body Content Best Practices

The Markdown body following the frontmatter provides operational instructions:

- **Procedures Over Declarations**: Teach the agent _how to approach_ the problem rather than giving
  a static answer to one instance.
- **Gotchas Section**: Document non-obvious traps, quirks, and environment-specific behaviors that
  an agent would otherwise get wrong.
- **Defaults over Menus**: Pick a clear default tool or path, offering alternatives only as explicit
  fallbacks.
- **Calibrated Control**: Provide prescriptive instructions for fragile operations, and flexible
  guidance for tasks tolerating variation.

---

## 5. Script Design Standards (`scripts/`)

When bundling scripts:

- **Non-Interactive**: Scripts MUST run without interactive prompts, TTY menus, or password dialogs.
- **Self-Documenting**: Implement `--help` detailing flags, arguments, and exit codes.
- **Structured Output**: Write structured data (JSON, CSV) to `stdout` and diagnostic messages or
  progress logs to `stderr`.
- **Inline Dependencies**: Use self-contained script metadata where possible (e.g., PEP 723 for
  Python using `uv run`, or `tsx`/Node for TypeScript).
- **Safe Defaults**: Support `--dry-run` for stateful or destructive operations.
