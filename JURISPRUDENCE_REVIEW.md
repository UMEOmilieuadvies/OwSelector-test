# Werkinstructie jurisprudentie beoordelen

Deze werkinstructie beschrijft de volledige route van een uitspraak uit Rechtspraak Open Data naar een eventueel zichtbare verwijzing in de Omgevingswet Zoeker.

> **Kernregel:** een gevonden kandidaat is nog geen juridische duiding. Alleen een afzonderlijk door een mens goedgekeurde artikelkoppeling kan later, na een aparte opdracht en controle, zichtbaar worden gemaakt.

## 1. Wat staat waar?

| Plaats | Functie | Zichtbaar voor bezoekers? |
| --- | --- | --- |
| `main` | Geteste testapplicatie en uitsluitend goedgekeurde koppelingen | Ja, op de testsite |
| `jurisprudence-review` | Werkdossier met kandidaten, beoordelingen en voortgang | Nee |
| `data/jurisprudence.json` | Alleen koppelingen die al afzonderlijk zijn gepubliceerd | Ja |
| `review-data/jurisprudence_candidates.json` | Alle gevonden kandidaten en de beoordeling per artikel | Nee |
| `JURISPRUDENTIE_BEOORDELING.md` | Leesbare beoordelingslijst met ECLI-links en context | Nee |
| `JURISPRUDENTIE_DEKKING.md` | Stand per regeling en periode | Nee |

Productie is niet betrokken bij deze werkinstructie. Een wijziging gaat altijd eerst aantoonbaar via test en vereist daarna een afzonderlijke opdracht voor productie.

## 2. Kandidaten verzamelen

1. Open in de **testrepository** GitHub **Actions**.
2. Kies **Verzamel jurisprudentiekandidaten voor beoordeling**.
3. Kies **Run workflow**.
4. Vul voor de eerste volledige ronde in:

   - begindatum: `2024-01-01`;
   - einddatum: `2024-12-31`;
   - maximaal aantal ECLI's: `500`;
   - **Ook buiten omgevingsrecht zoeken**: uit.

5. Start de workflow en wacht tot deze is afgerond.

De standaardzoekroute beperkt zich bewust tot het rechtsgebied omgevingsrecht. Dat houdt de resultaten beheersbaar. Alleen wanneer na beoordeling blijkt dat een aanvullende bronroute nodig is, wordt het vakje voor alle rechtsgebieden expliciet gebruikt.

### Een periode afmaken

De verzameling is hervatbaar. Start dezelfde workflow opnieuw met exact dezelfde begin- en einddatum totdat `JURISPRUDENTIE_DEKKING.md` vermeldt: **Verzamelstand: voltooid**. Eerder verwerkte ECLI's worden niet opnieuw opgehaald.

De workflow verwerkt één uitspraak tegen alle zeven opgenomen regelingen:

- Omgevingswet (OW);
- Besluit activiteiten leefomgeving (BAL);
- Besluit bouwwerken leefomgeving (BBL);
- Besluit kwaliteit leefomgeving (BKL);
- Omgevingsbesluit (OB);
- Omgevingsregeling (OR);
- Invoeringswet Omgevingswet (IWO).

Eén uitspraak kan daardoor meerdere regelingen en meerdere artikelen raken. Het dekkingsrapport telt zowel uitspraken als afzonderlijke artikelkoppelingen.

## 3. Het beoordelingsdossier openen

Na de workflow staan in de run-samenvatting links naar:

- **JURISPRUDENTIE_BEOORDELING.md**: de inhoudelijke werklijst;
- **JURISPRUDENTIE_INZICHTEN.md**: aantallen en beoordelingspatronen;
- **JURISPRUDENTIE_DEKKING.md**: voortgang en dekking per regeling.

Deze bestanden staan op de aparte branch `jurisprudence-review`. Open bij een kandidaat altijd eerst de officiële uitspraak via de ECLI-link. Beoordeel niet uitsluitend op de getoonde tekstcontext.

## 4. Beoordelen per artikelkoppeling

