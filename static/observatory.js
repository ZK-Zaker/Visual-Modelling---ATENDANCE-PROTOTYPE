/* Shares app.js polling; no separate camera requests or client-generated observations. */
function renderPulse(s){
 const root=document.querySelector('#pulse-stats');if(!root)return;
 const safe=value=>String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 const put=(id,value)=>{const el=document.getElementById(id);if(el)el.innerHTML=value;};
 const live=Boolean(s.connected&&s.session);
 const people=live?s.people:[], identified=people.filter(p=>p.state==='student').length;
 const pending=people.filter(p=>['pending','intruder'].includes(p.state)).length;
 const usable=people.filter(p=>p.capture==='usable').length;
 const points=live?(s.pulse||[]).filter(p=>Date.parse(p.at)>=Date.now()-20*60*1000):[];
 const peak=points.length?Math.max(...points.map(p=>p.total)):null;
 root.innerHTML=[['Visibles',live?people.length:'—','Dentro del encuadre'],['Alumnos',live?identified:'—','Identidad confirmada'],['Por resolver',live?pending:'—','Desconocidos con referencia'],['Pico · 20 min',peak??'—','Máximo de personas visibles']].map(([label,value,note])=>`<div class="pulse-stat"><small>${label}</small><strong>${value}</strong><span>${note}</span></div>`).join('');
 document.querySelector('#pulse-mode').textContent=live?(s.session_title||'Sesión en curso'):s.connected?'Vista previa · análisis inactivo':'Sin captura activa';
 let insight;
 if(!live)insight=s.connected?'Inicia o reanuda una sesión para activar la detección y construir el pulso.':'Conecta la cámara e inicia una sesión. Sin captura no se estima la presencia.';
 else if(!people.length)insight='No hay personas detectadas en este encuadre. Esto no confirma que el salón esté vacío.';
 else if(pending)insight=`${pending} ${pending===1?'identidad pendiente visible':'identidades pendientes visibles'}. Puedes resolverlas en Most Wanted.`;
 else if(people.some(p=>p.identity===null))insight=`${people.filter(p=>p.identity===null).length} personas visibles todavía sin identidad confirmada.`;
 else insight=`${identified} alumnos identificados en el encuadre actual.`;
 document.querySelector('#pulse-insight').textContent=insight;
 const notices=document.getElementById('away-notices');
 if(notices){
   const alerts=live?(s.away||[]):[];
   const duration=n=>`${Math.floor(n/60)} min ${n%60} s`;
   const title={notice:'Fuera del radar',brief:'¿Pausa técnica?',long:'¿Se nos escapó?',returned:'De vuelta al radar'};
   notices.hidden=!live||(!alerts.length&&!s.group_warning);
   notices.innerHTML=(s.group_warning?'<p class="capture-caption">Pérdida colectiva de seguimiento: revisa el encuadre. Se suspenden los avisos individuales de las personas afectadas hasta volver a detectarlas.</p>':'')+alerts.slice(0,6).map(a=>`<div class="away-notice away-level-${safe(a.level)}"><span>${safe(title[a.level]||'Fuera de vista')}</span><strong>${safe(a.name)}</strong><small>${a.level==='returned'?'Volvió después de':'Fuera de vista durante'} ${duration(a.seconds)}</small></div>`).join('')+(alerts.length>6?`<p class="capture-caption">${alerts.length-6} avisos adicionales.</p>`:'')+(alerts.length?'<p class="capture-caption">Tiempo sin observar durante captura continua. La cámara no conoce el motivo. Umbrales ajustables en Settings.</p>':'');
 }
 const ratio=people.length?Math.round(100*usable/people.length):null;
 put('capture-quality',live&&people.length?`<div class="capture-meter" role="meter" aria-label="Personas con rostro útil en el último análisis" aria-valuemin="0" aria-valuemax="100" aria-valuenow="${ratio}"><span style="width:${ratio}%"></span></div><p class="capture-caption">${usable} de ${people.length} con rostro útil en el último análisis. ${usable<people.length?'La distancia, el ángulo, la nitidez o una oclusión pueden limitar la captura.':'Referencias aptas para comparar.'} Esto no es una probabilidad de identidad.</p>`:'');
 if(!points.length)put('pulse-chart',`<p>${live?'Esperando la primera muestra…':'El pulso se construye durante una sesión activa.'}</p>`);
 else{
   const W=680,H=205,L=32,R=660,T=18,B=168;
   const end=Date.parse(points[points.length-1].at),start=Math.min(Date.parse(points[0].at),end-2000);
   const ceiling=Math.max(4,...points.map(p=>p.total));
   const x=p=>L+(Date.parse(p.at)-start)/(end-start)*(R-L), y=n=>B-n/ceiling*(B-T);
   const clock=t=>new Date(t).toLocaleTimeString('es-MX',{hour:'2-digit',minute:'2-digit',second:'2-digit'});
   let svg=`<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="Personas visibles, alumnos identificados e identidades pendientes en los últimos veinte minutos"><title>Pulso de la clase. Eje horizontal: hora. Eje vertical: personas.</title>`;
   [...new Set([0,Math.round(ceiling/2),ceiling])].forEach(n=>svg+=`<line x1="${L}" y1="${y(n)}" x2="${R}" y2="${y(n)}" stroke="#49605a" stroke-dasharray="2 6"/><text x="3" y="${y(n)+4}">${n}</text>`);
   [['total','#d6ed91',''],['students','#84d5d3','7 4'],['pending','#f2b776','2 5']].forEach(([key,color,dash])=>{
     let path='';points.forEach((p,i)=>{const gap=i===0||p.gap||Date.parse(p.at)-Date.parse(points[i-1].at)>6000;path+=`${gap?'M':'L'}${x(p).toFixed(1)},${y(p[key]).toFixed(1)} `;});
     svg+=`<path d="${path}" fill="none" stroke="${color}" stroke-width="2.5" stroke-dasharray="${dash}"/>`;
     const last=points[points.length-1];svg+=`<circle cx="${x(last)}" cy="${y(last[key])}" r="4" fill="${color}"><title>${last[key]} personas · ${clock(end)}</title></circle>`;
   });
   svg+=`<text x="${L}" y="195">${clock(start)}</text><text x="${R}" y="195" text-anchor="end">${clock(end)}</text></svg>`;
   put('pulse-chart',svg);
 }
 put('pulse-events',(s.events||[]).map(e=>`<div class="signal-event ${safe(e.kind)}"><time>${safe(new Date(e.at).toLocaleTimeString('es-MX'))}</time><strong>${safe(e.label)}</strong><span>${safe(e.person||s.session_title)}</span></div>`).join('')||'<p class="caption">Sin eventos registrados para este curso.</p>');
}
document.addEventListener('DOMContentLoaded',()=>{
 const filter=document.querySelector('#wanted-filter');
 filter?.addEventListener('change',()=>{
   const cards=[...document.querySelectorAll('[data-case-state]')];
   cards.forEach(card=>card.hidden=filter.value!=='all'&&card.dataset.caseState!==filter.value);
   document.querySelector('#wanted-no-match').hidden=!cards.length||cards.some(card=>!card.hidden);
 });
});
