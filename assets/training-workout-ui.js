(function trainingWorkoutUI() {
  "use strict";
  const M=window.FMZ_WORKOUT_MODEL;
  const copy={
    create:["Workout maken","Create workout","Workout erstellen"], edit:["Workout bewerken","Edit workout","Workout bearbeiten"],
    library:["Oefeningen","Exercises","Uebungen"], search:["Zoek oefening","Search exercises","Uebung suchen"],
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
  window.FMZ_WORKOUT_UI={media,icon,create(api){
    let dialog=null, draft=null, screen="editor", selected=new Set(), filters={search:"",muscle:"",equipment:""},limit=72;
    let detail=null,replaceIndex=null,busy=false,error="",owner="",opener=null,scroll={editor:0,library:0},dragIndex=null,saveReceipt=null,renderedScreen="",renderedDetail=false;
    const t=k=>copy[k]?.[["nl","en","de"].indexOf(api.language())]||copy[k]?.[0]||api.text(k);
    const key=()=> "fmz-phase3-workout-draft:"+api.userKey();
    const catalog=()=>api.catalog().filter(e=>e.catalogBacked);
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
      const meta=api.meta(c.slug),id=api.uuid();
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
      if(!dialog){dialog=document.createElement("dialog");dialog.className="tw-dialog";dialog.id="fmz-workout-maker";document.body.append(dialog);bind();}
      render();dialog.showModal();document.body.classList.add("tw-open");remember();
      if(screen==="library"||!catalog().length)loadCatalog();
    }
    async function loadCatalog() {const who=api.userKey();renderLibrary();await api.loadCatalog();if(dialog&&who===api.userKey()){if(screen==="library")renderLibrary();else render();}}
    function list() {
      const search=filters.search.trim().toLocaleLowerCase();
      return catalog().filter(c=>{
        const meta=api.meta(c.slug);
        return (!search||[...Object.values(c.names||{}),c.slug,...Object.values(c.primary||{}),...Object.values(c.equipment||{})].join(" ").toLocaleLowerCase().includes(search))&&
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
      const rows=list();
      target.innerHTML=rows.slice(0,limit).map(c=>{
        const meta=api.meta(c.slug),checked=selected.has(c.id);
        return '<div class="tw-library-row"><label>'+media(c)+'<span><strong>'+esc(meta.name)+'</strong><small>'+esc(meta.primary+" / "+meta.equipment)+'</small></span>'
          +'<input type="checkbox" data-tw-select="'+esc(c.id)+'"'+(checked?' checked':'')+' aria-label="'+esc(meta.name)+'"></label>'
          +button("info","info",c.id,"file-text")+'</div>';
      }).join("")||'<p>'+esc(catalog().length?t("empty"):t("loadError"))+'</p>';
      if(!catalog().length)target.innerHTML+=button("retry","retry");
      if(rows.length>limit)target.innerHTML+=button("more","more");
      const count=dialog.querySelector("[data-tw-count]");if(count)count.textContent=selected.size+" "+t("selected");
      const add=dialog.querySelector('[data-tw-action="selected"]');if(add)add.disabled=!selected.size;
    }
    const input=(label,value,attrs)=>'<label><span>'+esc(label)+'</span><input value="'+esc(value)+'" '+attrs+'></label>';
    function editorExercise(e,i) {
      const mode=api.preferences().effort_mode||"rir",rows=M.targets(e),imperial=api.imperial(),unit=imperial?"lb":"kg";
      const meta=api.meta(e.slug),name=meta.name||e.name,detail=[meta.primary||e.primaryMuscle,meta.equipment||e.equipment].filter(Boolean).join(" / ");
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
        const meta=api.meta(detail.slug);title=meta.name;
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
        if(action==="library"||action==="replace"){scroll.editor=dialog.querySelector("main").scrollTop;screen="library";selected.clear();replaceIndex=action==="replace"?i:null;render();await loadCatalog();return;}
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
