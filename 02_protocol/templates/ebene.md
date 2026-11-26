# <Level name>

<!-- Level router: one CONTEXT.md per Record Library, Knowledge Bundle or Context Map level; a Capability, Tool or Check router follows the same layout. Layout after the CONTEXT.md anatomy in the ICM Workspace Blueprint (_examples/03-context-md-anatomy.md); aim for 25 to 80 lines, a guide, not a rule. `impacts validate` checks the Form line, that this router links each entry of the level by a relative link, that a level router holds the headings Overview and What to load at any number of entries, and, except for a Record Library or Context Map router, that the router stays at or below 24,000 bytes; it checks no other heading. Delete every placeholder row you do not fill. -->

`Form: <form> per <unit>`: write this line unindented and without backticks only when this level declares itself; otherwise its parent router declares it.

## What lies here

`<One or two sentences: what this level holds, who fills it, who reads it.>`

## Call and checks

Only in a Capability, Tool or Check router; delete this section in a level router.

- Call: `<command or operation with its inputs>`
- Checks before its result counts: `<check, where it reports, what a failure stops>`

## What to load

| Intent | Open | Do not load |
|---|---|---|
| `<intent in the words of the work>` | `<relative link to <entry>/ or <entry>/CONTEXT.md>` | `<nearby entry this intent must skip, and why>` |

## Overview

One row per entry; each row links the entry by a relative path. A missing link is a validator finding.

Optional, only when a tool writes rows into this table: put `<!-- impacts:table-contract heading="Overview" columns="Entry, State and source" -->` on its own line in this router, without backticks, naming the columns the tool needs. `impacts validate` then fails if a column is renamed or dropped.

| Entry | What it is | Writer | State and source |
|---|---|---|---|
| `<relative link to <entry>/ or <entry>/CONTEXT.md>` | `<what one entry holds>` | `<person or tool that adds entries>` | `<evidence label, as-of date, source>` |

## Rules

- `If <observable condition>, then <action>; source: <relative link>.`

## Tools

| Tool | When | Permitted effect |
|---|---|---|
| `<tool or Capability>` | `<observable trigger, not "available">` | `<files it may write or change>` |

## Do not

Only errors that were observed, each with its date and evidence; add rows when a mistake happens, never in advance.

- `<observed error> (seen <YYYY-MM-DD>, evidence: <relative link>)`
