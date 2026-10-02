# Testmelding bij nieuwe opmerkingen

De Edge Function notify-new-comment verstuurt één e-mail wanneer in de testdatabase een nieuwe rij in public.comments wordt toegevoegd. Updates van bestaande opmerkingen worden genegeerd.

## Instellen in de testomgeving

1. Maak bij een e-maildienst met een geverifieerde afzender een API-sleutel. De implementatie gebruikt Resend.
2. Plaats uitsluitend als Supabase Edge Function-secret:
   - RESEND_API_KEY
   - COMMENT_EMAIL_FROM — de geverifieerde afzender
   - COMMENT_EMAIL_TO — het ontvangstadres
   - COMMENT_WEBHOOK_SECRET — een lange, willekeurige gedeelde sleutel
3. Publiceer de functie notify-new-comment met JWT-verificatie uitgeschakeld. De functie controleert vervolgens zelf de geheime header.
4. Maak in Supabase Dashboard > Database > Webhooks een webhook:
   - tabel: public.comments
   - gebeurtenis: INSERT
   - doel: de URL van notify-new-comment
   - extra header: x-comment-webhook-secret met de waarde van COMMENT_WEBHOOK_SECRET.
5. Plaats één proefopmerking en controleer dat precies één e-mail met [TEST] in het onderwerp aankomt.

De sleutel en adressen horen niet in Git, de website of een migratiebestand. Voor productie is een afzonderlijke configuratie nodig.
