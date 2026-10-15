# Pre-productie

De testomgeving is de pre-productieomgeving van Omgevingswet Zoeker. Zij heeft een eigen repository, GitHub Pages-site, Supabase-project, database, sleutels en omgevingsinstellingen.

## Vaste poort

Elke publicatie naar de pre-productiesite moet slagen voor:

1. syntaxiscontrole van de clientcode;
2. controle dat productie-Supabase niet in testcode voorkomt;
3. opbouw en controle van de zes officiële regelinggrafen;
4. een browser-starttest op de gepubliceerde testsite: geen browserfout, zes regelingen geladen en een actief zoekveld.

Een mislukte pre-productietest blokkeert overdracht naar productie.

## Overdracht naar productie

Productie ontvangt alleen een expliciet goedgekeurde, geslaagde kandidaat. Test- en productieconfiguratie blijven strikt gescheiden. Productie wordt nooit vanuit een testworkflow gepubliceerd en publicatie van programmatuur verloopt alleen via de handmatige productie-workflow na expliciete opdracht.
