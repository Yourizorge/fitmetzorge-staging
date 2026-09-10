# 6E-4 Preregistratie

Vastgelegd VOOR implementatie. Baseline adfff180e30093abc2febe601a3dead123afe36b.
T1-T4 zijn geaccepteerde ontwikkelrichting, geen acceptatie van de resultaten.

129 bron-/context-/toegangsgevallen en 41 taalgevallen liggen vast in
_offline/phase6e4/preregistered-cases.json en language-cases.json.
Bronverwachtingen betreffen eigen identiteit, actuele geldigheid, exacte versie,
trainerbevoegdheid en setgrenzen, ontbrekende gegevens, kg/kg en lb/lb zonder conversie,
RIR/RPE/null/0 en context-/hervattingsgrenzen. Geen medisch niveau wordt nieuw toegekend.
Taalvoorbeelden bevatten volledige review-parafrases, onbekende resttekst,
ontkenning, historie, educatie, citaat, technische uitval en gemengde echte klachten.

Aanvullend te bewijzen: input-immutabiliteit; herhaalde/verkeerde contextbinding;
O5 vlak voor/op/na 30 dagen, eerder verval, retry/statuswisseling, nieuwe meldingen;
bronverlies zonder reconstructie; historische 6E-3-output byte-ongewijzigd na een
later schema/doel; geen authority/consent-bypass of leakage; offline VM-isolatie.
Nieuwe tests mogen tekortkomingen vinden; verwachtingen niet stilzwijgend aanpassen.
Bekende missers apart registreren en niet als herkenningssucces tellen.

De oorspronkelijke 6E-3-beperking blijft historisch waar; de nieuwe adapter moet
het verbeterde gedrag aantoonbaar testen zonder frozen bronnen te wijzigen.
Geen live data, provider, runtime- of databasewijziging. Geen deskundige validatie.

Voor implementatie gecorrigeerde fixturetijd: de plansnapshot wordt vastgelegd
NA de expliciete doelkoppeling (clock-800 versus link clock-900). De eerste
fixture had plan-capture clock-1000, dus ten onrechte eerder dan zijn eigen link.
Alle 129 verwachte uitkomsten en 41 taalgevallen blijven gelijk. Beide
preregistratieversies blijven zichtbaar in Git; geen test achteraf groen gemaakt.
