---
type: DomainModel
x_tables:
  customers:
    resource: ../records/customers.csv
    primary_key: [customer_id]
  products:
    resource: ../records/products.csv
    primary_key: [product_id]
  services:
    resource: ../records/services.csv
    primary_key: [service_id]
  agreements:
    resource: ../records/agreements.csv
    primary_key: [agreement_id, version]
    foreign_keys:
      - fields: [customer_id]
        target: customers
        references: [customer_id]
        meaning: contracting_customer
  agreement_items:
    resource: ../records/agreement_items.csv
    primary_key: [item_id]
    foreign_keys:
      - fields: [agreement_id, agreement_version]
        target: agreements
        references: [agreement_id, version]
        meaning: agreed_under_version
      - fields: [product_id]
        target: products
        references: [product_id]
        nullable: true
        meaning: agreed_product_kind
      - fields: [service_id]
        target: services
        references: [service_id]
        nullable: true
        meaning: agreed_service_kind
    exactly_one: [product_id, service_id]
---

# Fachliche Bedeutung und lokale Lesekonvention

`resource` ist relativ zu dieser Modelldatei; `target` bezeichnet einen Eintrag
in `x_tables`; `fields` und `references` entsprechen sich positionsweise.
`exactly_one` verlangt genau einen gefüllten Produkt-/Servicebezug je Position.
IDs sind Zeichenketten, Mengen Dezimalzahlen, Fassungsnummern kanonische
positive Ganzzahlen. Leere CSV-Werte sind nur an optionalen Stellen zulässig.

Jede Vertragszeile bezeichnet eine Fassung mit ihrem vertraglichen Kunden.
Produkt und Service bezeichnen Katalogarten, keine konkreten gelieferten Objekte.
`quantity` ist der vereinbarte Positionsumfang; Lieferung, Verbrauch, Preis und
monatliche Wiederholung lassen sich daraus nicht ableiten.
Mengen sind endlich und nicht negativ. Für die hier gezeigten Katalogarten gilt
`Stück` bei P-10 und `Stunde` bei S-20; eine Umrechnung ist nicht definiert.

Die Gültigkeitsdaten sind ISO-Daten: `valid_from` einschließlich, `valid_to`
ausschließlich. Leeres `valid_to` bedeutet bestätigtes offenes Ende, nicht
unbekannt. Mehrere gültige Verträge eines Kunden bleiben mehrere Ergebnisse.
Ungeklärte Überlappungen von Fassungen desselben Vertrags sind ein Klärungsbedarf;
„höchste Version gewinnt“ ist hier keine Regel.
