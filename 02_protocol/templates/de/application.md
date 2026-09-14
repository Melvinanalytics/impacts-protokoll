<!-- Translation source: 02_protocol/templates/application.md; sha256: 8039d02846c9e75935d303020f5ace23d7baf0c2d7d02a99bd4faaeaf392b6cd -->

# Schablone einer Application

Diese Vorlage gilt für gewählte Core-Verträge gemäß `02_protocol/impacts-architect/references/formwahl.md`, Abschnitt „Tooling stop“, in der benannten Protokollquelle und Revision.

Eine Application ist ein Hauptprozess mit seiner Leistung, seinen Teilprozessen und Arbeitsschritten. Die Ordner tragen die fachlichen Namen des Prozesses; die Rolle jeder `CONTEXT.md` steht in ihrem `type`. Diese Schablone zeigt, wo jede Datei liegt und welche Vorlage sie erzeugt. Sie ist kein Router und wird nicht als `CONTEXT.md` gespeichert.

## Baum

```text
applications/<hauptprozess>/
├── CONTEXT.md                  # type: hauptprozess    impacts template hauptprozess --language de
└── <teilprozess>/
    ├── CONTEXT.md              # type: teilprozess     impacts template teilprozess --language de
    └── <arbeitsschritt>/
        └── CONTEXT.md          # type: arbeitsschritt  impacts template arbeitsschritt --language de

vorgaenge/<vorgang>/
├── CONTEXT.md                  # type: vorgang         impacts template vorgang --language de
└── <arbeitsschritt>/<versuch>/
    ├── input/
    └── output/
```

## Regeln

- Ein Blockskalarwert im Frontmatter darf keine alleinstehende `---`-Zeile enthalten.
- `<hauptprozess>`, `<teilprozess>`, `<arbeitsschritt>` und `<vorgang>` sind Slugs: `[a-z0-9]+(?:-[a-z0-9]+)*`. Die ID jeder `CONTEXT.md` ist `<type>:<ordnername>`.
- Der Application-Baum enthält nur `CONTEXT.md`-Dateien und Ordner. Jeder Hauptprozess hat mindestens einen Teilprozess, jeder Teilprozess mindestens einen Arbeitsschritt; ein Arbeitsschritt hat keine Unterordner.
- Arbeitsschritt-IDs sind in der ganzen Application eindeutig. Routen zeigen auf `arbeitsschritt:<slug>` oder `end:<slug>`; jeder Schritt erreicht ein Ende.
- `<versuch>` ist dreistellig, `versuch: 1` heißt `001`. Nur im Laufpfad erreichte Arbeitsschritte und Versuche besitzen Ordner.

Der Arbeitsschritt-Body enthält Prompt und Werkzeugaufrufvertrag. Gemeinsame Regeln, Promptbausteine und Dokumentvorlagen behalten ihre bestehende fachliche Heimat außerhalb dieses Baums und gelangen mit Herkunftsnachweisen als deklarierte Eingaben in den Versuch. Werkzeugimplementierungen bleiben Abhängigkeiten oder begründete Capabilities; konkrete Werte, Zwischenergebnisse und Ergebnisnachweise gehören zum Vorgang. Den Vertrag mit der Arbeitsschrittvorlage und `impacts-method.md`, Abschnitt „Compose an Arbeitsschritt“, aus der benannten Protokollrevision ausfüllen.

## Beispiel

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

Erforderliche Core-Strukturkonformität mit `impacts validate` im gewählten Umfang feststellen; fehlgeschlagene oder nicht ausgeführte Prüfbedingungen unter der gebundenen Werkzeuggrenze festhalten.
