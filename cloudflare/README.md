# Testbackend zonder Supabase

De testsite gebruikt een Cloudflare Worker met D1 voor publieke opmerkingen. D1 is SQLite-compatibel; de database is niet rechtstreeks publiek bereikbaar.

## Eenmalig bij Cloudflare

1. Maak een Cloudflare-account en installeer Wrangler op een eigen beheermachine.
2. Meld aan met `wrangler login`.
3. Maak de testdatabase: `wrangler d1 create owselector-test-comments`.
4. Zet de ontvangen `database_id` in `wrangler.toml`.
5. Pas `ALLOWED_ORIGIN` aan wanneer de testsite een andere URL krijgt.
6. Stel een geheim in: `wrangler secret put RATE_LIMIT_SECRET`.
7. Pas het schema toe: `wrangler d1 execute owselector-test-comments --remote --file=cloudflare/schema.sql`.
8. Publiceer: `wrangler deploy`.
9. Zet de Worker-URL als GitHub Actions-variabele `TEST_COMMENTS_API_URL` en publiceer daarna de testsite.
10. Voeg de GitHub-secrets `CLOUDFLARE_API_TOKEN` en `CLOUDFLARE_ACCOUNT_ID` toe; start daarna handmatig de workflow **Deploy test comments API**.

## Beheer en backup

Opmerkingen worden in de Cloudflare D1-console beheerd. Maak dagelijks een D1-export buiten GitHub. Bestaande testopmerkingen worden pas na een afzonderlijke migratieopdracht gekopieerd. Maak eerst lokaal `comments-import.sql` met `tools/export_comments_for_d1.py` en voer dat daarna eenmalig uit met `wrangler d1 execute ... --remote --file=cloudflare/comments-import.sql`. Het bestaande testproject blijft tot die controle beschikbaar.