Beoordeel iedere regel **per combinatie van uitspraak, regeling en artikel**. Dus niet één oordeel voor de hele uitspraak. Een uitspraak kan bijvoorbeeld wel inhoudelijk over BAL artikel 3.1 gaan, maar slechts terloops BKL artikel 5.4 noemen.

Werk in `review-data/jurisprudence_candidates.json` op de branch `jurisprudence-review`. Wijzig uitsluitend het betreffende artikelobject:

```json
{
  "article": "3.1",
  "review_status": "goedgekeurd",
  "review_reason": "inhoudelijk_behandeld",
  "review_note": "De rechter beoordeelt de toepasselijkheid van dit artikel."
}
```

Gebruik één van deze statussen:

| Status | Wanneer gebruiken? |
| --- | --- |
| `goedgekeurd` | De uitspraak behandelt dit artikel inhoudelijk en de koppeling klopt. |
| `afgewezen` | De koppeling is onjuist of juridisch niet relevant voor dit artikel. |
| `later_bekijken` | De relevantie is nog niet betrouwbaar vast te stellen. |
| `te_beoordelen` | Nog niet inhoudelijk bekeken; dit is de beginstatus. |

Kies bij een beslissing altijd een reden:

| Reden | Toepassing |
| --- | --- |
| `inhoudelijk_behandeld` | Inhoudelijke behandeling van het actuele artikel. |
| `alleen_terloops_genoemd` | Alleen een verwijzing, zonder inhoudelijke behandeling. |
| `verkeerde_regeling` | De regeling is ten onrechte herkend. |
| `verkeerd_artikel` | Het artikelnummer is ten onrechte gekoppeld. |
| `historische_verwijzing` | Het gaat om oud recht of een voorganger, niet om het actuele artikel. |
| `onvoldoende_duidelijk` | Betekenis of koppeling is niet betrouwbaar vast te stellen. |

Gebruik `review_note` alleen voor een korte, concrete toelichting die een volgende beoordelaar helpt. Sla het bestand op in dezelfde branch met een duidelijke commit, bijvoorbeeld: `Beoordeel ECLI:NL:RVS:2024:1234`.

## 5. Kwaliteitscontrole vóór publicatie

Een goedgekeurde koppeling wordt niet automatisch zichtbaar. Controleer vóór een voorstel tot publicatie ten minste:

1. ECLI-link opent de officiële uitspraak.
2. Uitspraak en artikel zijn inhoudelijk gekoppeld.
3. De regeling is de actuele regeling; bij oud recht is de reden `historische_verwijzing` gebruikt, tenzij een expliciete en gecontroleerde transponering is vastgelegd.
4. De beslissing is op artikelniveau vastgelegd, ook als dezelfde uitspraak nog andere artikelen raakt.
5. Eventuele samenvatting is feitelijk, kort en zonder eigen juridische conclusie.

Pas daarna kan een afzonderlijke opdracht worden gegeven om uitsluitend de goedgekeurde koppelingen van `jurisprudence-review` naar de testapplicatie over te nemen. Dat is een aparte stap met tests, releasenotitie en expliciete publicatieopdracht.

## 6. Wat gebeurt er niet automatisch?

- Kandidaten worden niet automatisch in de zoeker geplaatst.
- Een terugkerend patroon in `JURISPRUDENTIE_INZICHTEN.md` wijzigt geen zoekregels.
- Afwijzingen verwijderen niets uit de openbare jurisprudentie-index.
- Testgegevens, testlinks en testbeoordelingen gaan niet vanzelf naar productie.

## 7. Praktische volgorde voor 2024

1. Maak de 2024-verzameling af door batches van 500 te draaien totdat het dekkingsrapport `voltooid` zegt.
2. Beoordeel eerst kandidaten met een duidelijke context en een beperkt aantal artikelkoppelingen.
3. Leg twijfelgevallen vast als `later_bekijken`, niet als goedkeuring.
4. Maak pas na een eerste beoordeelde set een voorstel voor een kleine, controleerbare testpublicatie.
5. Evalueer dan pas of uitbreiding naar andere jaren of rechtsgebieden nodig is.
