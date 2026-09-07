# Package 6E-0 Compatibility Matrix

Frozen referentie: bc6308fbf0f914b04c7faa711219d9ae46e9cbe3.
Alle uitspraken over huidig gedrag zijn op gelezen bron/retained bewijs gebaseerd.
Geen live database- of Edgecontrole uitgevoerd in 6E-0.

| Frozen contract | Bestaande autoriteit | Offline voorstel | Compatibiliteit / gate |
| --- | --- | --- | --- |
| 6A auth, volwassenheid, AI entitlement, consent | Server-side authority, niet clienttekst | Alleen synthetische boolean snapshot in access() | Grenzen behouden, geen echte adapter. Snapshot mag nooit serverautorisatie vervangen |
| 6A begrensde action proposals | Beperkte actiontypes; uitvoering eigen gate | Alle acties false/[] | Compatibel in doel; geen proposal of uitvoering toegevoegd |
| 6B provider/privacy/kosten | Real-member external processing niet vrijgegeven | Geen netwerk/provider/import of secrettoegang in kern/harness | Geen activatie of privacygoedkeuring; bestaande providerflags onaangeraakt |
| 6C request-safety | phase6c-handler.ts classifyPhase6cSafety, regel 138: clear / hard_stop | Vijf voorlopige niveaus plus aparte onzekerheid | NIET drop-in compatibel. R0 is geen medische clear; R1-R4 zijn geen algemene featureban |
| 6C gewone chat / eigen historie | Bestaande private-chatconsent, own-user autorisatie en chatroutes | Health-onafhankelijke functie/history-snapshot | Geen appblokkade toegevoegd, maar geen huidige gate gewijzigd |
| 6C herstelintentie | phase6dRecoveryIntent, regel 151; intentie biedt review, schrijft geen safetyvrijgave | Actuele eigen zelfrapportage met revisie in geheugen | Geen stille vervanging van frozen recovery-RPC; ernstige/onduidelijke herstelvoorwaarden OPEN |
| 6D analyses | Apart ai_analysis-consent; eigen gestructureerde brondata, geen private chat; actions=[] | Feitenallowlist en waarschuwing, geen gepersonaliseerd advies | D3 NIET direct compatibel met huidige safety_hard_stop voor nieuwe analyses. Nieuwe bounded-facts route vereist apart ontwerp/review, geen SQL-gate weghalen |
| 6D herstel | Drie expliciete bevestigingen, member/revision/lock gebonden; nieuw signaal maakt oud herstel ongeldig | Alleen synthetic self_report; lage niveaus reviewcandidate, R3/R4/open context review required | Owner D4 is productrichting, niet autorisatie om huidige bevestigingen te reduceren |
| 6D worker/inbox | Consent/entitlement/owner-scope, idempotentie, read-only, geen provider/action | Alleen in-memory request-dedupe en bounded viewmodel | Geen cron, worker, scheduling, databasejob of automatic analysis-trigger gewijzigd |
| 6D result/history | Retained 90d results / 180d minimale metadata onder eigen contract | D5 aparte safetysoorten, geen chat/analysis retentieadapter | Niet onderling uitwisselbaar; toekomstige policy/migratie afzonderlijk toetsen |
| 6D trainergrens | Geen private chat/safety delen op basis van algemene summaryconsent | trainer_sharing=false | Geen trainerrol, link, consent of notification |
| 6D UX/thema | Accepted avatar, chat, dashboard, settings, system/light/dark | Geen presentatiebestanden aangeraakt | Byte-identiteit tegen frozen Git en 56 gepubliceerde assets is gate |
| 6D migration chain | Retained 31/31; lokale pg_cron-beperking historische gate | Geen SQL/migrations en geen lokale DB nodig | 31 lokale SQL-bronnen ongewijzigd; live 31/31 niet opnieuw gemeten |

## Verplichte Scheiding Voor Een Later Ontwerp

1. Laat bestaande serverautorisatie beslissen wie welke eigen gegevens mag zien.
2. Definieer een afzonderlijk strikt facts-only contract; claim geen volledige normale analyse.
3. Maak persoonlijk advies een expliciete niet-vrijgegeven categorie, niet vrije tekst achter een waarschuwing.
4. Houd automatische uitvoering en providerverwerking uit.
5. Maak herstel zichtbaar als zelfrapportage, met ernstige/ontbrekende context apart.
6. Pas geen enum/SQL/RPC aan zonder een afzonderlijke owneropdracht en relevante review.

Exacte frozen bronverwijzingen:
supabase/functions/youri-ai/phase6c-handler.ts,
supabase/functions/youri-ai/phase6d-handler.ts,
assets/phase6c-private-ai-chat.js, assets/phase6d-analysis-inbox.js,
assets/phase6d-owner-settings.js en de ongewijzigde canonical supabase/migrations.
De testharness leest die bronnen alleen voor isolatie; er wordt niets aan gekoppeld.
