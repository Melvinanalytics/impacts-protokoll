# Application layout

This template applies to selected Core contracts under `02_protocol/impacts-architect/references/formwahl.md`, "Tooling stop", in the recorded protocol source/revision.

An Application is one main process with its accepted result, subprocesses and worksteps. Folders carry domain names; each `CONTEXT.md` declares its role in `type`. This layout shows where each file belongs and which template creates it. It is not a router and is not stored as `CONTEXT.md`. Select the customer's language with `--language de` or `--language en` when generating working templates.

<a id="baum"></a>
## Tree

```text
applications/<hauptprozess>/
├── CONTEXT.md                  # type: hauptprozess    impacts template hauptprozess
└── <teilprozess>/
    ├── CONTEXT.md              # type: teilprozess     impacts template teilprozess
    └── <arbeitsschritt>/
        └── CONTEXT.md          # type: arbeitsschritt  impacts template arbeitsschritt

vorgaenge/<vorgang>/
├── CONTEXT.md                  # type: vorgang         impacts template vorgang
└── <arbeitsschritt>/<versuch>/
    ├── input/
    └── output/
```

## Rules

- A frontmatter block-scalar value must not contain a bare `---` line.
- Placeholders are slugs matching `[a-z0-9]+(?:-[a-z0-9]+)*`. Each ID is `<type>:<folder-name>`.
- An Application contains only `CONTEXT.md` files and folders. Each main process has at least one subprocess, each subprocess at least one workstep; worksteps have no subfolders.
- Workstep IDs are unique across the Application. Routes target `arbeitsschritt:<slug>` or `end:<slug>`; every step can reach an end.
- `<versuch>` has three digits; `versuch: 1` means `001`. Only steps and attempts reached by `laufpfad` have run folders.

The workstep body contains its prompt and tool invocation contract. Shared rules, prompt fragments and document blanks keep their existing domain home outside this tree and enter attempts as declared inputs with provenance. Tool implementations remain dependencies or earned Capabilities; actual values, intermediate work and result evidence belong to the run. Use the recorded protocol's `impacts-method.md`, “Compose an Arbeitsschritt”, and the workstep template to fill this contract.

## Example

```text
applications/prueffall/
├── CONTEXT.md                  # hauptprozess:prueffall
├── vorpruefung/
│   ├── CONTEXT.md              # teilprozess:vorpruefung
│   ├── pruefen/CONTEXT.md      # arbeitsschritt:pruefen
│   └── nachfordern/CONTEXT.md  # arbeitsschritt:nachfordern
└── entscheidung/
    ├── CONTEXT.md              # teilprozess:entscheidung
    └── entscheiden/CONTEXT.md  # arbeitsschritt:entscheiden
```

Establish required Core structural conformance with `impacts validate` on the selected scope; retain any failed or unperformed condition under the bound Tooling stop boundary.
