<!-- Translation source: FIRST-WIN.md; sha256: 61ea81dd945299850320e8374e3ed7bc0235288a22a9573a5f60d80317482dc9 -->

# Einen nützlichen Angebotsentwurf vorbereiten

Für einen echten Fall die vorhandene Anfrage, Quellen und Dokumentvorlage verwenden. Die Vorbereitung an der bestehenden Fallheimat mit Quellenverweisen, offenen Fragen und nächster Handlung speichern.

Die [erste nützliche Vorbereitung](../../FIRST-WIN.md) zeigt vier Markdown-Dateien als synthetische Übung für diese Beziehungen. Legen Sie diese in einem eigenen Übungsordner an. Sie verwenden die bestehenden Rollen Katalog, Kunde, Anfrage und Angebotsvorlage aus dem synthetischen Unternehmensbeispiel. Die angefragten Identitäten, Mengen und Einheiten bleiben erhalten: C-1 fragt P-10, 2 Stück, und S-20, 12 Stunden, für O-1/Fassung 1 an. Es sind Beispieldaten; ein Preis, ein Lieferdatum und eine Freigabe werden nicht geliefert.

Der Auftrag für einen Agenten lautet:

> Lesen Sie CONTEXT.md und die drei verlinkten Quelldateien. Füllen Sie eine Kopie der Angebotsvorlage unter records/offer-o1/draft.md. Nennen Sie die Quelle jeder Aussage. Lassen Sie Preis, Summe und Lieferdatum offen. Halten Sie Rückfrage, zuständige Person und nächste Handlung beim Entwurf fest; verlinken Sie den Entwurf im Root-Router. Berechnen Sie keine unbelegten Beträge, behaupten Sie keine durchgeführte Prüfung und erfinden Sie keine Liefernachweise. Erteilen Sie keine Freigabe und versenden Sie nichts.

Die Übergabe benennt den tatsächlichen Fortschritt:

> Entwurf zur internen Durchsicht bereit: Preis und Lieferdatum sind noch offen, daher ist keine bepreiste Lieferzusage belegt. Nächster Schritt: anwendbare Preis- und Regelevidenz sowie die Lieferentscheidung der zuständigen Person beschaffen; ihre Quellen bei diesem Entwurf erhalten. Versand braucht eine eigene Erlaubnis.

Eine neue Sitzung startet nur bei `CONTEXT.md`, findet Entwurf und Quellen und benennt die offenen Punkte sowie die nächste Handlung. Das ist der erwartete Übungsablauf, kein bereits durchgeführter Agententest und keine bestätigte Kundenzusage. Entwurf, Quellen und Fragen bleiben an ihrer vorhandenen Heimat.

Der erste Gebrauch bleibt dateibasiert und braucht keine Installation. Als späteren, optionalen reproduzierbaren Techniknachweis kann die [synthetische Lieferwiederholung](../../06_evaluations/delivery-replay/CONTEXT.md) dienen. Sie verwendet deklarierte Beispieldaten und führt eine deterministische Berechnung aus; sie ist keine Voraussetzung für diesen Entwurf und simuliert keine Kundenaktion, Freigabe oder Geschäftswirkung.

Diese Grenze regelt der [Tooling stop](../impacts-architect/references/formwahl.md#tooling-stop).

**Flexibel im Denken. Unnachgiebig darin, was zählt.** Auslegung und Entwurf können fehlerhaft sein. Eine geprüfte Berechnung braucht die tatsächliche deterministische Ausführung nach der maßgeblichen Regel; eine menschliche Entscheidung kommt vom zuständigen Menschen. Unbekannte Fakten bleiben unbekannt.

Ist Git bei der Vorbereitung eines Git-gebundenen Vorgangs nicht verfügbar, bleiben Entwurf, Quellen, Fragen und Definitionsentwurf erhalten und fortsetzbar. Die Vorgangsvalidierung wurde nicht durchgeführt; die Vorbereitung bleibt ungebunden und ist kein validierter Vorgang. Nächster Schritt: an einem Rechner mit Git und Python-CLI den Hauptprozess-Vertrag samt erforderlichen Entwurfsfällen vervollständigen, den Hauptprozess am Root des Core-Arbeitsbereichs committen, den Vorgang anhand der [Vorgangsvorlage](../templates/vorgang.md) an den tatsächlichen committed Tree binden und `impacts validate` auf dem Arbeitsbereich ausführen. Das wirkliche Ergebnis erhalten und Fehler vor einer Behauptung validierter Bindung korrigieren. Keine Tree-ID, keinen Hash, keinen Ausführungseintrag und keine Freigabe erfinden. Strukturelle Validierung allein beweist weder ausgeführte Arbeit noch ein geprüftes Geschäftsergebnis.
