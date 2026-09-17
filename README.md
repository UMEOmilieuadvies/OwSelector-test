# OwSelector — Omgevingswet Zoeker 0.01

GitHub Pages-uitgave van Omgevingswet Zoeker 0.01.

De website wordt voorlopig alleen handmatig gebouwd met GitHub Actions. Tijdens de build worden de zes officiële regelingen opgehaald via de bestaande KOOP/BWB-downloader en omgezet naar de legal graphs die de browser gebruikt. De gepubliceerde website bevat alleen statische HTML, CSS, JavaScript en JSON.

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
