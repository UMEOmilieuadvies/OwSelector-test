# Jurisprudentie beoordelen in GitHub

De testvoorziening verzamelt alleen **kandidaten** uit Rechtspraak Open Data. De
publieke testsite leest deze gegevens niet. Daardoor verandert er niets in de
zoeker totdat een kandidaat inhoudelijk is gecontroleerd en in een afzonderlijke
publicatiestap is verwerkt.

## Starten

Ga in GitHub naar **Actions** en kies *Verzamel jurisprudentiekandidaten voor
beoordeling*. Kies **Run workflow**. De standaardzoekroute is omgevingsrecht;
voor uitzonderlijke zaken kan aanvullend alle rechtsgebieden worden gekozen.

## Beoordelen

Na afloop bevat het overzicht van de run een link naar
`JURISPRUDENTIE_BEOORDELING.md` op de aparte tak `jurisprudence-review`. Per
kandidaat staan daar de ECLI, een link naar de officiële uitspraak, de mogelijke
regeling- en artikelkoppeling en de gevonden context.

Een kandidaat betekent uitsluitend dat regeling en artikel in dezelfde passage
zijn aangetroffen. Controleer daarom altijd de officiële uitspraak. Leg de
beslissing vast in `review-data/jurisprudence_candidates.json` met één van deze
waarden:

- `goedgekeurd` — inhoudelijk relevant en correct gekoppeld;
- `afgewezen` — niet relevant of onjuist gekoppeld;
- `later_bekijken` — nog onvoldoende duidelijk;
- `te_beoordelen` — nog niet beoordeeld.

Alleen kandidaten met `goedgekeurd` mogen later, na een aparte controle en
opdracht, worden toegevoegd aan de zichtbare jurisprudentie van de testsite.

## Scheiding met de testsite

- `main`: geteste, zichtbare testapplicatie en uitsluitend gecontroleerde
  jurisprudentie;
- `jurisprudence-review`: online werkdossier, voortgang en kandidaten;
- productie: niet betrokken bij deze voorziening.
