"use strict";
(() => {
  const $ = id => document.getElementById(id), data = window.FMZDemoData, M = window.FMZDemoModel;
  let locale = "nl", persona = "member", selected = "normal", model = M.create(data.seeds.normal), count = 0;
  const t = key => window.FMZDemoCopy[locale][key] || key;
  const el = (tag, text, cls) => { const node = document.createElement(tag); if (text !== undefined) node.textContent = text; if (cls) node.className = cls; return node; };
  const num = x => x === null || x === undefined ? "-" : String(x).replace(".", locale === "en" ? "." : ",");
  const ref = x => x ? x.id + " @ " + x.revision : "-";
  function opts(node, keys, value) {
    const short = {version_conflict:"short_versions",expired:"short_expired",consent_revoked:"short_consent",
      relation_revoked:"short_relation",incomplete:"short_incomplete",unavailable:"short_unavailable",
      no_trainer:"short_no_trainer",ambiguous_rules:"short_ambiguous"};
    node.replaceChildren(...keys.map(k => { const o = el("option", t(short[k] || k)); o.value = k; return o; }));
    node.value = value;
  }
  function button(parent, text, id, handler, cls = "") {
    const b = el("button", text, cls); b.type = "button"; b.dataset.action = id; b.addEventListener("click", handler); parent.append(b); return b;
  }
  function act(action, target = null) {
    const out = model.command(model.event(action, persona, "cmd-ui-" + (++count), target));
    render(); $("feedback").textContent = out.ok ? t("success") : t("error") + " (" + out.reason + ")";
  }
  function planTable(exercise, old, mark) {
    const table = el("table"), head = el("thead"), tr = el("tr");
    for (const key of ["set", "weight", "reps", "RIR", "RPE"]) tr.append(el("th", t(key)));
    head.append(tr); table.append(head); const body = el("tbody");
    for (const set of exercise.sets) {
      const before = old?.sets.find(s => s.index === set.index), row = el("tr");
      const values = [set.index, num(set.load.value) + " " + set.load.unit,
        set.reps.min === set.reps.max ? num(set.reps.min) : num(set.reps.min) + "-" + num(set.reps.max), num(set.rir), num(set.rpe)];
      const changed = [false, before && !M.same(set.load, before.load), before && !M.same(set.reps, before.reps),
        before && set.rir !== before.rir, before && set.rpe !== before.rpe];
      values.forEach((value, i) => { const cell = el("td", String(value), mark && changed[i] ? "delta" : "");
        if (mark && changed[i]) cell.setAttribute("aria-label", t("changed") + ": " + value);
        row.append(cell); }); body.append(row);
    }
    table.append(body); return table;
  }
  function renderComparison(s, seed) {
    const p = s.proposal, parent = $("comparison"); parent.replaceChildren();
    for (const workout of p.base.options) for (const exercise of workout.exercises) {
      const next = p.target.options.find(w => w.id === workout.id)?.exercises.find(e => e.exercise_id === exercise.exercise_id);
      const row = seed.rows.find(r => r.exercise_id === exercise.exercise_id);
      const label = seed.catalog.find(c => c.id === exercise.exercise_id)?.labels[locale] || exercise.exercise_id;
      const section = el("div", undefined, "exercise"), heading = el("div", undefined, "exercise-head");
      heading.append(el("h3", label));
      heading.append(el("span", p.kind === "restore" ? t("restore") : row ? t(row.kind) : t("facts"), "kind"));
      section.append(heading);
      const pair = el("div", undefined, "plan-pair");
      const left = el("div", undefined, "plan-side"), right = el("div", undefined, "plan-side");
      left.append(el("h4", t("oldPlan") + " · v" + p.base.revision), planTable(exercise));
      right.append(el("h4", t("proposed") + (p.status === "maintained" || p.status === "blocked" ? "" : " · v" + (p.base.revision + 1))),
        planTable(next || exercise, exercise, p.status !== "blocked"));
      pair.append(left, right); section.append(pair);
      const details = el("details", undefined, "actual"); details.append(el("summary", t("actual")));
      const list = el("ul"), observations = row?.observations || seed.facts.filter(f => f.exercise_ref.id === exercise.exercise_id).map(f => ({
        ...f.recorded, set_index: f.set_index, session_ref: f.session_ref, plan_ref: f.plan_ref
      }));
      for (const o of observations) list.append(el("li",
        ref(o.session_ref) + " · " + t("set") + " " + o.set_index + ": " + num(o.reps) + " reps · " +
        num(o.load?.value) + " " + (o.load?.unit || "") + " · RIR " + num(o.rir) + " · RPE " + num(o.rpe) + " · " + ref(o.plan_ref)));
      if (!observations.length) list.append(el("li", t("incomplete")));
      details.append(list); section.append(details);
      section.append(el("p", t("reason") + ": " + (p.kind === "restore" ? t("restoreWarning") : row ? t(row.reason) : t(seed.gate || "unavailable")), "reason"));
      parent.append(section);
    }
  }
  function render() {
    const s = model.view(), p = s.proposal, seed = data.seeds[selected];
    document.documentElement.lang = locale;
    const labels = {"demo-label":"demo","reset-note":"resetNote",title:"title",fiction:"fiction","language-label":"language",
      "theme-label":"theme",reset:"reset","scenario-label":"scenario","persona-label":"persona","member-label":"member",
      "trainer-label":"trainer","review-heading":"review","history-heading":"history","sources-heading":"sources",
      "inbox-heading":"inbox","simulate-heading":"simulate",inject:"trigger",retention:"retention","audit-heading":"audit",
      "chat-heading":"chat","chat-note":"chatNote",boundary:"noAdvice"};
    for (const [id, key] of Object.entries(labels)) $(id).textContent = t(key);
    $("source-event").setAttribute("aria-label", t("simulate"));
    opts($("theme"), ["light","dark"], document.documentElement.dataset.theme);
    opts($("scenario"), Object.keys(data.seeds), selected);
    opts($("source-event"), ["version_conflict","expired","consent_revoked","relation_revoked","incomplete","unavailable"], $("source-event").value || "version_conflict");
    $("status").textContent = t(p.status) + " · " + t("version") + " " + s.active.revision;
    $("goal").textContent = seed.goal.labels[locale] + " · " + ref(seed.goal.ref);
    $("warning").textContent = s.gate ? t(s.gate) : p.kind === "restore" ? t("restoreWarning") : p.status === "maintained" ? t("noChange") : "";
    const timeline = $("timeline"); timeline.replaceChildren();
    const rank = {member_pending:2,trainer_pending:3,approved:4,applied:5}[p.status] || 0;
    ["review","member","approval","application"].forEach((key,i) => {
      const li = el("li", undefined, rank === i + 1 ? "active" : rank > i + 1 ? "done" : "");
      li.append(el("span", String(i + 1), "step-number"), el("span", t(key)));
      timeline.append(li);
    });
    $("w2").replaceChildren();
    for (const r of seed.w2) $("w2").append(el("p", r.exercise + " · " + t("step") + ": " + num(r.step) + " " + r.unit +
      " · " + t("weights") + ": " + r.available.map(num).join(", ") + " " + r.unit));
    renderComparison(s, seed);
    $("actions").replaceChildren();
    if (persona === "member" && p.status === "member_pending" && !s.gate) {
      button($("actions"), t("accept"), "member_accept", () => act("member_accept"), "primary");
      button($("actions"), t("reject"), "member_reject", () => act("member_reject"), "danger");
    }
    if (persona === "trainer" && p.status === "trainer_pending" && !s.gate) {
      button($("actions"), t("approve"), "trainer_approve", () => act("trainer_approve"), "primary");
      button($("actions"), t("reject"), "trainer_reject", () => act("trainer_reject"), "danger");
      button($("actions"), t("block"), "trainer_block", () => act("trainer_block"), "danger");
    }
    if (persona === "trainer" && p.status === "approved" && !s.gate)
      button($("actions"), t("apply"), "apply", () => act("apply"), "primary");
    $("feedback").textContent = "";
    $("approvals").replaceChildren(...[
      t("member") + ": " + t(p.member), t("trainer") + ": " + (p.trainer === "approved" ? t("trainer_approve") : t(p.trainer)),
      t("application") + ": " + t(p.application)
    ].map(x => el("span", x)));
    $("history").replaceChildren();
    $("history").append(el("p", t("plan") + ": v" + s.active.revision));
    for (const h of s.history) {
      const row = el("div", undefined, "history-item"); row.append(el("strong", "v" + h.revision));
      if (p.status === "applied" && !s.gate)
        button(row, t("restore") + " v" + h.revision, "restore", () => act("restore", h.revision));
      const details = el("details"); details.append(el("summary", t("plan")), el("pre", JSON.stringify(h, null, 2))); row.append(details); $("history").append(row);
    }
    $("sources").replaceChildren(el("pre", JSON.stringify({source_commit:data.source_commit,refs:p.refs,basis:p.basis},null,2)));
    for(const row of seed.rows) $("sources").append(el("div",row.labels[locale] + ": " + JSON.stringify(row.rule),"source-item"));
    $("inbox").replaceChildren(el("p", t(persona)));
    const inbox = el("ol");
    for(const n of s.notifications.filter(n=>n.recipient===persona && !(persona==="trainer" && !s.trainer))) {
      const keys={approved:"approved_notice",applied:"applied_notice",restore:"restore_notice",blocked:"blocked_notice",rejected:"rejected_notice"};
      const li=el("li",t(keys[n.key]||n.key)+(n.reason?" "+t(n.reason):""));
      li.append(el("time",n.at));inbox.append(li);
    }
    if(!inbox.children.length) $("inbox").append(el("p",t("empty"),"empty"));else $("inbox").append(inbox);
    $("audit").replaceChildren();
    for(const a of [...s.audit].reverse()) {
      const item=el("div",undefined,"audit-entry"),meta=el("div",undefined,"audit-meta");
      meta.append(el("strong",t(a.action)),el("span",t(a.actor)),el("span",t(a.status)),el("span","v"+a.before_version+" → v"+a.after_version));
      item.append(meta,el("time",a.at),el("p",t("reason")+": "+t(a.reason)));
      const details=el("details"); details.append(el("summary",t("sources")),el("pre",JSON.stringify(a,null,2)));item.append(details);$("audit").append(item);
    }
  }
  $("language").addEventListener("change",e=>{locale=e.target.value;render();});
  $("theme").addEventListener("change",e=>{document.documentElement.dataset.theme=e.target.value;});
  $("scenario").addEventListener("change",e=>{selected=e.target.value;model=M.create(data.seeds[selected]);count=0;render();});
  $("reset").addEventListener("click",()=>{model=M.create(data.seeds[selected]);count=0;render();});
  document.querySelectorAll('input[name="persona"]').forEach(input=>input.addEventListener("change",e=>{persona=e.target.value;render();}));
  $("inject").addEventListener("click",()=>{model.inject($("source-event").value);render();});
  render();
})();
