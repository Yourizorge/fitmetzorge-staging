(function trainingWorkoutUI() {
  "use strict";
  const M=window.FMZ_WORKOUT_MODEL;
  // Curated view of existing catalog identities; never create or infer a variant.
  const basicGroups=[
    {names:["Borst","Chest","Brust"],exercises:[
      {"id":"bfcda5e1-5a31-551b-ab00-a34e1d51d9be","slug":"barbell-bench-press","names":["Bankdrukken (halterstang)","Barbell bench press","Bankdruecken (Langhantel)"]},
      {"id":"48b83d53-5b2e-5d65-94cc-c0c874e021a2","slug":"dumbbell-bench-press","names":["Dumbbell bench press","Dumbbell bench press","Bankdruecken (Kurzhanteln)"]},
      {"id":"7fc87a35-b24f-53c9-bf76-f299bb89f948","slug":"incline-dumbbell-press","names":["Incline dumbbell press","Incline dumbbell press","Schraegbankdruecken (Kurzhanteln)"]},
      {"id":"83336082-92c1-5ffc-9577-d66242ec8163","slug":"machine-bench-press","names":["Chest press (toestel)","Machine chest press","Brustpresse (Maschine)"]},
      {"id":"065131ba-6d12-53f9-a737-6b501bda164f","slug":"butterfly","names":["Pec deck","Pec deck","Butterfly (Maschine)"]},
      {"id":"fa6ff1f2-c453-58da-9510-a26d5fd6d5b5","slug":"cable-chest-fly","names":["Cable fly (hoge kabels)","Cable fly (high pulleys)","Kabel-Flys (hoher Zug)"]}
    ]},
    {names:["Rug","Back","Ruecken"],exercises:[
      {"id":"fbd17d30-8eec-500a-a123-d2873f5981cd","slug":"wide-grip-lat-pulldown","names":["Lat pulldown (brede greep)","Lat pulldown (wide grip)","Latzug (breiter Griff)"]},
      {"id":"7e11783e-3582-5023-b965-afaf877e4e1b","slug":"seated-cable-rows","names":["Seated cable row (smalle greep)","Seated cable row (close grip)","Kabelrudern sitzend (enger Griff)"]},
      {"id":"06baffb3-553f-5f3c-8a00-717203bb347f","slug":"bent-over-barbell-row","names":["Barbell row","Barbell row","Langhantelrudern"]},
      {"id":"f4b3d183-68b9-5d6e-91a7-751fb49fc444","slug":"one-arm-dumbbell-row","names":["Eenarmige dumbbell row","Single-arm dumbbell row","Einarmiges Kurzhantelrudern"]},
      {"id":"ee7e42f1-3ade-5ccc-92e2-a29fb9d51f4f","slug":"pull-up","names":["Pull-up","Pull-up","Klimmzug"]}
    ]},
    {names:["Schouders","Shoulders","Schultern"],exercises:[
      {"id":"8deb73f1-ca3e-5f31-b089-077b66316a84","slug":"dumbbell-shoulder-press","names":["Dumbbell shoulder press (zittend)","Dumbbell shoulder press (seated)","Schulterdruecken sitzend (Kurzhanteln)"]},
      {"id":"e2229c50-85ca-5eb6-a22d-c21eaf7c56b0","slug":"standing-military-press","names":["Overhead press (halterstang, staand)","Barbell overhead press (standing)","Schulterdruecken stehend (Langhantel)"]},
      {"id":"1feff4cc-8c69-5c92-8d83-2200bad83b70","slug":"leverage-shoulder-press","names":["Shoulder press (toestel, schijven)","Machine shoulder press (plate loaded)","Schulterpresse (scheibenbeladen)"]},
      {"id":"9e9fc710-be0c-5fe0-998c-c69f4f6be489","slug":"lateral-raise","names":["Lateral raise (dumbbells)","Dumbbell lateral raise","Seitheben (Kurzhanteln)"]},
      {"id":"e7669f95-1624-5f4a-a5ab-08fc82e15208","slug":"reverse-machine-flyes","names":["Reverse pec deck","Reverse pec deck","Reverse Butterfly (Maschine)"]},
      {"id":"ee29b63d-e33f-5c62-9677-dafc1b5b9200","slug":"face-pull","names":["Face pull","Face pull","Face Pull"]}
    ]},
    {names:["Benen / billen","Legs / glutes","Beine / Gesaess"],exercises:[
      {"id":"62ac4931-aa57-5795-a722-3888f965e3df","slug":"barbell-squat","names":["Squat (halterstang)","Barbell back squat","Kniebeuge (Langhantel)"]},
      {"id":"55b90c36-5e1b-5582-a1f4-e3adbe4c71d8","slug":"leg-press","names":["Leg press","Leg press","Beinpresse"]},
      {"id":"6b01e0b0-4d0c-5c4e-a001-afa2d1096b98","slug":"leg-extensions","names":["Leg extension","Leg extension","Beinstrecker"]},
      {"id":"c2a48629-90de-5237-9ef9-438b9d61281f","slug":"seated-leg-curl","names":["Leg curl (zittend)","Seated leg curl","Beinbeuger sitzend"]},
      {"id":"d1112790-f11f-514b-9319-ce7589d0b109","slug":"lying-leg-curls","names":["Leg curl (liggend)","Lying leg curl","Beinbeuger liegend"]},
      {"id":"a521421d-dc22-533c-a570-b8131e068a7f","slug":"deadlift","names":["Deadlift (halterstang)","Barbell deadlift","Kreuzheben (Langhantel)"]},
      {"id":"32613884-3784-591e-af61-027451680252","slug":"romanian-deadlift","names":["Romanian deadlift (halterstang)","Barbell Romanian deadlift","Rumaenisches Kreuzheben (Langhantel)"]},
      {"id":"846cb8a7-4939-5509-943c-1efeee5e2d0a","slug":"hip-thrust","names":["Hip thrust (halterstang)","Barbell hip thrust","Hip Thrust (Langhantel)"]},
      {"id":"5824adeb-3e94-50fd-b1ba-61496cfda317","slug":"split-squat-with-dumbbells","names":["Bulgarian split squat (dumbbells)","Dumbbell Bulgarian split squat","Bulgarische Kniebeuge (Kurzhanteln)"]},
      {"id":"c4bb9acb-7973-5245-95a1-e6016c3dd8d3","slug":"thigh-abductor","names":["Hip abduction (toestel)","Machine hip abduction","Hueftabduktion (Maschine)"]},
      {"id":"fdefc70c-dbd2-5f84-a3b8-7eae3c5b2643","slug":"standing-calf-raises","names":["Calf raise (staand, toestel)","Standing machine calf raise","Wadenheben stehend (Maschine)"]}
    ]},
    {names:["Armen","Arms","Arme"],exercises:[
      {"id":"8c8fba33-55d1-5a58-a4a9-33ff13cd2252","slug":"dumbbell-bicep-curl","names":["Dumbbell curl","Dumbbell curl","Bizepscurl (Kurzhanteln)"]},
      {"id":"9fedd062-4d81-546a-8eac-e0db59b0ff76","slug":"barbell-curl","names":["Barbell curl","Barbell curl","Bizepscurl (Langhantel)"]},
      {"id":"640a857e-3b6b-521e-be8d-da729825ac37","slug":"hammer-curls","names":["Hammer curl","Hammer curl","Hammercurl"]},
      {"id":"2cefd973-2a11-5a85-b372-c31b7d1d4e7c","slug":"triceps-pushdown","names":["Triceps pushdown (stang)","Triceps pushdown (bar)","Trizepsdruecken (Stange)"]},
      {"id":"704e0ce4-c007-573f-94f2-b6dee76f376b","slug":"triceps-pushdown-rope-attachment","names":["Triceps pushdown (touw)","Triceps pushdown (rope)","Trizepsdruecken (Seil)"]}
    ]},
    {names:["Buik","Abs","Bauch"],exercises:[
      {"id":"f2380b42-08ca-5c9b-a074-5cf394b8a91b","slug":"crunches","names":["Crunch","Crunch","Crunch"]},
      {"id":"300b0022-6c14-5b99-91fb-9f5bb49ce3e5","slug":"cable-crunch","names":["Cable crunch","Cable crunch","Kabel-Crunch"]}
    ]}
  ];
  const copy={
    create:["Workout maken","Create workout","Workout erstellen"], edit:["Workout bewerken","Edit workout","Workout bearbeiten"],
    library:["Oefeningen","Exercises","Uebungen"], search:["Zoek oefening","Search exercises","Uebung suchen"],
    basics:["Basisoefeningen","Basic exercises","Grunduebungen"], other:["Overige oefeningen","Other exercises","Weitere Uebungen"],
    muscle:["Alle spiergroepen","All muscle groups","Alle Muskelgruppen"], equipment:["Alle materialen","All equipment","Alle Geraete"],
    back:["Terug","Back","Zurueck"], cancel:["Annuleren","Cancel","Abbrechen"], save:["Workout opslaan","Save workout","Workout speichern"],
    saving:["Opslaan...","Saving...","Speichern..."], name:["Naam workout","Workout name","Workoutname"],
    selected:["geselecteerd","selected","ausgewaehlt"], add:["Toevoegen","Add","Hinzufuegen"],
    replace:["Oefening vervangen","Replace exercise","Uebung ersetzen"], remove:["Verwijderen","Remove","Entfernen"],
    info:["Oefeningdetails","Exercise details","Uebungsdetails"], close:["Sluiten","Close","Schliessen"],
    reps:["Reps","Reps","Wdh."], weight:["Doelgewicht","Target weight","Zielgewicht"], notes:["Notities","Notes","Notizen"],
    rest:["Rust (sec)","Rest (sec)","Pause (Sek.)"], groupRest:["Supersetrust (sec)","Superset rest (sec)","Supersatzpause (Sek.)"],
    addSet:["Set toevoegen","Add set","Satz hinzufuegen"], addExercise:["Oefeningen toevoegen","Add exercises","Uebungen hinzufuegen"],
    up:["Omhoog","Move up","Nach oben"], down:["Omlaag","Move down","Nach unten"], drag:["Versleep oefening of superset","Drag exercise or superset","Uebung oder Supersatz ziehen"],
    group:["Koppel met volgende","Link with next","Mit naechster verbinden"], unlink:["Superset losmaken","Unlink superset","Supersatz aufloesen"],
    more:["Meer oefeningen","More exercises","Weitere Uebungen"], empty:["Geen oefeningen gevonden","No exercises found","Keine Uebungen gefunden"],
    loading:["Catalogus laden...","Loading catalog...","Katalog wird geladen..."], retry:["Opnieuw proberen","Retry","Erneut versuchen"],
    loadError:["Catalogus niet geladen. Probeer opnieuw.","Catalog not loaded. Please retry.","Katalog nicht geladen. Bitte erneut versuchen."],
    noMedia:["Geen oefenbeeld","No exercise image","Kein Uebungsbild"],
    noDetails:["Nog geen instructies beschikbaar.","No instructions available yet.","Noch keine Anleitung verfuegbar."],
    invalid:["Controleer de naam, sets, herhalingen en optionele waarden.","Check the name, sets, reps and optional values.","Name, Saetze, Wiederholungen und optionale Werte pruefen."],
    failed:["Niet opgeslagen. Je concept is behouden. Probeer opnieuw.","Not saved. Your draft is retained. Please retry.","Nicht gespeichert. Dein Entwurf bleibt erhalten. Bitte erneut versuchen."],
    conflict:["Elders gewijzigd. Je concept is behouden; herlaad de workout voordat je opnieuw opslaat.","Changed elsewhere. Your draft is retained; reload the workout before saving again.","Andernorts geaendert. Dein Entwurf bleibt erhalten; Workout vor dem Speichern neu laden."],
    discard:["Dit concept verwijderen? Opgeslagen workouts blijven ongewijzigd.","Discard this draft? Saved workouts remain unchanged.","Entwurf verwerfen? Gespeicherte Workouts bleiben unveraendert."],
    reload:["Workout opnieuw laden","Reload workout","Workout neu laden"], reloadConfirm:["Concept vervangen door de opgeslagen workout?","Replace draft with the saved workout?","Entwurf durch gespeichertes Workout ersetzen?"],
    storage:["Concept alleen in dit scherm bewaard; lokale opslag is niet beschikbaar.","Draft retained in this screen only; local storage is unavailable.","Entwurf nur in diesem Bildschirm behalten; lokaler Speicher nicht verfuegbar."],
    day:["Trainingsdag","Training day","Trainingstag"], limit:["Maximaal 4 actieve workouts met Free.","Maximum 4 active workouts with Free.","Mit Free maximal 4 aktive Workouts."],
    optional:["optioneel","optional","optional"], sets:["sets","sets","Saetze"]
  };
  const esc=v=>String(v??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"})[c]);
  const icon=(name,extra="")=>'<img class="tw-icon '+extra+'" src="assets/vendor/lucide-'+name+'.svg" width="20" height="20" alt="">';
  function media(exercise,large=false) {
    const url=exercise?.animationUrl;
    // Only owner-hosted exercise media; no third-party or inferred variant images.
    if(url && /^assets\/[a-z0-9/_-]+\.(?:webp|png|jpg|gif)$/i.test(url))
      return '<img class="tw-media '+(large?'tw-media-large':'')+'" src="'+esc(url)+'" alt="'+esc(exercise.names?.nl||exercise.name||"")+'">';
    return '<span class="tw-media tw-media-fallback '+(large?'tw-media-large':'')+'" aria-label="FitMetZorge">'
      +'<img src="fit-met-zorge-logo.png" alt="" width="40" height="40"></span>';
  }
  window.FMZ_WORKOUT_UI={media,icon,basicGroups,create(api){
    let dialog=null, draft=null, screen="editor", selected=new Set(), filters={search:"",muscle:"",equipment:""},limit=72;
    let detail=null,replaceIndex=null,busy=false,error="",owner="",opener=null,scroll={editor:0,library:0},dragIndex=null,saveReceipt=null,renderedScreen="",renderedDetail=false;
    const t=k=>copy[k]?.[["nl","en","de"].indexOf(api.language())]||copy[k]?.[0]||api.text(k);
    const key=()=> "fmz-phase3-workout-draft:"+api.userKey();
    const catalog=()=>api.catalog().filter(e=>e.catalogBacked);
    const basic=c=>basicGroups.flatMap(g=>g.exercises).find(e=>e.id===c.id&&e.slug===c.slug);
    const localized=names=>names[Math.max(0,["nl","en","de"].indexOf(api.language()))];
    const displayMeta=c=>({...api.meta(c.slug),name:basic(c)?localized(basic(c).names):api.meta(c.slug).name});
    const button=(name,action,index="",symbol="",disabled=false)=>'<button type="button" data-tw-action="'+action+'" data-tw-index="'+index+'" class="'+(symbol?'tw-tool':'secondary-btn')+'" title="'+esc(t(name))+'" aria-label="'+esc(t(name))+'"'+(disabled?' disabled':'')+'>'+(symbol?icon(symbol,action==="down"?"tw-down":""):esc(t(name)))+'</button>';
    const option=(value,label,current)=>'<option value="'+esc(value)+'"'+(value===current?' selected':'')+'>'+esc(label)+'</option>';
    function remember() {
      try {localStorage.setItem(key(),JSON.stringify({owner:api.userKey(),draft,saveReceipt}));}
      catch {error=t("storage");}
    }
    function restore() {
      try {const value=JSON.parse(localStorage.getItem(key())||"null");
        if(value?.owner===api.userKey() && value.draft?.days?.length) {draft=value.draft;saveReceipt=value.saveReceipt||null;}}
      catch {error=t("storage");}
    }
    function fresh() {
      const day=api.days()[0],now=new Date().toISOString();
      return {id:api.uuid(),title:"",status:"active",source:"phase3_client",createdAt:now,updatedAt:null,localOnly:false,
        days:[{id:api.uuid(),label:day,order:0,status:"active",exercises:[]}]};
    }
    const exercises=()=>draft.days[0].exercises;
    function syncTargets(e) {
      const rows=M.targets(e),first=rows[0];e.setTargets=rows;e.targetSets=rows.length;
      e.targetReps=first.reps;e.targetWeight=first.weight??"";e.targetRir=first.rir??"";e.targetRpe=first.rpe??"";
    }
    function fromCatalog(c,previous=null) {
      const meta=displayMeta(c),id=api.uuid();
      const e={...(previous?M.clone(previous):{}),id,key:id,exerciseId:c.id,catalogBacked:true,slug:c.slug,canonicalSlug:c.slug,
        name:meta.name,primaryMuscle:meta.primary,equipment:meta.equipment,status:"active",
        setTargets:previous?M.targets(previous):Array.from({length:3},()=>({reps:"8-10",weight:null,rir:null,rpe:null})),
        restSeconds:previous?.restSeconds??90,notes:previous?.notes||""};
      syncTargets(e);return e;
    }
    function reset() {close();draft=null;owner=api.userKey();saveReceipt=null;error="";}
    function close() {dialog?.close();dialog?.remove();dialog=null;document.body.classList.remove("tw-open");opener?.focus?.();}
    function open(plan=null) {
      if(owner!==api.userKey())reset();
      opener=document.activeElement;error="";
      if(plan) {
        if(draft && draft.id!==plan.id && !confirm(t("discard")))return;
        if(!draft||draft.id!==plan.id) {
          draft=M.clone(plan);saveReceipt=null;scroll={editor:0,library:0};
          draft.days=[draft.days.find(d=>(d.status||"active")==="active")||draft.days[0]];
          draft.days[0].exercises=draft.days[0].exercises.filter(e=>(e.status||"active")==="active");
        }
      } else {
        if(!draft)restore();
        if(!draft&&!api.canCreate()){api.feedback(t("limit"));return;}
        draft ||= fresh();
      }
      exercises().forEach(syncTargets);
      screen=exercises().length?"editor":"library";selected=new Set();replaceIndex=null;detail=null;
      if(screen==="library"){filters={search:"",muscle:"",equipment:""};limit=72;scroll.library=0;}
      if(!dialog){dialog=document.createElement("dialog");dialog.className="tw-dialog";dialog.id="fmz-workout-maker";document.body.append(dialog);bind();}
      render();dialog.showModal();document.body.classList.add("tw-open");remember();
      if(screen==="library"||!catalog().length)loadCatalog();
    }
    async function loadCatalog() {const who=api.userKey();renderLibrary();await api.loadCatalog();if(dialog&&who===api.userKey()){if(screen==="library")renderLibrary();else render();}}
    function list() {
      const search=filters.search.trim().toLocaleLowerCase();
      return catalog().filter(c=>{
        const meta=api.meta(c.slug);
        return (!search||[...Object.values(c.names||{}),...(basic(c)?.names||[]),c.slug,...Object.values(c.primary||{}),...Object.values(c.equipment||{})].join(" ").toLocaleLowerCase().includes(search))&&
          (!filters.muscle||meta.primary===filters.muscle)&&(!filters.equipment||meta.equipment===filters.equipment);
      });
    }
    function filtersHtml() {
      const values=field=>[...new Set(catalog().map(c=>api.meta(c.slug)[field]))].sort();
      return '<label class="tw-search"><span>'+esc(t("search"))+'</span><input data-tw-filter="search" type="search" value="'+esc(filters.search)+'" autocomplete="off"></label>'
        +'<div class="tw-filters"><select aria-label="'+esc(t("muscle"))+'" data-tw-filter="muscle">'+option("",t("muscle"),filters.muscle)+values("primary").map(v=>option(v,v,filters.muscle)).join("")+'</select>'
        +'<select aria-label="'+esc(t("equipment"))+'" data-tw-filter="equipment">'+option("",t("equipment"),filters.equipment)+values("equipment").map(v=>option(v,v,filters.equipment)).join("")+'</select></div>';
    }
    function renderLibrary() {
      if(!dialog||screen!=="library"||detail)return;
      const target=dialog.querySelector("[data-tw-results]");if(!target)return;
      const rows=list(),unfiltered=!Object.values(filters).some(v=>v.trim());
      const rowHtml=c=>{
        const meta=displayMeta(c),checked=selected.has(c.id);
        return '<div class="tw-library-row"><label>'+media(c)+'<span><strong>'+esc(meta.name)+'</strong><small>'+esc(meta.primary+" / "+meta.equipment)+'</small></span>'
          +'<input type="checkbox" data-tw-select="'+esc(c.id)+'"'+(checked?' checked':'')+' aria-label="'+esc(meta.name)+'"></label>'
          +button("info","info",c.id,"file-text")+'</div>';
      };
      const basics=unfiltered?basicGroups.map(g=>({names:g.names,exercises:g.exercises.map(e=>rows.find(c=>c.id===e.id&&c.slug===e.slug)).filter(Boolean)})):[];
      const basicIds=new Set(basics.flatMap(g=>g.exercises.map(c=>c.id)));
      const remaining=rows.filter(c=>!basicIds.has(c.id));
      target.innerHTML=(basicIds.size?'<section class="tw-basics" aria-labelledby="tw-basics-title"><h3 id="tw-basics-title">'+esc(t("basics"))+'</h3>'
        +basics.filter(g=>g.exercises.length).map(g=>'<h4>'+esc(localized(g.names))+'</h4>'+g.exercises.map(rowHtml).join("")).join("")+'</section><h3 class="tw-library-title">'+esc(t("other"))+'</h3>':"")
        +remaining.slice(0,limit).map(rowHtml).join("");
      if(!rows.length)target.innerHTML='<p>'+esc(catalog().length?t("empty"):t("loadError"))+'</p>';
      if(!catalog().length)target.innerHTML+=button("retry","retry");
      if(remaining.length>limit)target.innerHTML+=button("more","more");
      const count=dialog.querySelector("[data-tw-count]");if(count)count.textContent=selected.size+" "+t("selected");
      const add=dialog.querySelector('[data-tw-action="selected"]');if(add)add.disabled=!selected.size;
    }
    const input=(label,value,attrs)=>'<label><span>'+esc(label)+'</span><input value="'+esc(value)+'" '+attrs+'></label>';
    function editorExercise(e,i) {
      const mode=api.preferences().effort_mode||"rir",rows=M.targets(e),imperial=api.imperial(),unit=imperial?"lb":"kg";
      const c=catalog().find(c=>c.id===e.exerciseId),meta=c?displayMeta(c):api.meta(e.slug),name=meta.name||e.name,detail=[meta.primary||e.primaryMuscle,meta.equipment||e.equipment].filter(Boolean).join(" / ");
      const group=M.groups(exercises()).find(g=>g.indices.includes(i)),first=group.indices[0]===i;
      const groupTitle=e.supersetId&&first?'<div class="tw-group-title"><strong>Superset '+String.fromCharCode(65+M.groups(exercises()).filter(g=>g.id).findIndex(g=>g.id===e.supersetId))+'</strong>'+button("unlink","unlink",i,"x")+'</div>':"";
      return groupTitle+'<article class="tw-exercise" data-tw-exercise="'+i+'">'
        +'<header>'+media(api.catalog().find(c=>c.id===e.exerciseId))+'<div><h3>'+esc(name)+'</h3><small>'+esc(detail)+'</small></div>'
        +'<button type="button" draggable="true" data-tw-drag="'+i+'" class="tw-tool" title="'+esc(t("drag"))+'" aria-label="'+esc(t("drag"))+'">'+icon("arrow-up")+'</button></header>'
        +'<div class="tw-exercise-tools">'+button("up","up",i,"arrow-up",group.indices[0]===0)+button("down","down",i,"arrow-up",group.indices.at(-1)===exercises().length-1)
        +button("replace","replace",i,"rotate-cw")+button("remove","remove",i,"trash-2")+'</div>'
        +'<label class="tw-notes"><span>'+esc(t("notes"))+'</span><textarea rows="2" maxlength="2000" data-tw-notes="'+i+'">'+esc(e.notes||"")+'</textarea></label>'
        +'<div class="tw-targets">'+rows.map((row,n)=>'<div class="tw-target-row"><strong class="tw-set-no">'+(n+1)+'</strong>'
          +input(t("reps"),row.reps,'data-tw-target="'+i+':'+n+':reps" required maxlength="32" inputmode="text"')
          +input(t("weight")+" ("+unit+")",M.displayWeight(row.weight,imperial),'data-tw-target="'+i+':'+n+':weight" type="number" min="0" max="'+(imperial?22046:10000)+'" step="any" inputmode="decimal"')
          +(mode!=="none"?input(mode.toUpperCase()+" ("+t("optional")+")",row[mode]??"",'data-tw-target="'+i+':'+n+':'+mode+'" type="number" min="'+(mode==="rpe"?1:0)+'" max="10" step="'+(mode==="rir"?1:.5)+'" inputmode="decimal"'):"")
          +button("remove","remove-set",i+":"+n,"x",rows.length===1)+'</div>').join("")+'</div>'
        +'<div class="tw-exercise-footer">'+button("addSet","add-set",i,"plus",rows.length>=20)
        +input(t("rest"),e.restSeconds,'data-tw-rest="'+i+'" type="number" min="0" max="3600" step="1" inputmode="numeric"')
        +(e.supersetId&&first?input(t("groupRest"),e.supersetRestSeconds,'data-tw-group-rest="'+i+'" type="number" min="0" max="3600" step="1" inputmode="numeric"'):"")+'</div>'
        +(i<exercises().length-1&&(!e.supersetId||exercises()[i+1].supersetId!==e.supersetId)?button("group","group",i):"")+'</article>';
    }
    function render() {
      if(!dialog)return;
      const old=dialog.querySelector("main");if(old&&!renderedDetail&&renderedScreen)scroll[renderedScreen]=old.scrollTop;
      let title=t(screen==="library"?"library":draft.updatedAt?"edit":"create"),body="",footer="";
      if(detail) {
        const meta=displayMeta(detail);title=meta.name;
        body=media(detail,true)+'<h3>'+esc(meta.name)+'</h3><p>'+esc(meta.primary+" / "+meta.equipment)+'</p><p>'+esc(meta.instructions||t("noDetails"))+'</p>';
      } else if(screen==="library") {
        body=filtersHtml()+'<div data-tw-results></div>';
        footer='<span data-tw-count>'+selected.size+' '+esc(t("selected"))+'</span><button type="button" class="primary-btn" data-tw-action="selected"'+(!selected.size?' disabled':'')+'>'+esc(t(replaceIndex===null?"add":"replace"))+'</button>';
      } else {
        body=input(t("name"),draft.title,'data-tw-title required maxlength="120"')
          +'<label><span>'+esc(t("day"))+'</span><select data-tw-day>'+api.days().map(d=>option(d,api.text(d),draft.days[0].label)).join("")+'</select></label>'
          +exercises().map(editorExercise).join("")+'<div class="tw-add">'+button("addExercise","library","", "plus")+'</div>';
        footer='<span>'+exercises().length+' '+esc(t("library").toLowerCase())+'</span><button type="button" class="primary-btn" data-tw-action="save"'+(busy?' disabled':'')+'>'+esc(t(busy?"saving":"save"))+'</button>';
      }
      dialog.innerHTML='<header class="tw-header">'+button("back","back","","arrow-left",busy)+'<h2>'+esc(title)+'</h2>'+button("cancel","cancel","","x",busy)+'</header>'
        +'<main>'+body+'</main><div class="tw-feedback" role="status">'+esc(error)+'</div><footer>'+footer+'</footer>';
      if(error===t("conflict"))dialog.querySelector(".tw-feedback").insertAdjacentHTML("beforeend",button("reload","reload"));
      if(!detail)dialog.querySelector("main").scrollTop=scroll[screen]||0;
      if(screen==="library"&&!detail)renderLibrary();
      renderedScreen=screen;renderedDetail=!!detail;
    }
    function normalizeGroups() {
      const rows=exercises(),groups=M.groups(rows);
      groups.forEach(g=>{if(g.id&&(g.indices.length<2||groups.filter(x=>x.id===g.id).length>1))g.indices.forEach(i=>{rows[i].supersetId=null;rows[i].supersetRestSeconds=null;});});
      rows.forEach((e,i)=>{e.order=i;syncTargets(e);});
    }
    function move(from,to) {
      const gs=M.groups(exercises()),a=gs.findIndex(g=>g.indices.includes(from)),b=gs.findIndex(g=>g.indices.includes(to));
      if(a<0||b<0||a===b)return;
      const chunks=gs.map(g=>g.indices.map(i=>exercises()[i])),[chunk]=chunks.splice(a,1);chunks.splice(b,0,chunk);
      draft.days[0].exercises=chunks.flat();normalizeGroups();remember();render();
    }
    async function save() {
      if(busy)return;
      if(!draft.title.trim()||!exercises().length||!exercises().every(e=>M.validTargets(e.setTargets)&&Number.isInteger(Number(e.restSeconds))&&Number(e.restSeconds)>=0&&Number(e.restSeconds)<=3600)){
        error=t("invalid");render();return;
      }
      normalizeGroups();
      const payload=JSON.stringify(draft);
      if(!saveReceipt||saveReceipt.payload!==payload)saveReceipt={id:api.uuid(),payload};
      busy=true;error="";remember();render();const who=api.userKey();
      try{
        const result=await api.save(M.clone(draft),saveReceipt.id);
        if(api.userKey()!==who)return;
        if(!result.ok)throw result.error||new Error("save_failed");
        draft=null;saveReceipt=null;localStorage.removeItem(key());close();api.saved();
      }catch(e){if(who===api.userKey()){error=/stale|conflict/.test(e.message||"")?t("conflict"):t("failed");remember();}}
      finally{busy=false;if(dialog)render();}
    }
    function bind() {
      dialog.addEventListener("cancel",event=>{event.preventDefault();if(!busy){remember();close();}});
      dialog.addEventListener("input",event=>{
        const el=event.target;
        if(el.dataset.twFilter==="search"){filters.search=el.value;limit=72;renderLibrary();return;}
        if(busy)return;
        if(el.hasAttribute("data-tw-title"))draft.title=el.value;
        if(el.hasAttribute("data-tw-notes"))exercises()[Number(el.dataset.twNotes)].notes=el.value;
        if(el.hasAttribute("data-tw-target")){
          const [i,n,k]=el.dataset.twTarget.split(":");const row=exercises()[i].setTargets[n];
          row[k]=k==="reps"?el.value:k==="weight"?M.storedWeight(el.value,api.imperial()):M.number(el.value);
        }
        if(el.hasAttribute("data-tw-rest"))exercises()[Number(el.dataset.twRest)].restSeconds=el.value;
        if(el.hasAttribute("data-tw-group-rest")){const e=exercises()[Number(el.dataset.twGroupRest)];exercises().filter(x=>x.supersetId===e.supersetId).forEach(x=>x.supersetRestSeconds=el.value);}
        remember();
      });
      dialog.addEventListener("change",event=>{
        const el=event.target;
        if(el.dataset.twFilter&&el.dataset.twFilter!=="search"){filters[el.dataset.twFilter]=el.value;limit=72;renderLibrary();}
        if(el.hasAttribute("data-tw-day")){draft.days[0].label=el.value;draft.days[0].order=api.days().indexOf(el.value);remember();}
        if(el.dataset.twSelect){if(replaceIndex!==null)selected.clear();el.checked?selected.add(el.dataset.twSelect):selected.delete(el.dataset.twSelect);renderLibrary();}
      });
      dialog.addEventListener("dragstart",e=>{const handle=e.target.closest("[data-tw-drag]");if(handle){
        dragIndex=Number(handle.dataset.twDrag);e.dataTransfer.setData("text/plain",String(dragIndex));e.dataTransfer.effectAllowed="move";
        // Compact long exercise blocks so the drop destination remains reachable.
        requestAnimationFrame(()=>{if(dialog&&dragIndex!==null)dialog.classList.add("tw-dragging");});
      }});
      dialog.addEventListener("dragover",e=>{if(dragIndex!==null&&e.target.closest("[data-tw-exercise]")){e.preventDefault();e.dataTransfer.dropEffect="move";}});
      dialog.addEventListener("dragend",()=>{dragIndex=null;dialog?.classList.remove("tw-dragging");});
      dialog.addEventListener("drop",e=>{const target=e.target.closest("[data-tw-exercise]");if(target&&dragIndex!==null){e.preventDefault();dialog.classList.remove("tw-dragging");move(dragIndex,Number(target.dataset.twExercise));dragIndex=null;}});
      dialog.addEventListener("click",async event=>{
        const b=event.target.closest("[data-tw-action]");if(!b||busy)return;
        const action=b.dataset.twAction,i=Number(b.dataset.twIndex);
        if(action==="back"){if(detail){detail=null;render();return;}if(screen==="library"){screen="editor";render();return;}remember();close();return;}
        if(action==="cancel"){if(screen==="library"||detail){detail=null;screen="editor";selected.clear();render();return;}if(confirm(t("discard"))){draft=null;saveReceipt=null;localStorage.removeItem(key());close();}return;}
        if(action==="save"){await save();return;}
        if(action==="reload"){if(confirm(t("reloadConfirm"))){await api.reload();const plan=api.plans().find(p=>p.id===draft.id);if(plan){draft=null;open(plan);}}return;}
        if(action==="library"||action==="replace"){scroll.editor=dialog.querySelector("main").scrollTop;screen="library";filters={search:"",muscle:"",equipment:""};limit=72;scroll.library=0;selected.clear();replaceIndex=action==="replace"?i:null;render();await loadCatalog();return;}
        if(action==="retry"){await loadCatalog();return;}
        if(action==="more"){limit+=72;renderLibrary();return;}
        if(action==="info"){scroll.library=dialog.querySelector("main").scrollTop;const c=catalog().find(c=>c.id===b.dataset.twIndex);if(c){detail=c;render();await api.details([c]);if(dialog&&detail?.id===c.id)render();}return;}
        if(action==="selected"){const chosen=[...selected].map(id=>catalog().find(c=>c.id===id)).filter(Boolean);if(replaceIndex!==null){if(chosen[0])exercises()[replaceIndex]=fromCatalog(chosen[0],exercises()[replaceIndex]);}else exercises().push(...chosen.map(c=>fromCatalog(c)));selected.clear();replaceIndex=null;screen="editor";}
        if(action==="remove"){exercises().splice(i,1);}
        if(action==="add-set"){if(exercises()[i].setTargets.length<20)exercises()[i].setTargets.push(M.clone(exercises()[i].setTargets.at(-1)));}
        if(action==="remove-set"){const [x,n]=b.dataset.twIndex.split(":").map(Number);if(exercises()[x].setTargets.length>1)exercises()[x].setTargets.splice(n,1);}
        if(action==="up"||action==="down"){const gs=M.groups(exercises()),g=gs.find(x=>x.indices.includes(i)),n=gs.indexOf(g)+(action==="up"?-1:1);if(gs[n])move(i,gs[n].indices[0]);return;}
        if(action==="group"){const a=exercises()[i],c=exercises()[i+1];if(c){const ids=[a.supersetId,c.supersetId].filter(Boolean),id=a.supersetId||c.supersetId||api.uuid();exercises().forEach((e,n)=>{if(n===i||n===i+1||ids.includes(e.supersetId)){e.supersetId=id;e.supersetRestSeconds=a.supersetRestSeconds??90;}});}}
        if(action==="unlink"){const id=exercises()[i].supersetId;exercises().filter(e=>e.supersetId===id).forEach(e=>{e.supersetId=null;e.supersetRestSeconds=null;});}
        normalizeGroups();remember();render();
      });
    }
    return {open,close,reset,render,isOpen:()=>!!dialog};
  }};
})();
