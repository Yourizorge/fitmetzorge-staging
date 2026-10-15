'use strict';
(()=>{
 const cold=document.body.hasAttribute('data-offline-shell');
 const words={
  title:['Toegang geblokkeerd','Access blocked','Zugriff gesperrt'],
  status:['De lokale server is niet bereikbaar. Je bent hier niet aangemeld.','The local server is unavailable. You are not signed in here.','Der lokale Server ist nicht erreichbar. Du bist hier nicht angemeldet.'],
  privacy:['Accountgegevens en concepten blijven verborgen totdat de server je toegang opnieuw heeft gecontroleerd.','Account data and drafts remain hidden until the server has verified your access again.','Kontodaten und Entwuerfe bleiben verborgen, bis der Server deinen Zugriff erneut geprueft hat.'],
  drafts:['Eerder bewaarde concepten kunnen nog op dit apparaat staan. Na opnieuw aanmelden kun je ze controleren en zelf verzenden.','Previously saved drafts may still be on this device. Sign in again to review and explicitly submit them.','Zuvor gespeicherte Entwuerfe koennen noch auf diesem Geraet liegen. Nach erneuter Anmeldung kannst du sie pruefen und selbst senden.'],
  reconnect:['Opnieuw verbinden','Reconnect','Erneut verbinden'],
  note:['Alleen deze algemene pagina is offline beschikbaar. Er wordt niets automatisch verzonden.','Only this generic page is available offline. Nothing is sent automatically.','Nur diese allgemeine Seite ist offline verfuegbar. Nichts wird automatisch gesendet.'],
  online:['Verbinding lijkt hersteld. Verbind opnieuw om je toegang door de server te laten controleren.','Connection appears restored. Reconnect so the server can verify your access.','Verbindung scheint wiederhergestellt. Erneut verbinden, damit der Server deinen Zugriff pruefen kann.'],
  live:['Offline: nieuwe registraties blijven alleen op dit apparaat totdat je ze zelf controleert en verzendt.','Offline: new records stay only on this device until you explicitly check and submit them.','Offline: Neue Eintraege bleiben nur auf diesem Geraet, bis du sie selbst pruefst und sendest.'],
  ready:['Algemene offlinepagina gereed. Accountgegevens worden niet gecachet.','Generic offline page ready. Account data is not cached.','Allgemeine Offline-Seite bereit. Kontodaten werden nicht zwischengespeichert.'],
  unavailable:['Offlinepagina niet beschikbaar. Opnieuw openen vereist de lokale server.','Offline page unavailable. Reopening requires the local server.','Offline-Seite nicht verfuegbar. Zum erneuten Oeffnen wird der lokale Server benoetigt.'],
  light:['Licht','Light','Hell'],dark:['Donker','Dark','Dunkel'],language:['Taal','Language','Sprache'],theme:['Thema','Theme','Design']
 };
 const lang=document.querySelector('#lang'),theme=document.querySelector('#theme');
 let index=0,ready=false,restored=false;
 // Device display choices only. No account preferences, IDs or auth state.
 try{const p=JSON.parse(localStorage.getItem('fmz-shell-display-v1'));if(p&&['nl','en','de'].includes(p.language)&&['light','dark'].includes(p.theme)){index=['nl','en','de'].indexOf(p.language);lang.value=String(index);theme.value=p.theme;}}catch(_){}
 function paint(){
  index=Number(lang.value);if(!Number.isInteger(index)||index<0||index>2)index=0;
  document.documentElement.lang=['nl','en','de'][index];document.body.dataset.theme=theme.value==='dark'?'dark':'light';
  lang.setAttribute('aria-label',words.language[index]);theme.setAttribute('aria-label',words.theme[index]);
  theme.options[0].textContent=words.light[index];theme.options[1].textContent=words.dark[index];
  if(cold){for(const key of ['title','status','privacy','drafts','reconnect','note'])document.querySelector('#shell-'+key).textContent=words[key][index];if(restored)document.querySelector('#shell-status').textContent=words.online[index];}
  else{const node=document.querySelector('#offline-status');if(node)node.textContent=words[!navigator.onLine?'live':ready?'ready':'unavailable'][index];}
 }
 function change(){paint();try{localStorage.setItem('fmz-shell-display-v1',JSON.stringify({language:['nl','en','de'][index],theme:theme.value==='dark'?'dark':'light'}));}catch(_){} }
 lang.addEventListener('change',change);theme.addEventListener('change',change);
 window.addEventListener('offline',()=>{restored=false;paint();});window.addEventListener('online',()=>{restored=true;paint();});
 if(cold)document.querySelector('#shell-reconnect').onclick=()=>location.replace('/');
 else if(location.hostname==='127.0.0.1'&&'serviceWorker' in navigator){
  navigator.serviceWorker.register('/offline_sw.js',{scope:'/',updateViaCache:'none'}).then(()=>navigator.serviceWorker.ready).then(()=>{ready=true;paint();}).catch(()=>{ready=false;paint();});
 }
 paint();
})();
