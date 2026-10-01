# OwSelector — Omgevingswet Zoeker 1.01k

GitHub Pages-uitgave van Omgevingswet Zoeker 1.01k.

De website wordt bij iedere push en dagelijks met GitHub Actions gebouwd. Tijdens de build worden de zes officiële regelingen opgehaald via de bestaande KOOP/BWB-downloader, met de dag van de build als peildatum, en omgezet naar de legal graphs die de browser gebruikt. De dagelijkse build publiceert alleen als de inhoud is gewijzigd. De gepubliceerde website bevat alleen statische HTML, CSS, JavaScript en JSON.

Iedere officiële externe XML-verwijzing wordt als link getoond. Een verwijzing naar een van de zes opgenomen regelingen opent gericht in kolom 2. Andere Nederlandse BWB-regelingen openen op Wetten.nl, EU-regelgeving op EUR-Lex en overige externe bronnen in een nieuw tabblad. De build maakt hiervoor `data/external_refs.json` als beheeroverzicht.

## Regelingen

- Omgevingswet (OW)
- Besluit activiteiten leefomgeving (BAL)
- Besluit bouwwerken leefomgeving (BBL)
- Besluit kwaliteit leefomgeving (BKL)
- Omgevingsbesluit (OB)
- Omgevingsregeling (OR)

## Publicatie

De workflow staat in `.github/workflows/pages.yml`. GitHub Pages moet voor deze repository ingesteld zijn op **GitHub Actions** als publicatiebron.

De zelfstandige Windows-release blijft los van deze Pages-publicatie; de viewerfunctionaliteit is gebaseerd op V550.

## Beheer van versies

Voer vóór iedere wijziging `python tools/release.py groot` of `python tools/release.py klein` uit, met ten minste één `--note`. Voeg voor opgeloste opmerkingen ook `--issue ID` toe. Het hulpmiddel werkt `VERSION`, de zichtbare versie, `release.json` en `RELEASE_NOTES.md` bij.

Na een succesvolle Pages-uitgave registreert GitHub Actions de versie en de opgeloste opmerkingen in Supabase. Dit vereist de GitHub-secrets `SUPABASE_URL` en `SUPABASE_SERVICE_ROLE_KEY`; de service-role sleutel wordt nooit in de website opgenomen.

Bij een doorgevoerde opmerking kan de beheerder in de kolom `admin_note` in de Supabase-tabel `comments` een korte toelichting invullen. Die toelichting wordt op de website onder de opmerking getoond.
