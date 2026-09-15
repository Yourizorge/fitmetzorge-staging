# 6E-9 Owner Retest Window

Status: OPEN / AWAITING PHYSICAL OWNER RETEST / NOT OWNER-ACCEPTED.
Baseline c7b44357a5e56b86a9b0a38b46e4739aeacf7a07.

The owner approved exactly three Gmail plus aliases and the narrow demo-login
compatibility change. No server authority, role model, migration, Edge source or
functional workflow contract changes. All three identities must be NEW. Existing
identities at these addresses cause a stop, never an update or role conversion.

## Provisioning And Bounds

The isolated owner-window runner reuses the existing fixed-project broker,
Auth password login, proof-secret gate, private subjects, server roles and existing
published browser suite. It creates three profiles, two workspaces and synthetic
workflow records only. Route B is first tested as an ordinary newly authenticated
principal WITHOUT a workspace, then enrolled. No real account is used for denial tests.

Expiry is fixed once, at database time plus 23 hours 59 minutes, never extended by
login, refresh, commands or mail delivery. The existing 24-hour constraint is unchanged.
Expired-session denial is exercised by temporarily expiring only these two new
workspaces and restoring their ORIGINAL deadline. No migration or expiry bypass.

Only coach-backend-demo/app.js changes publicly: the login allowlist is exactly the
three approved aliases. Authorization remains server-derived from auth.uid(), sessions,
trusted profile role/link, subject membership, consent, versions, proof and expiry.
The global test switch is enabled only with exactly these two workspace memberships;
it does not enroll other users. No editable metadata grants access.

## Secrets And Mail

Passwords are random and held only in process memory for verification. Only three
standard recovery emails are requested, after the checks, using the existing staging
password-setup route. No passwords, tokens, session data or recovery links are logged
or written. The existing Auth recovery TTL is 3600 seconds; this is separate from the
workspace deadline. No SMTP/provider settings change. Receipt records mail attempts,
not delivery claims. Owner receipt and physical phone use remain unverified until reported.

On success the broker explicitly retains fixtures/proof. On failure it disables access
but does not delete fixtures. The nonsecret receipt is kept in ignored
supabase/.temp/phase6e9-owner-window.json for exact-ID cleanup after the owner test or
expiry. No automatic cleanup on successful process exit. Server expiry does not imply
physical deletion; cleanup remains a separate bounded operation, never a broad delete.

## Verification And Owner Flow

Preexisting row fingerprints are compared excluding ONLY the three newly created profile
IDs and the two new synthetic audit/notice workspaces. All other public/AI/legacy business
tables remain included. Entire migration records are compared, not just their count.
Official migration list and db push --dry-run are also required.

The existing published browser matrix exercises real test Auth/Edge/RLS: Route A
member acceptance, trainer approval, separate apply; Route B independent confirm/apply;
restore as a new version, explicit lost-response retry, refresh and relogin. All inputs
are synthetic. Browser layout checks emulate mobile/tablet/desktop, not a physical phone.

Audit history is NOT reset after internal tests. The owner receives an A restore proposal
awaiting member acceptance and a B candidate awaiting confirmation. This uses the existing
workflow; it does not fabricate a new initial version. An A rejection/block is terminal
in this existing design: test it LAST. Refresh does not undo it or create a fresh proposal.
Stale version testing uses two pages: update one, then attempt a decision from the older
page. No client-side admin/injection controls are added.

1725 existing contract/frozen regression tests passed before opening. The live window
receipt and final delivery section record actual subsequent outcomes. None implies
owner acceptance/freeze, live AI permission or a start of 6E-10.

## Delivery Receipt - 2026-09-15

- Implementation/published runtime: 05bd11ef25c8972d88e71f374ef422f22cc18463.
- Pages run 34953425774: success. All 80 public assets match Git; 76 prior assets
  remain byte-identical. Of the four backend-demo files, only app.js differs from
  c7b4435, by the exact alias allowlist. All 187 private source/test paths return 404.
- 1725 contract/frozen tests + 10 alias checks PASS; 14 live groups PASS;
  200 published browser checks / 72 layouts / zero errors. Physical phone untested.
  Existing public Auth/password recovery mock suite rerun: 88/88 PASS, no live mail.
- 68 preexisting-cohort table fingerprints unchanged, including the original 66
  business tables and two synthetic audit/notice tables excluding only new fixtures.
- 34/34 CLI migration identities match; all migration record hashes unchanged.
  db push --dry-run --skip-vault is empty before and after opening.
- Three NEW Auth identities, three NEW profiles, two isolated workspaces retained.
  No existing profile/account was converted. B has no trainer. No real account was
  logged into for the ordinary-user denial test; B was tested before enrollment.
