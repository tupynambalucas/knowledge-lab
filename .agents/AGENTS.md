<context-hierarchy src="../AGENTS.md">
  <system-instruction>
    Stop now and read the parent context file before proceeding with any actions in this directory.
  </system-instruction>
</context-hierarchy>

# Agents & Automation Context

This document serves as the bounded context router (Layer 2) for the `.agents/` workspace.

## Purpose

This directory manages all AI agent behaviors, skills, and user-driven execution plans for Knowledge Lab.

## Workspaces

- [skills](./skills/): Contains all custom agent skills, formatted according to the `skill-expert` guidelines.
- [plans](./plans/): Directory dedicated to study and execution plans authored by the user.

## Guidelines

- Agents MUST strictly follow the directives in `skills/` when performing tasks.
- The `plans/` directory is the primary source of truth for upcoming study goals and architectural milestones.
