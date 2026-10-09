---
name: mdx-docs-expert
description: Use this skill when extracting, creating, updating, or reviewing architectural documentation in MDX format (.mdx) within the docs/ workspace, adhering to the Diátaxis framework and Portuguese (pt-BR) language standards.
---

# MDX Architectural Documentation Expert

This skill defines the authoritative standards, directory structures, Diátaxis quadrant
organization, MDX specifications, and validation workflows for architectural knowledge in `docs/`.

---

## 1. Architectural Knowledge Base & Diátaxis Framework

The `docs/` workspace officially adopts the **Diátaxis** framework for all architectural
documentation (starting with Autodesk Revit). All documentation must be structured around the
learner's needs into four distinct quadrants rather than unstructured topic dumps.

MDX (`.mdx`) is the mandatory format because its structured AST, frontmatter metadata,
component-readiness, and explicit syntax provide superior machine-readability for AI models and
agents compared to ambiguous, unstructured markdown.

### A. The Four Diátaxis Quadrants

Every document authored or updated within a domain (such as `docs/revit/`) MUST be classified and
placed into the appropriate quadrant directory:

- `tutorials/`: **Learning-oriented**. Practical step-by-step lessons for beginner architects to
  acquire core competencies (e.g., initial project configuration, basic structural grid creation).
- `guides/` (How-to guides): **Goal-oriented**. Practical step-by-step recipes to solve specific
  architectural and modeling problems (e.g., configuring shared coordinates, setting up parametric
  curtain wall families).
- `reference/`: **Information-oriented**. Concise technical descriptions, parameter catalogs, tool
  ribbon layouts, family category matrices, keyboard shortcut references, and API/node definitions.
- `explanation/`: **Understanding-oriented**. Theoretical discussions, architectural background, BIM
  methodology concepts, coordination workflows, and parametric modeling philosophy.

### B. Directory Structure Pattern

Each domain within `docs/` (e.g., `docs/revit/`) follows this standard layout:

```plaintext
docs/<domain>/
├── AGENTS.md                 # Sub-domain router (Layer 3)
├── README.md                 # Human entry point (English)
├── tutorials/                # Learning-oriented lessons (.mdx)
├── guides/                   # How-to guides for specific problems (.mdx)
├── reference/                # Technical reference, parameters, specs (.mdx)
└── explanation/              # Theoretical and architectural explanations (.mdx)
```

When a domain requires grouped sub-categories within a quadrant, group related files inside a
dedicated subfolder (e.g., `docs/revit/reference/families/`).

---

## 2. Document & MDX Standards

All files placed inside `docs/` (excluding entry point `README.md` and router `AGENTS.md`) MUST
strictly adhere to the following rules:

### A. Language Policy: Portuguese (pt-BR)

- **Mandatory Portuguese**: All architectural documentation, titles, descriptions, headings, notes,
  and explanations in `docs/` MUST be written in Portuguese (pt-BR).
- **Technical Terms**: Standard architectural software terminology (e.g., Autodesk Revit terms) may
  reference the original English term alongside the Portuguese definition for clarity (e.g.,
  "Família Carregável (_Loadable Family_)", "Parâmetros de Tipo (_Type Parameters_)").

### B. Tone of Voice: Senior Architecture Research Assistant

- Maintain a highly didactic, educational, and accessible tone.
- The primary reader is an architect engaged in studies, not a software developer.
- Break down complex architectural and BIM concepts step-by-step.
- Explain the practical rationale ("why this matters in architectural practice") alongside technical
  instructions.
- Avoid casual chatter, conversational filler, or empty conclusion paragraphs.

### C. Extension Rule: All-MDX

- **Zero `.md` Files for Documentation**: All technical and architectural documentation must use the
  `.mdx` file extension. The only allowed `.md` files are `README.md` and `AGENTS.md`.
- MDX provides strict AST parsing, metadata uniformity, and rich UI component support that enables
  AI models to parse, extract, and index documentation with high fidelity.

