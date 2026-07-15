const GRAPH_DATA   = __GRAPH_DATA__;
const DOSSIER_DATA = __DOSSIER_DATA__;
const STATS        = __STATS_JSON__;
const SOURCES      = __SOURCES_DATA__;
const D = DOSSIER_DATA;

document.getElementById('h-pages').textContent = STATS.pages;
document.getElementById('h-hl').textContent    = STATS.highlights;
document.getElementById('h-nodes').textContent = STATS.concepts;
document.getElementById('h-edges').textContent = STATS.relations;

// Speech bubble tooltip
const tip=document.getElementById('tip'),tipC=document.getElementById('tip-cat'),tipR=document.getElementById('tip-reason');
document.querySelectorAll('mark.hl').forEach(el=>{
  el.addEventListener('mouseenter',()=>{
    const imp=el.dataset.importance||'';
    const col=imp==='critical'?'#e8192c':imp==='high'?'#c97d10':'#007a7a';
    tipC.textContent=imp.toUpperCase()+(el.dataset.category?' · '+el.dataset.category:'');
    tipC.style.color=col; tip.style.borderColor='#1a1517';
    tipR.textContent=el.dataset.reason||''; tip.classList.add('on');
  });
  el.addEventListener('mousemove',e=>{tip.style.left=(e.clientX+14)+'px';tip.style.top=(e.clientY-40)+'px'});
  el.addEventListener('mouseleave',()=>tip.classList.remove('on'));
});

// Graph — manga sketch aesthetic
const TC={
  entity:   {fill:'#00b4b4',border:'#007a7a'},
  process:  {fill:'#f5a623',border:'#a06000'},
  tool:     {fill:'#4caf50',border:'#1b5e20'},
  technique:{fill:'#9c88e8',border:'#4527a0'},
  risk:     {fill:'#ef5350',border:'#8b0000'},
  outcome:  {fill:'#f48fb1',border:'#880e4f'},
  concept:  {fill:'#64b5f6',border:'#0d47a1'},
};
const C=t=>(TC[t]||TC.concept);

const cy=cytoscape({
  container:document.getElementById('graph-canvas'),
  elements:[
    ...GRAPH_DATA.nodes.map(n=>({data:{id:n.id,label:n.label,type:n.type,weight:n.weight||.5,fill:C(n.type).fill,bdr:C(n.type).border}})),
    ...GRAPH_DATA.edges.map(e=>({data:{source:e.source,target:e.target,label:e.relation||'',weight:e.weight||.5,srcFill:C(GRAPH_DATA.nodes.find(n=>n.id===e.source)?.type).fill}}))
  ],
  style:[
    {selector:'node',style:{
      shape:'ellipse',
      width: ele=>72+(ele.data('weight')||.5)*64,
      height:ele=>72+(ele.data('weight')||.5)*64,
      'background-fill':'radial-gradient',
      'background-gradient-stop-colors':ele=>`rgba(255,255,255,.65) ${ele.data('fill')} ${ele.data('bdr')}`,
      'background-gradient-stop-positions':'0% 50% 100%',
      'background-gradient-direction':'to-bottom-right',
      'border-color':'data(bdr)',
      'border-width':3,
      label:'data(label)',
      'text-valign':'center','text-halign':'center',
      color:'#fff',
      'font-size':ele=>Math.max(9,13-ele.data('label').length*.38),
      'font-family':'Inter,sans-serif','font-weight':'700',
      'text-wrap':'wrap',
      'text-max-width':ele=>(72+(ele.data('weight')||.5)*64)-14,
      'text-shadow-blur':2,'text-shadow-color':'rgba(0,0,0,.45)','text-shadow-offset-x':0,'text-shadow-offset-y':1,
      'shadow-blur':18,'shadow-color':'data(fill)','shadow-opacity':.45,'shadow-offset-x':0,'shadow-offset-y':5,
      'transition-property':'width,height,shadow-blur','transition-duration':'180ms','z-index':1
    }},
    {selector:'node:hover',style:{
      width:ele=>(72+(ele.data('weight')||.5)*64)*1.15,
      height:ele=>(72+(ele.data('weight')||.5)*64)*1.15,
      'shadow-blur':44,'shadow-opacity':.85,'z-index':999
    }},
    {selector:'node:selected',style:{'border-width':5,'border-color':'#fff','shadow-blur':55,'z-index':1000}},
    {selector:'edge',style:{
      width:ele=>3.5+(ele.data('weight')||.5)*4.5,
      'line-color':'data(srcFill)','line-opacity':.45,
      'target-arrow-color':'data(srcFill)','target-arrow-shape':'triangle','arrow-scale':1.1,
      'curve-style':'bezier',label:'data(label)',
      'font-size':9,'font-family':'Inter,sans-serif','font-weight':'600',color:'#fff',
      'text-rotation':'autorotate','text-background-color':'rgba(26,21,23,.8)',
      'text-background-opacity':1,'text-background-padding':'3px','text-background-shape':'roundrectangle',opacity:.65
    }},
    {selector:'edge:hover',style:{'line-opacity':.9,opacity:1,'z-index':999}},
    {selector:'node.dim',style:{opacity:.1}},
    {selector:'edge.dim',style:{opacity:.05}}
  ],
  layout:{name:'cose',animate:true,animationDuration:1000,animationEasing:'ease-out-cubic',
    padding:80,nodeRepulsion:16000,idealEdgeLength:190,gravity:.2,numIter:2200,
    initialTemp:900,coolingFactor:.99,randomize:false,componentSpacing:90},
  userZoomingEnabled:true,userPanningEnabled:true,boxSelectionEnabled:false,minZoom:.2,maxZoom:3
});

