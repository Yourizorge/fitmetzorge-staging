# 6E-6 Preregistratie

Vastgelegd VOOR uitvoerbare 6E-6-code. Synthetische fixtures; geen medische norm.
Begin-HEAD: 8b994e1c355e1c3a6145a91546936d42123b20b0.
6E-5-acceptatie: 4392d3b; 106 frozen bronnen en 60 runtime-assets blijven gelijk.

57 bron/progressie/contextgevallen, 33 review/transactiegevallen,
7 facts-only controles; exacte ID's en uitkomsten in
_offline/phase6e6/preregistered-cases.json.
Scenario's: squat 2x8 op 55 -> 2x9 op 55; row 2x10 op 30 -> 2x8 op 32.5;
shoulder press target 2x8 op 20, actual 7 -> bestaand target behouden.
ALLE getallen komen uit expliciete TEST-trainerregels, niet echt coachingbeleid.

Nieuwe bron: versiegebonden rulebook met expliciete min/max reps, reps-stap,
gewichtsstap, sets en onafhankelijke RIR/RPE-voorwaarden. Per oefening OF exact
brongebonden type; meer dan een passende regel blokkeert, geen impliciete voorrang.
Beschikbare gewichten blijven expliciet; off-grid of overschrijding geeft geen rounding.
Frozen 6E-5 rekent uitsluitend de geldig opgeloste expliciete regels door.

Toepassing alleen in memory, na apart lid/trainerakkoord en trainer-only apply.
Storing VOOR commit moet de gehele aggregate ongewijzigd laten; audit, vorige plan,
bronversies en idempotency horen bij dezelfde gesimuleerde commit.
Geen bewijs van live duurzame database-atomiciteit of echte trainerherkomst.

Negatieve contextverwachtingen volgen de bestaande frozen contracten; geen nieuwe
medische labels. Bekende taalobservaties blijven beperkingen, geen herkenningssucces.
Eventuele technische verwachte statusnaam-correctie wordt expliciet gelogd;
blokkade versus toestemming mag niet stilzwijgend worden veranderd.
