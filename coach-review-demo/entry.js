/* The explicit demo boot never loads app/auth/theme scripts or reads app storage. */
(function(){"use strict";
 const params=new URLSearchParams(location.search),demo=params.has("fmzDemo");
 const valid=demo&&params.get("fmzDemo")==="6e8"&&["nl","en","de"].includes(params.get("lang")||"nl")&&["light","dark"].includes(params.get("theme")||"light")&&[...params.keys()].every(k=>["fmzDemo","lang","theme"].includes(k)&&params.getAll(k).length===1);
 const allowed=["assets/theme-authority.js?v=20260907-theme1","https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2","config.js","assets/vendor/zxing-browser-0.2.1.min.js?v=20260827-phase4fd-owner-barcode1","app.js?v=20260910-effort-align1"];
 window.FMZ_6E8_BOOT=Object.freeze({loadLive(sources){if(!demo)for(const src of sources){if(!allowed.includes(src))throw new Error("Unapproved bootstrap");document.write('<script src="'+src+'"><\/script>');}}});
 if(!demo)return;
 document.documentElement.dataset.fmzDemo="6e8";
 const css=document.createElement("link");css.rel="stylesheet";css.href="coach-review-demo/panel.css";document.head.append(css);
 document.addEventListener("DOMContentLoaded",()=>{
  document.title="FitMetZorge | Synthetic Coach Review";
  document.body.className="fmz-demo-host";document.body.replaceChildren();
  const main=document.createElement("main");main.id="synthetic-panel";
  const locale=params.get("lang")||"nl",words={nl:["Synthetische demo","Sluiten","Heropenen"],en:["Synthetic demo","Close","Reopen"],de:["Synthetische Demo","Schliessen","Erneut oeffnen"]}[locale]||["Invalid demo","Close","Reopen"];
  const label=document.createElement("h1");label.textContent="FitMetZorge / "+words[0];
  const button=document.createElement("button");button.type="button";button.textContent=words[1];
  const area=document.createElement("div");area.className="demo-frame-area";main.append(label,button,area);document.body.append(main);
  function open(){
   area.replaceChildren();
   if(!valid){area.textContent="Ongeldige demo-instellingen / Invalid demo settings / Ungueltige Demo-Einstellungen";return;}
   const frame=document.createElement("iframe");frame.title="Synthetic FitMetZorge coach review";frame.setAttribute("sandbox","allow-scripts");
   frame.referrerPolicy="no-referrer";frame.src="coach-review-demo/index.html?lang="+(params.get("lang")||"nl")+"&theme="+(params.get("theme")||"light");area.append(frame);
  }
  let opened=true;button.addEventListener("click",()=>{opened=!opened;if(opened)open();else area.replaceChildren();button.textContent=words[opened?1:2];});
  open();
 },{once:true});
})();