cy.one('layoutstop',()=>{cy.resize();cy.fit(undefined,80)});
setTimeout(()=>{cy.resize();cy.fit(undefined,80)},1200);

// Gentle float after layout
cy.on('layoutstop',()=>{
  setInterval(()=>{
    if(cy.$(':grabbed').length)return;
    cy.nodes().forEach(n=>{
      const p=n.position();
      n.animate({position:{x:p.x+(Math.random()-.5)*2.5,y:p.y+(Math.random()-.5)*2.5}},{duration:2000,easing:'ease-in-out-sine',queue:false});
    });
  },2500);
});

// Hover: dim others
const pop=document.getElementById('node-pop'),popT=document.getElementById('np-type'),popN=document.getElementById('np-name');
cy.on('mouseover','node',e=>{
  const d=e.target.data();
  popT.textContent=(d.type||'concept').toUpperCase();popT.style.color=d.fill;
  popN.textContent=d.label; pop.classList.add('on');
  cy.elements().addClass('dim'); e.target.removeClass('dim');
  e.target.connectedEdges().removeClass('dim').connectedNodes().removeClass('dim');
});
cy.on('mouseout','node',()=>{pop.classList.remove('on');cy.elements().removeClass('dim')});
cy.on('mousemove',e=>{const v=e.originalEvent;if(v){pop.style.left=(v.clientX+16)+'px';pop.style.top=(v.clientY-55)+'px'}});
cy.on('tap','node',e=>{
  const lbl=e.target.data('label').toLowerCase().slice(0,6);
  for(const m of document.querySelectorAll('mark.hl')){
    if(m.textContent.toLowerCase().includes(lbl)){
      m.scrollIntoView({behavior:'smooth',block:'center'});
      m.style.outline=`3px solid ${e.target.data('fill')}`;m.style.outlineOffset='2px';
      setTimeout(()=>{m.style.outline='';m.style.outlineOffset=''},2500);break;
    }
  }
});

// Legend
const bar=document.getElementById('graph-bar');
Object.entries(TC).forEach(([type,c])=>{
  const d=document.createElement('div');d.className='leg';
  d.innerHTML=`<span class="leg-c" style="background:${c.fill};border-color:${c.border}"></span>${type}`;
  bar.appendChild(d);
});

// Dossier render
const finds=D.key_findings.map(f=>`<div class="find-item"><div class="find-txt">${f.finding}</div><div class="find-conf fc-${f.confidence}">◆ ${f.confidence}</div>${f.implication?`<div class="find-impl">${f.implication}</div>`:''}</div>`).join('');
const gaps=D.knowledge_gaps.map(g=>`<div class="gap-row">${g}</div>`).join('');
const steps=D.recommended_learning_path.map(s=>`<div class="step-row"><span class="step-n">${String(s.step).padStart(2,'0')}</span><div><div class="step-top">${s.topic}</div><div class="step-why">${s.reason}</div></div></div>`).join('');
const ans=D.analogies.map(a=>`<div class="an-row"><div class="an-con">${a.concept}</div><div class="an-txt">${a.analogy}</div></div>`).join('');
const threat=D.threat_surface?`<div class="dos-card threat-panel full"><div class="threat-lbl">⚠ THREAT SURFACE</div><div class="threat-txt">${D.threat_surface}</div></div>`:'';

document.getElementById('dos-content').innerHTML=`
<div class="dos-class">${D.classification} // ${new Date().toISOString().slice(0,10)}</div>
<div class="dos-subject">${D.subject.toUpperCase()}</div>
<div class="dos-summary">${D.executive_summary}</div>
<div class="dos-panels">
  <div class="dos-card"><div class="card-hd">Key Findings</div>${finds||'<span style="opacity:.4;font-size:.8rem">None.</span>'}</div>
  <div class="dos-card"><div class="card-hd">Knowledge Gaps</div>${gaps||'<span style="opacity:.4;font-size:.8rem">None.</span>'}</div>
  <div class="dos-card"><div class="card-hd">Learning Path</div>${steps||'<span style="opacity:.4;font-size:.8rem">None.</span>'}</div>
  <div class="dos-card"><div class="card-hd">Analogies</div>${ans||'<span style="opacity:.4;font-size:.8rem">None.</span>'}</div>
  ${threat}
  <div class="dos-card verdict-panel full"><div class="verdict-lbl">Verdict</div><div class="verdict-txt">${D.verdict}</div></div>
</div>`;

// Footer
const foot=document.getElementById('foot');
SOURCES.forEach(s=>{const d=document.createElement('div');d.className='foot-src';d.innerHTML=`<a href="${s.url}" target="_blank" rel="noopener">${s.title||s.url}</a>`;foot.appendChild(d)});

// Nav highlight
const ios=new IntersectionObserver(entries=>entries.forEach(en=>{if(en.isIntersecting){document.querySelectorAll('.nav-a').forEach(l=>l.classList.remove('on'));const l=document.querySelector(`.nav-a[href="#${en.target.id}"]`);if(l)l.classList.add('on')}}),{threshold:.25});
['s1','s2','s3'].forEach(id=>{const el=document.getElementById(id);if(el)ios.observe(el)});
