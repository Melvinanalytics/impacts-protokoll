# I4: Complete process paths

## Normative rule

One Application contains one Hauptprozess. The Hauptprozess names its entry Arbeitsschritt. Every Arbeitsschritt owns at least one route to another Arbeitsschritt or a named `end:<slug>`.

The validator proves:

1. Entry and step targets resolve inside the same Application.
2. Every declared Arbeitsschritt is reachable from entry.
3. Every Arbeitsschritt has a route path to a named end.
4. A loop has an exit because each contained step can reach an end.
5. A Human Gate owns exactly `freigegeben` and `abgelehnt`.

Waiting is a state of the current Laufpfad entry. It keeps the current Arbeitsschritt and carries `ausloeser` plus `continuation_ref`. Resume continues through one declared route. No separate wait node or Wiedervorlage object exists.

Each violation yields one of `reference.unresolved`, `process.unreachable`, `process.no_end`, `process.gate` or `run.invalid`.
