# 6E-6 Preregistratie Errata

De oorspronkelijke preregistratie blijft byte-ongewijzigd.
Eerste run: 64 tests, 61 PASS, 3 FAIL; PHASE6E6_INITIAL_TESTS.json.

mixed_unit heeft in de frozen 6E-4-bronvalidator status unavailable, niet de
nieuwe adapterstatus facts_only. De test corrigeert uitsluitend die statusnaam.
In beide gevallen blijft plan_option=null en zijn betrouwbare historische feiten
apart beschikbaar. Geen toegestane handeling of medisch label veranderd.

De twee overige failures vonden dezelfde programmeerfout: ontbrekende optionele
context.options werd bij ingetrokken analyseconsent naar JSON gekloond.
Gecorrigeerd naar een lege optielijst; access_unavailable, geen voorstel of feiten.
