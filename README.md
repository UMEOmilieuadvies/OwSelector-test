# OwSelector — Omgevingswet Zoeker V550

GitHub Pages-uitgave van Omgevingswet Zoeker V550.

De website wordt bij iedere push naar `main` gebouwd met GitHub Actions. Tijdens de build worden de zes officiële regelingen opgehaald via de bestaande KOOP/BWB-downloader en omgezet naar de legal graphs die de browser gebruikt. De gepubliceerde website bevat alleen statische HTML, CSS, JavaScript en JSON.

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