### D. Frontmatter Specifications

Every `.mdx` file MUST begin with a complete YAML frontmatter block enclosed by `---`:

```yaml
---
title: "Modelagem de Paredes Básicas no Revit"
description: "Aprenda a configurar e modelar paredes básicas no Autodesk Revit passo a passo."
sidebar_position: 1
quadrant: "tutorial"
tags: ["revit", "arquitetura", "modelagem", "paredes"]
---
```

- `title`: Clear, descriptive document title in Portuguese (pt-BR).
- `description`: One or two sentences summarizing the document's learning or operational outcome.
- `sidebar_position`: Integer defining sequential display order.
- `quadrant`: The Diátaxis quadrant (`tutorial`, `guide`, `reference`, `explanation`).
- `tags`: Array of relevant architectural and software keyword tags.

### E. MDX Syntax & Formatting Rules

- **Zero HTML Comments**: Standard HTML comments (`<!-- comment -->`) are forbidden. Always use
  JavaScript comments wrapped in curly braces: `{/* Comentário MDX */}`.
- **Escaping Special Characters**: Literal curly braces (`\{` and `\}`) and less-than signs (`\<`)
  must be escaped when used in plain text to prevent JSX parse errors.
- **Self-Closing Tags**: All JSX and HTML elements must be self-closing (e.g., `<br />`, `<hr />`,
  `<img src="..." />`).
- **Admonitions**: Use native colon admonitions with Portuguese titles:
  - `:::note[Nota]` for supplementary context.
  - `:::tip[Dica de Modelagem]` for architectural best practices and efficiency shortcuts.
  - `:::info[Informação Técnica]` for technical specs and BIM standards.
  - `:::caution[Atenção]` for common modeling traps and coordinate pitfalls.
  - `:::danger[Aviso Crítico]` for risk of data loss, corrupt worksets, or broken central models.
- **Cross-linking**: Use relative markdown links with the `.mdx` extension (e.g.,
  `[Guia de Famílias](../guides/familias-parametricas.mdx)`). Absolute filesystem paths are
  strictly forbidden.
- **Formatting**: Strictly follow Prettier standards (2-space indent, max 100-character line
  width, hyphen-based unordered lists).
- **Zero Emojis**: Emojis are strictly forbidden across all documentation.
- **Zero Placeholders**: Never include "TODO", "TBD", or empty sections.

For complete MDX syntax rules and JSX guidelines, read [syntax.md](references/syntax.md).
For architectural layout templates for each quadrant, read [patterns.md](references/patterns.md).

---

## 3. Extraction & Normalization Workflow (Firecrawl & Context7)

When extracting architectural knowledge from external sources (Autodesk Knowledge Network, vendor
manuals, architectural standards) using tools like Firecrawl or Context7:

1. **Strip Scraped Web Noise**: Remove cookie banners, navigation breadcrumbs, floating menus, AI
   chat widgets, feedback forms, and site announcement headers.
2. **Classify by Diátaxis Quadrant**: Analyze the extracted content and assign it to the proper
   quadrant (`tutorials/`, `guides/`, `reference/`, or `explanation/`).
3. **Structure & Translate into Portuguese (pt-BR)**: Restructure the extracted content into a
   didactic Brazilian Portuguese document tailored for architectural learners.
4. **Convert to MDX**: Add YAML frontmatter, convert callouts to MDX admonitions, and ensure all
   tags and special characters comply with MDX parsing.
5. **Deduplication Check**: Check existing files in the domain before creating a new one. If the
   topic already exists, update and enrich the existing `.mdx` file.

For the step-by-step extraction and validation pipeline, read [workflow.md](references/workflow.md).

---

## 4. Single-Pass Deferred Validation

To ensure documentation integrity:

- Batch all file creations or modifications before performing validation.
- Verify that every file uses the `.mdx` extension, has valid frontmatter, contains zero emojis, has
  no broken relative links, and conforms to Prettier formatting.