- Expiry: 2026-09-16 09:39:58.660473 UTC, Wednesday 16 September 2026
  11:39:58.660473 Europe/Amsterdam (CEST/UTC+2). Expiry is server enforced.
- Three recovery requests accepted on 2026-09-15 around 09:42:32 UTC / 11:42:32 CEST.
  The links last one hour. Delivery/click/password setup remains owner-observed.
- No provider calls, AI costs, production action, migration or Edge code deployment.
  The existing proof secret was set for this window; this can increment Supabase
  function deployment counters without changing function source. No proof is public.

## Eenvoudige Telefoontest

Open https://yourizorge.github.io/fitmetzorge-staging/coach-backend-demo/?lang=nl
Gebruik niet je gewone stagingaccount. Stel via elk van de drie mails een eigen
wachtwoord in. Controleer steeds het Aan-adres; het gaat om drie aparte accounts.
De bestaande instelpagina stuurt terug naar inloggen. Ga daarna terug naar de demokoppeling,
niet naar het gewone dashboard. Deel geen wachtwoorden of links in de chat.

1. Begin met zorgeyouri+6e9-a-lid@gmail.com. Bovenaan moet Route A / Lid staan.
   A staat op v6; het klaargezette terugzetvoorstel naar het oorspronkelijke v3
   wacht op jouw acceptatie. Dit is het behouden resultaat van de interne tests.
2. Klik Voorstel accepteren. Het schema blijft v6. Trainerknoppen zijn niet bruikbaar.
3. Klik Uitloggen. Log in met zorgeyouri+6e9-a-trainer@gmail.com.
   Controleer Route A / Trainer. Klik Goedkeuren / Trainer. Nog steeds geen toepassing.
4. Klik afzonderlijk Wijziging toepassen. Er verschijnt een NIEUWE v7; v3-v6 blijven
   bewaard. Ververs of log opnieuw in: v7 blijft. Dubbel tikken geeft geen tweede versie.
5. Voor terugzetten: Uitloggen, weer A-lid. Onder Bewaarde schemaversies klik
   Terugzetvoorstel maken bij v6. Herhaal accepteren, uitloggen, trainergoedkeuring
   en afzonderlijk toepassen. Resultaat v8, niet een overschrijving van v6.
6. Uitloggen. Log in met zorgeyouri+6e9-b-lid@gmail.com. Controleer Route B / Lid.
   Bekijk/bewerk het klaargezette concept via Training, Voeding en Herstel.
   Klik Plan bevestigen en daarna Planversie activeren. v3 wordt een nieuwe v4.
   Er is nergens een trainergoedkeuringsstap. Ververs en log opnieuw in: status blijft.
7. Bij B maak je via Terugzetvoorstel bij een oudere versie opnieuw een concept;
   Plan bevestigen plus Planversie activeren maakt weer een nieuwe versie.

Versieconflict: klik bij B eerst Opnieuw bewerken wanneer het plan al actief is.
Open dezelfde B-login in twee tabbladen en laat beide dat concept laden. Wijzig in
tab 1 via Herstel het Slaapdoel en klik Vervangen. Klik in het oude tab 2
op Plan bevestigen. Verwacht de melding dat bron/versie is gewijzigd, geen toepassing.
Klik Actuele versie laden. Een tab kan apart inloggen vereisen; nooit tokens kopieren.

Afwijzen: B > Opnieuw bewerken > Afwijzen. Activeren blijft geblokkeerd; Opnieuw
bewerken kan een nieuw concept openen. Test A-afwijzing/blokkering ALS LAATSTE:
een nieuw A-terugzetvoorstel kan door het lid met Afwijzen / Lid worden afgewezen,
of na lidacceptatie door de trainer met Afwijzen / Trainer of Blokkeren / Trainer.
Dit is in het bestaande contract een eindstatus; verversen maakt het niet ongedaan.

Meld na afloop: ontvangst/instellen van de drie mails, Route A geslaagd ja/nee,
Route B geslaagd ja/nee, behoud na refresh/login, conflict/afwijzing/terugzetten en
eventuele knop of foutmelding. Geen inloggeheimen meesturen. Daarna pas ownerbeoordeling
en afzonderlijke cleanup; geen automatische freeze of 6E-10.

Official sources checked before Auth/access work:
[Auth recovery](https://supabase.com/docs/reference/javascript/auth-resetpasswordforemail),
[RLS](https://supabase.com/docs/guides/database/postgres/row-level-security),
[Changelog](https://supabase.com/changelog).
