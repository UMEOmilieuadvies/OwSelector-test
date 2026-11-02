# Pre-productie

De testomgeving is de pre-productieomgeving van Omgevingswet Zoeker. Zij heeft een eigen repository, GitHub Pages-site, Supabase-project, database, sleutels en omgevingsinstellingen.

## Vaste poort

Elke publicatie naar de pre-productiesite moet slagen voor:

1. syntaxiscontrole van de clientcode;
2. controle dat productie-Supabase en paden buiten de testmap niet in de testopbouw voorkomen;
3. opbouw en controle van de zeven officiële regelinggrafen;
4. een browser-starttest op de gepubliceerde testsite: geen browserfout, het geconfigureerde aantal regelingen geladen en een actief zoekveld.

## Tijdelijke bestanden

Lokale bouw-, cache- en beoordelingsbestanden staan uitsluitend onder de testmap, in expliciet uitgesloten mappen zoals `.cache`, `_site` en `review`. Zij worden niet gecommit. De werkruimtecontrole blokkeert harde Windows-paden en relatieve paden die uit de testmap kunnen ontsnappen.

Een mislukte pre-productietest blokkeert overdracht naar productie.

## Overdracht naar productie

Productie ontvangt alleen een expliciet goedgekeurde, geslaagde kandidaat. Test- en productieconfiguratie blijven strikt gescheiden. Productie wordt nooit vanuit een testworkflow gepubliceerd en publicatie van programmatuur verloopt alleen via de handmatige productie-workflow na expliciete opdracht.
