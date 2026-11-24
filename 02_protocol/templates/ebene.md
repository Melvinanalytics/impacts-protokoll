# <Level name>

<!-- Level router: one CONTEXT.md per Record Library or Knowledge Bundle level. Layout after the CONTEXT.md anatomy in the ICM Workspace Blueprint (_examples/03-context-md-anatomy.md); aim for 25 to 80 lines, a guide, not a rule. `impacts validate` checks only the Form line and that this router links each entry of the level by a relative link; it does not check these headings. Delete every placeholder row you do not fill. -->

`Form: <form> per <unit>`: write this line unindented and without backticks only when this level declares itself; otherwise its parent router declares it.

## What lies here

`<One or two sentences: what this level holds, who fills it, who reads it.>`

## What to load

| Intent | Open | Do not load |
|---|---|---|
| `<intent in the words of the work>` | `<relative link to <entry>/ or <entry>/CONTEXT.md>` | `<nearby entry this intent must skip, and why>` |

## Overview

One row per entry; each row links the entry by a relative path. A missing link is a validator finding.

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
