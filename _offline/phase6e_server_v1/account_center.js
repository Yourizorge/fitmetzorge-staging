'use strict';
const FMZAccountCenter = (() => {
  const words = {
    account: ['Account en toegang', 'Account and access', 'Konto und Zugang'],
    clients: ['Cliëntwerkruimtes', 'Client workspaces', 'Klientenbereiche'],
    workspace: ['Werkruimte', 'Workspace', 'Arbeitsbereich'],
    assigned: ['Toegewezen werkruimtes', 'Assigned workspaces', 'Zugewiesene Arbeitsbereiche'],
    noWorkspaces: ['Geen toegewezen werkruimtes beschikbaar.', 'No assigned workspaces available.', 'Keine zugewiesenen Arbeitsbereiche verfügbar.'],
    noClients: ['Geen gekoppelde cliëntwerkruimtes beschikbaar.', 'No linked client workspaces available.', 'Keine verknüpften Klientenbereiche verfügbar.'],
    workspace_denied: ['Dit account heeft geen toegang tot een toegewezen werkruimte. Gebruik het toegewezen account of laat de bestaande koppeling controleren.', 'This account cannot access an assigned workspace. Use the assigned account or have the existing link checked.', 'Dieses Konto hat keinen Zugang zu einem zugewiesenen Arbeitsbereich. Zugewiesenes Konto verwenden oder bestehende Verknüpfung prüfen lassen.'],
    accessTitle: ['Toegangsstatus', 'Access status', 'Zugangsstatus'],
    source_missing: ['Geen geverifieerde toegangsbron aangeleverd. Abonnement en proefperiode zijn onbekend.', 'No verified access source supplied. Subscription and trial status are unknown.', 'Keine verifizierte Zugangsquelle vorhanden. Abonnement und Testzeitraum sind unbekannt.'],
    source_invalid: ['De toegangsbron kan niet worden beoordeeld. Er wordt geen toegangsniveau getoond.', 'The access source cannot be assessed. No access tier is shown.', 'Die Zugangsquelle kann nicht bewertet werden. Keine Zugangsstufe wird angezeigt.'],
    readOnlyAccess: ['Alleen-lezen status van een geverifieerde synthetische bron.', 'Read-only status from a verified synthetic source.', 'Schreibgeschützter Status einer verifizierten synthetischen Quelle.'],
    tier: ['Niveau volgens bron', 'Tier from source', 'Stufe laut Quelle'],
    free: ['Free', 'Free', 'Free'], pro: ['Pro', 'Pro', 'Pro'], ai: ['AI', 'AI', 'KI'],
    source: ['Bron', 'Source', 'Quelle'],
    assessed: ['Beoordeeld op', 'Assessed at', 'Bewertet am'],
    trial: ['Proefperiode', 'Trial', 'Testzeitraum'],
    trial_active: ['Actief volgens bron', 'Active according to source', 'Laut Quelle aktiv'],
    trial_scheduled: ['Nog niet gestart volgens bron', 'Not yet started according to source', 'Laut Quelle noch nicht begonnen'],
    trial_expired: ['Verlopen volgens bron', 'Expired according to source', 'Laut Quelle abgelaufen'],
    trial_revoked: ['Ingetrokken volgens bron', 'Revoked according to source', 'Laut Quelle widerrufen'],
    noTrial: ['Geen proefperiode in deze bron.', 'No trial in this source.', 'Kein Testzeitraum in dieser Quelle.'],
    starts: ['Begin volgens bron', 'Start from source', 'Beginn laut Quelle'],
    ends: ['Einde volgens bron', 'End from source', 'Ende laut Quelle'],
    fallback: ['Niveau op het broneindmoment', 'Tier at the source end time', 'Stufe zum Endzeitpunkt der Quelle'],
    fallbackNote: ['Bepaald met dezelfde bronversie; latere bronwijzigingen kunnen de uitkomst wijzigen.', 'Calculated from the same source version; later source changes can change the outcome.', 'Aus derselben Quellversion berechnet; spätere Änderungen können das Ergebnis ändern.'],
    retained: ['Historie blijft behouden volgens deze toegangspolicy.', 'History is retained under this access policy.', 'Der Verlauf bleibt gemäß dieser Zugangsregel erhalten.'],
    noActivation: ['Geen automatische verlenging, betaling of externe AI ingeschakeld.', 'No automatic renewal, payment or external AI enabled.', 'Keine automatische Verlängerung, Zahlung oder externe KI aktiviert.'],
    accessNotices: ['Proefperiodestatus uit de bron', 'Trial status from source', 'Testzeitraumstatus laut Quelle'],
    seven_days: ['Laatste zeven dagen bereikt', 'Last seven days reached', 'Letzte sieben Tage erreicht'],
    one_day: ['Laatste dag bereikt', 'Last day reached', 'Letzter Tag erreicht'],
    expired: ['Eindmoment bereikt', 'End time reached', 'Endzeitpunkt erreicht'],
    noticeRule: ['Dit zijn bronstatussen, geen bevestigde bezorgingen. Tijdzone en bezorgregel voor de laatste dag zijn nog niet vastgesteld.', 'These are source statuses, not confirmed deliveries. The final-day timezone and delivery rule are unresolved.', 'Dies sind Quellstatus, keine bestätigten Zustellungen. Zeitzone und Zustellregel für den letzten Tag sind noch ungeklärt.'],
    notificationDelivery: ['Meldingen in de app', 'In-app notifications', 'Mitteilungen in der App'],
    inAppOnly: ['Bestaande meldingen zijn in de app beschikbaar. Push, e-mail en achtergrondbezorging zijn niet ingeschakeld.', 'Existing notifications are available in the app. Push, email and background delivery are not enabled.', 'Bestehende Mitteilungen sind in der App verfügbar. Push, E-Mail und Hintergrundzustellung sind nicht aktiviert.'],
    notificationPreferences: ['Er is nog geen ondersteunde actie om meldingsvoorkeuren te wijzigen.', 'There is no supported action to change notification preferences yet.', 'Eine unterstützte Aktion zum Ändern der Mitteilungseinstellungen fehlt noch.'],
    pendingNotices: ['Openstaande meldingen', 'Pending notifications', 'Ausstehende Mitteilungen'],
    openToday: ['Vandaag bekijken', 'Open today', 'Heute öffnen'],
    openWorkspace: ['Overzicht openen', 'Open overview', 'Übersicht öffnen'],
    openProposal: ['Voorstel bekijken', 'Review proposal', 'Vorschlag ansehen'],
    memberReview: ['Wacht op lidbevestiging', 'Awaiting member confirmation', 'Mitgliedsbestätigung ausstehend'],
    trainerReview: ['Wacht op trainergoedkeuring', 'Awaiting trainer approval', 'Trainerfreigabe ausstehend'],
    separateApply: ['Wacht op afzonderlijke toepassing door het lid', 'Awaiting separate application by the member', 'Separate Anwendung durch das Mitglied ausstehend'],
    noProposal: ['Geen openstaand voorstel', 'No pending proposal', 'Kein ausstehender Vorschlag'],
    consentTitle: ['Toestemming', 'Consent', 'Einwilligung'],
    consentGranted: ['Vastgelegd; de server controleert toestemming opnieuw bij iedere actie.', 'Recorded; the server checks consent again for every action.', 'Erfasst; der Server prüft die Einwilligung bei jeder Aktion erneut.'],
    consentUnknown: ['Toestemmingsstatus niet aangeleverd.', 'Consent status not supplied.', 'Einwilligungsstatus nicht angegeben.'],
    sourceRole: ['Rol in deze werkruimte', 'Role in this workspace', 'Rolle in diesem Arbeitsbereich'],
    historicalWorkspace: ['Historische workout', 'Historical workout', 'Historisches Training'],
    navigation: ['Account- en werkruimtenavigatie', 'Account and workspace navigation', 'Konto- und Bereichsnavigation'],
    currentWorkspace: ['Huidige werkruimte', 'Current workspace', 'Aktueller Arbeitsbereich']
  };
  const escape = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&#39;'}[c]));
  const w = (key, language) => words[key]?.[language] || key;
  const tierKnown = tier => ['free', 'pro', 'ai'].includes(tier);

  function accessStatus(value) {
    if (value == null || value.status === 'source_missing') return 'source_missing';
    if (value.status !== 'verified_synthetic' || value.read_only !== true || value.synthetic_only !== true ||
        !value.source || typeof value.source.id !== 'string' || !value.source.id || !Number.isSafeInteger(value.source.version) || value.source.version < 1 ||
        !Number.isSafeInteger(value.evaluated_at) || !value.policy || !tierKnown(value.policy.tier) ||
        value.policy.source_version !== value.source.version || !Array.isArray(value.policy.notices) ||
        value.policy.external_ai_enabled !== false || value.policy.payment_action_allowed !== false ||
        value.policy.trial_creation_allowed !== false || value.policy.automatic_renewal !== false || value.policy.retained_history !== true) return 'source_invalid';
    if (value.trial && (!['active','scheduled','expired','revoked'].includes(value.trial.status) ||
        !Number.isSafeInteger(value.trial.start) || !Number.isSafeInteger(value.trial.end) ||
        value.trial.fallback && (!tierKnown(value.trial.fallback.tier) || value.trial.fallback.at !== value.trial.end))) return 'source_invalid';
    return 'verified_synthetic';
  }

  function date(value, language) {
    const d = new Date(value);
    if (!Number.isFinite(d.getTime())) return String(value);
    return new Intl.DateTimeFormat(['nl-NL', 'en-GB', 'de-DE'][language], {
      dateStyle: 'medium', timeStyle: 'short', timeZone: 'UTC'
    }).format(d) + ' UTC';
  }

  function accessPanel(value, language) {
    const status = accessStatus(value), text = key => w(key, language);
    let html = `<section class="account-access" data-access-status="${status}"><h2>${text('accessTitle')}</h2>`;
    if (status !== 'verified_synthetic') return html + `<p>${text(status)}</p></section>`;
    const row = (key, data) => `<dt>${text(key)}</dt><dd>${escape(data)}</dd>`;
    html += `<p>${text('readOnlyAccess')}</p><dl>${row('tier', text(value.policy.tier))}${row('source', value.source.id + ' · v' + value.source.version)}${row('assessed', date(value.evaluated_at, language))}</dl>`;
    if (value.trial) {
      const trial = value.trial;
      html += `<h3>${text('trial')}</h3><p>${text('trial_' + trial.status)}</p><dl>${row('starts', date(trial.start, language))}${row('ends', date(trial.end, language))}`;
      if (trial.fallback) html += row('fallback', text(trial.fallback.tier));
      html += '</dl>';
      if (trial.fallback) html += `<p class="small">${text('fallbackNote')}</p>`;
    } else html += `<p>${text('noTrial')}</p>`;
    const notices = value.policy.notices.filter(n => n && ['seven_days', 'one_day', 'expired'].includes(n.kind));
    if (notices.length) html += `<h3>${text('accessNotices')}</h3><ul>${notices.map(n => `<li>${text(n.kind)}</li>`).join('')}</ul>`;
    return html + `<p class="small">${text('noticeRule')}</p><p>${text('retained')}</p><p>${text('noActivation')}</p></section>`;
  }

  function workspaceLabel(view, language, t) {
    const type = view.capabilities?.registration12 ? w('historicalWorkspace', language) : 'Route ' + (view.state?.route || '?');
    return `${type} · ${t(view.role)} · ${view.workspace}`;
  }

  function reviewStatus(view) {
    const review = view.state?.review;
    if (!review) return 'noProposal';
    if (!review.member) return 'memberReview';
    if (view.state.route === 'A' && !review.trainer) return 'trainerReview';
    return 'separateApply';
  }

  function directory(views, current, language, t, trainerOnly = false) {
    const list = views.filter(v => !trainerOnly || v.role === 'trainer' && !v.capabilities?.registration12);
    const text = key => w(key, language);
    if (!list.length) return `<p data-no-workspaces>${text(trainerOnly ? 'noClients' : 'noWorkspaces')}</p>`;
    return `<ul class="workspace-list">${list.map(view => {
      const s = view.state || {}, historical = view.capabilities?.registration12;
      return `<li><h3>${escape(workspaceLabel(view, language, t))}</h3>${view.workspace === current?.workspace ? `<p class="small">${text('currentWorkspace')}</p>` : ''}<p>${t('version')} ${escape(view.version)}${historical ? '' : ' · ' + text(reviewStatus(view))}</p>${s.consent === false ? `<p class="warning">${t('consent')}</p>` : ''}${s.healthLatch ? `<p class="warning">${t('safety')}</p>` : ''}<div class="actions"><button type="button" data-workspace="${escape(view.workspace)}" data-destination="${historical ? 'training' : 'today'}">${text('openWorkspace')}</button>${!historical && s.review ? `<button type="button" data-workspace="${escape(view.workspace)}" data-destination="review">${text('openProposal')}</button>` : ''}</div></li>`;
    }).join('')}</ul>`;
  }

  function notifications(current, language, t) {
    const text = key => w(key, language);
    return `<section class="account-notifications"><h2>${text('notificationDelivery')}</h2><p>${text('inAppOnly')}</p><p class="small">${text('notificationPreferences')}</p><p>${text('pendingNotices')}: ${(current.notices || []).filter(n => n.status === 'pending').length}</p><button type="button" data-account-tab="today">${text('openToday')}</button></section>`;
  }

  function panel(current, views, tab, language, t) {
    if (tab === 'clients') return directory(views, current, language, t, true);
    if (tab !== 'account') return null;
    const text = key => w(key, language);
    if (!current) return `<p data-no-workspaces>${text('noWorkspaces')}</p>${accessPanel(null, language)}`;
    const s = current.state || {};
    const consent = s.consent === false ? t('consent') : s.consent === true ? text('consentGranted') : text('consentUnknown');
    return `<dl class="account-identity"><dt>${text('sourceRole')}</dt><dd>${escape(t(current.role))}</dd><dt>${text('workspace')}</dt><dd>${escape(current.workspace)}</dd></dl><h2>${text('consentTitle')}</h2><p>${consent}</p>${accessPanel(current.access, language)}${current.role === 'member' && !current.capabilities?.registration12 ? notifications(current, language, t) : ''}<h2>${text('assigned')}</h2>${directory(views, current, language, t)}`;
  }

  function tabs(current) {
    if (!current) return ['account'];
    if (current.capabilities?.registration12) return ['training', 'account'];
    if (current.role === 'member') return ['today','training','nutrition','recovery','intake','review','progress','history','settings','account'];
    return current.role === 'trainer' ? ['clients','today','review','account'] : ['today','review','account'];
  }

  return {words, accessStatus, accessPanel, workspaceLabel, reviewStatus, directory, notifications, panel, tabs};
})();
if (typeof module !== 'undefined') module.exports = FMZAccountCenter;
