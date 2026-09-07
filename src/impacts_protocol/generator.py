"""Stamp a contract-only IMPACTS customer workspace and serve context templates."""

from importlib import resources
from pathlib import Path
import shutil
from tempfile import mkdtemp

from .workspace_contract import WORKSPACE_FOLDERS

TEMPLATE_KINDS = ("application", "hauptprozess", "teilprozess", "arbeitsschritt", "vorgang")


def init_workspace(target: Path) -> Path:
    """Create an empty, valid, file-native workspace template."""
    target = Path(target)
    if target.exists() or target.is_symlink():
        raise FileExistsError(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(mkdtemp(prefix=f".{target.name}.", dir=target.parent))
    try:
        _write_workspace(staging)
        if target.exists() or target.is_symlink():
            raise FileExistsError(target)
        staging.rename(target)
    except BaseException:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    return target


def template_text(kind: str) -> str:
    """Return the packaged CONTEXT.md template for one core object."""
    if kind not in TEMPLATE_KINDS:
        raise ValueError(f"unknown template kind: {kind}")
    filename = f"{kind}.md"
    try:
        return (
            resources.files("impacts_protocol.templates")
            .joinpath(filename)
            .read_text(encoding="utf-8")
        )
    except ModuleNotFoundError:
        return (
            Path(__file__).resolve().parents[2] / "02_protocol" / "templates" / filename
        ).read_text(encoding="utf-8")


ROUTER_BODY = """# IMPACTS Workspace

Applications definieren wiederverwendbare Prozesse. Vorgänge halten konkrete Durchläufe. Dieser Body ist der Betriebsvertrag für Mensch und Harness.

## Betriebsvertrag

1. Workspace-Root ist Git-Root. Ein Vorgang bindet nur einen committeten Application-Tree.
2. Application entwerfen: `impacts template application` zeigt die Schablone des Baums, `impacts template <art>` liefert jede `CONTEXT.md` (hauptprozess, teilprozess, arbeitsschritt). Ordner tragen fachliche Namen: `applications/<hauptprozess>/<teilprozess>/<arbeitsschritt>/CONTEXT.md`; die Rolle steht im `type`, die ID ist `<type>:<ordnername>`. Der Application-Baum enthält nur `CONTEXT.md`-Dateien. Nach dem Commit liefert `git rev-parse HEAD:applications/<slug>` die Revision. Eine Application aus einem anderen Repository kommt als Byte-Kopie von `applications/<slug>/` (`git archive | tar -x`), committet mit Quellcommit und Tree-OID in der Commit-Nachricht; der OID ist auf beiden Seiten gleich.
3. Vorgang öffnen: `vorgaenge/<slug>/CONTEXT.md` aus `impacts template vorgang` mit `application_revision: git-tree:<oid>`. Der erste Laufpfadeintrag ist der Einstieg der Application, Versuch `001`, Status `aktiv`. Eingaben liegen unter `<schritt>/001/input/`; `impacts hash <versuchsordner> <flaeche>...` liefert `eingabe_hash`.
4. Versuch abschließen: Ausgaben unter `output/` schreiben, `impacts hash` liefert `ausgabe_hash`, `gewaehlte_route` eintragen, Status `abgeschlossen`. Führt die Route zu einem Arbeitsschritt, folgt dessen Eintrag im selben Schreibvorgang; ein Laufpfad endet nie auf einem abgeschlossenen Eintrag mit Schrittroute. Führt sie zu `end:<slug>`, endet der Vorgang.
5. Human Gate: der Eintrag bleibt `aktiv`, bis der benannte Mensch `freigabe` mit `by: human:<id>` und `at` schreibt. Kein Agent schreibt `human:<id>`.
6. Warten: Status `wartend` mit `wiedereinstieg` (`ausloeser`, `continuation_ref`). Die Fortsetzung schließt denselben Versuch über eine Route ab.
7. `impacts validate .` vor jedem Commit. Exit 1 blockiert.
8. Der Core führt keinen Arbeitsschritt aus. Werkzeuge und Rechnungen sind Abhängigkeiten dieses Repos; der Arbeitsschritt-Body nennt den Aufruf.
"""


def _write_workspace(target: Path) -> None:
    for folder in WORKSPACE_FOLDERS:
        (target / folder).mkdir()

    (target / "CONTEXT.md").write_text(
        "---\ntype: workspace\n---\n\n" + ROUTER_BODY,
        encoding="utf-8",
    )
