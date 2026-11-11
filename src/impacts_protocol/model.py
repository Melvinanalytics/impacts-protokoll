"""Immutable validator result types."""

from dataclasses import dataclass, field


RULES = {
    "format": "02_protocol/binding.md#validation-issue-codes",
    "schema": "02_protocol/binding.md#validation-issue-codes",
    "routing": "02_protocol/binding.md#hauptprozess-tree-rules",
    "structure": "02_protocol/binding.md#hauptprozess-tree-rules",
    "reference": "02_protocol/binding.md#hauptprozess-tree-rules",
    "process": "02_protocol/binding.md#execution",
    "process.gate": "02_protocol/binding.md#decision-results-and-auslöser",
    "process.no_end": "02_protocol/binding.md#hauptprozess-tree-rules",
    "process.unreachable": "02_protocol/binding.md#hauptprozess-tree-rules",
    "binding": "02_protocol/binding.md#snapshot-and-provenance",
    "execution": "02_protocol/binding.md#execution",
    "trust": "02_protocol/binding.md#signals-and-human-gates",
}


def issue_rule(code: str) -> str:
    return RULES.get(code, RULES.get(code.split(".")[0], "02_protocol/binding.md#validation-issue-codes"))


def judged_counts() -> dict[str, int]:
    return dict.fromkeys(("hauptprozess", "teilprozess", "arbeitsschritt", "vorgang", "versuch"), 0)


@dataclass(frozen=True)
class Issue:
    code: str
    path: str
    message: str
    rule: str = ""

    def __post_init__(self):
        if not self.rule:
            object.__setattr__(self, "rule", issue_rule(self.code))


@dataclass(frozen=True)
class NotJudged:
    path: str
    protocol: str | None
    validator_protocol: str
    reason: str | None = None

    @property
    def message(self) -> str:
        if self.reason:
            return f"{self.path}: {self.reason}"
        recorded = self.protocol if self.protocol is not None else "none"
        if self.path == "CONTEXT.md":
            return f"workspace not judged under {self.validator_protocol}: pinned {recorded}"
        return f"not judged under {self.validator_protocol}: {self.path} (records {recorded})"


@dataclass(frozen=True)
class ValidationReport:
    issues: tuple[Issue, ...]
    not_judged: tuple[NotJudged, ...] = ()
    superseded: tuple[str, ...] = ()
    external_references_not_verified: int = 0
    external_references: tuple[dict, ...] = ()
    release: str | None = None
    pin: str | None = None
    judged: dict[str, int] = field(default_factory=judged_counts)

    @property
    def not_judged_counts(self) -> dict[str, int]:
        return {
            "vorgang": sum(item.path.startswith("vorgaenge/") and not item.reason for item in self.not_judged),
            "definition_tree": sum(item.reason == "definition tree outside hauptprozesse/, not bindable" for item in self.not_judged),
        }

    @property
    def valid(self) -> bool:
        return not self.issues


ATTEMPT_PHASE = {"aktiv": "current", "wartend": "waiting", "abgeschlossen": "done", "abgebrochen": "stopped"}


def derive_progress(entries: list[dict], steps: dict[str, dict], leistung: dict,
                    *, superseded: bool = False) -> dict:
    """Derive the binding.md progress table for a structurally checked Laufpfad.

    Return open values for missing derivation inputs. No authority or business outcome
    is inferred. Callers establish whether a successor is judged before superseding.
    """
    result = {"status": "open", "current": None, "ended": None, "erreicht": "open",
              "phase": {}, "nummer": None}
    if not entries or any(not isinstance(e, dict) for e in entries):
        return result
    phases = result["phase"]
    path, looped = [], set()
    for entry in entries:
        ref, status = entry.get("arbeitsschritt_ref"), entry.get("status")
        if not isinstance(ref, str) or ref not in steps or not isinstance(status, str) or status not in ATTEMPT_PHASE:
            return result
        phases[ref] = ATTEMPT_PHASE[status]
        looped.discard(ref)
        if ref in path:
            cut = path.index(ref) + 1
            looped.update(path[cut:])
            del path[cut:]
        else:
            path.append(ref)
    for ref in looped:
        if phases[ref] == "done":
            phases[ref] = "looped"
    last = entries[-1]
    ref, status = last["arbeitsschritt_ref"], last["status"]
    result.update(current=ref, status=status, nummer=last.get("nummer"), erreicht=None)
    if status == "abgeschlossen":
        route = last.get("gewaehlte_route")
        target = steps[ref].get("routen", {}).get(route) if isinstance(route, str) else None
        if target in steps:
            result.update(status="zwischen", current=target, nummer=None)
            phases[target] = "next"
        elif isinstance(target, str) and target.startswith("end:"):
            ends = leistung.get("erreicht")
            result.update(status="beendet", current=None, ended=target,
                          erreicht="open" if not isinstance(ends, list) else target in ends)
        else:
            result.update(status="open", current=None, erreicht="open")
    elif status == "abgebrochen":
        result.update(current=None, erreicht=False)
    elif status == "wartend":
        for target in steps[ref].get("routen", {}).values():
            if target in steps and target not in phases:
                phases[target] = "possible"
    if superseded:
        result.update(status="superseded", current=None, erreicht=False)
        for ref, phase in phases.items():
            if phase in {"current", "waiting", "next", "possible"}:
                phases[ref] = "superseded"
    return result
