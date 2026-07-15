/* LEXIS — main.js */
const GRAPH_DATA   = __GRAPH_DATA__;
const DOSSIER_DATA = __DOSSIER_DATA__;
const STATS        = __STATS_JSON__;
const SOURCES      = __SOURCES_DATA__;

const D = DOSSIER_DATA;

// Stats
document.getElementById('h-pages').textContent    = STATS.pages;
document.getElementById('h-hl').textContent       = STATS.highlights;
document.getElementById('h-nodes').textContent    = STATS.concepts;
document.getElementById('h-edges').textContent    = STATS.relations;

// Tooltip on highlights
const tip  = document.getElementById('tip');
const tipC = document.getElementById('tip-cat');
const tipR = document.getElementById('tip-reason');
document.querySelectorAll('mark.hl').forEach(el => {
  el.addEventListener('mouseenter', () => {
    tipC.textContent = (el.dataset.importance||'').toUpperCase() + ' · ' + (el.dataset.category||'');
    tipR.textContent = el.dataset.reason || '';
    const col = el.dataset.importance === 'critical' ? '#d63031' : el.dataset.importance === 'high' ? '#e6a817' : '#00cec9';
    tip.style.borderLeftColor = col;
    tipC.style.color = col;
    tip.classList.add('on');
  });
  el.addEventListener('mousemove', e => {
    tip.style.left = (e.clientX + 18) + 'px';
    tip.style.top  = (e.clientY - 10) + 'px';
  });
  el.addEventListener('mouseleave', () => tip.classList.remove('on'));
});

// Graph
const TC = {
  entity:    '#00cec9',
  process:   '#e6a817',
  tool:      '#00b894',
  technique: '#a29bfe',
  risk:      '#d63031',
  outcome:   '#fd79a8',
  concept:   '#74b9ff',
};

const cy = cytoscape({
  container: document.getElementById('graph-canvas'),
  elements: [
    ...GRAPH_DATA.nodes.map(n => ({
      data: {
        id: n.id, label: n.label, type: n.type,
        weight: n.weight || 0.5,
        color: TC[n.type] || '#74b9ff'
      }
    })),
    ...GRAPH_DATA.edges.map(e => ({
      data: {
        source: e.source, target: e.target,
        label: e.relation, weight: e.weight || 0.5
      }
    }))
  ],
  style: [
    {
      selector: 'node',
      style: {
        'shape': 'ellipse',
        'width':  ele => 36 + (ele.data('weight') || 0.5) * 48,
        'height': ele => 36 + (ele.data('weight') || 0.5) * 48,
        'background-color': 'data(color)',
        'background-opacity': 0.12,
        'border-color': 'data(color)',
        'border-width': 2.5,
        'label': 'data(label)',
        'color': '#ede8e0',
        'font-size': 11,
        'font-family': 'JetBrains Mono, monospace',
        'font-weight': 500,
        'text-valign': 'bottom',
        'text-margin-y': 7,
        'text-wrap': 'wrap',
        'text-max-width': 100,
        'shadow-blur': 24,
        'shadow-color': 'data(color)',
        'shadow-opacity': 0.7,
        'shadow-offset-x': 0,
        'shadow-offset-y': 0,
        'transition-property': 'border-width, background-opacity, shadow-blur',
        'transition-duration': '0.2s'
      }
    },
    {
      selector: 'node:hover',
      style: {
        'border-width': 4,
        'background-opacity': 0.3,
        'shadow-blur': 48,
        'z-index': 9999
      }
    },
    {
      selector: 'node:selected',
      style: {
        'border-width': 4,
        'background-opacity': 0.4,
        'shadow-blur': 60,
        'shadow-opacity': 1
      }
    },
    {
      selector: 'edge',
      style: {
        'width': ele => 1 + (ele.data('weight') || 0.5) * 2.5,
        'line-color': 'rgba(237,232,224,0.08)',
        'target-arrow-color': 'rgba(237,232,224,0.15)',
        'target-arrow-shape': 'triangle',
        'curve-style': 'bezier',
        'label': 'data(label)',
        'font-size': 8,
        'font-family': 'JetBrains Mono, monospace',
        'color': 'rgba(122,112,104,0.8)',
        'text-rotation': 'autorotate',
        'text-background-color': 'rgba(6,5,8,0.7)',
        'text-background-opacity': 1,
        'text-background-padding': '2px',
        'opacity': 0.8
      }
    },
    {
      selector: 'edge:hover',
      style: { 'line-color': 'rgba(237,232,224,0.3)', opacity: 1 }
    }
  ],
  layout: {
    name: 'cose',
    animate: true,
    animationDuration: 800,
    padding: 80,
    nodeRepulsion: 12000,
    idealEdgeLength: 160,
    gravity: 0.25,
    numIter: 1500,
    randomize: false
  },
  userZoomingEnabled: true,
  userPanningEnabled: true,
  boxSelectionEnabled: false
});

cy.one('layoutstop', () => { cy.resize(); cy.fit(undefined, 80); });
setTimeout(() => { cy.resize(); cy.fit(undefined, 80); }, 1000);

// Node hover popup
const pop   = document.getElementById('node-pop');
const popTy = document.getElementById('np-type');
const popNm = document.getElementById('np-name');
cy.on('mouseover', 'node', e => {
  const d = e.target.data();
  popTy.textContent = (d.type || 'concept').toUpperCase();
  popTy.style.color = d.color;
  popNm.textContent = d.label;
  pop.classList.add('on');
});
cy.on('mousemove', e => {
  const pos = e.originalEvent;
  if (pos) { pop.style.left = (pos.clientX + 20) + 'px'; pop.style.top = (pos.clientY - 20) + 'px'; }
});
cy.on('mouseout', 'node', () => pop.classList.remove('on'));

// Node click → scroll to highlight
cy.on('tap', 'node', e => {
  const lbl = e.target.data('label').toLowerCase().slice(0, 7);
  for (const m of document.querySelectorAll('mark.hl')) {
    if (m.textContent.toLowerCase().includes(lbl)) {
      m.scrollIntoView({ behavior: 'smooth', block: 'center' });
      const prev = m.style.outline;
      m.style.outline = '2px solid ' + (e.target.data('color') || '#e6a817');
      m.style.outlineOffset = '3px';
      setTimeout(() => { m.style.outline = prev; m.style.outlineOffset = ''; }, 2500);
      break;
    }
  }
});

// Graph legend
const legBar = document.getElementById('graph-bar');
Object.entries(TC).forEach(([type, color]) => {
  const d = document.createElement('div');
  d.className = 'leg';
  d.innerHTML = `<span class="leg-c" style="background:${color};box-shadow:0 0 6px ${color}80"></span>${type}`;
  legBar.appendChild(d);
});

// Dossier
const findsHTML = D.key_findings.map(f => `
  <div class="find-item">
    <div class="find-txt">${f.finding}</div>
    <div class="find-conf fc-${f.confidence}">◆ ${f.confidence}</div>
    ${f.implication ? `<div class="find-impl">${f.implication}</div>` : ''}
  </div>`).join('');

const gapsHTML = D.knowledge_gaps.map(g =>
  `<div class="gap-row">${g}</div>`).join('');

const stepsHTML = D.recommended_learning_path.map(s => `
  <div class="step-row">
    <span class="step-n">${String(s.step).padStart(2, '0')}</span>
    <div><div class="step-top">${s.topic}</div><div class="step-why">${s.reason}</div></div>
  </div>`).join('');

const anHTML = D.analogies.map(a => `
  <div class="an-row">
    <div class="an-con">${a.concept}</div>
    <div class="an-txt">${a.analogy}</div>
  </div>`).join('');

const threatHTML = D.threat_surface ? `
  <div class="dos-card threat-card full">
    <div class="threat-lbl">⚠ THREAT SURFACE</div>
    <div class="threat-txt">${D.threat_surface}</div>
  </div>` : '';

document.getElementById('s3-inner').innerHTML = `
  <div class="s3-head">
    <div class="s3-kicker">${D.classification} // ${new Date().toISOString().slice(0,10)}</div>
    <div class="s3-subject">${D.subject.toUpperCase()}</div>
    <div class="s3-summary">${D.executive_summary}</div>
  </div>
  <div class="dos-card">
    <div class="card-title">KEY FINDINGS</div>
    ${findsHTML || '<div style="color:#7a7068;font-size:.8rem">None extracted.</div>'}
  </div>
  <div class="dos-card">
    <div class="card-title">KNOWLEDGE GAPS</div>
    ${gapsHTML || '<div style="color:#7a7068;font-size:.8rem">None identified.</div>'}
  </div>
  <div class="dos-card">
    <div class="card-title">LEARNING PATH</div>
    ${stepsHTML || '<div style="color:#7a7068;font-size:.8rem">None generated.</div>'}
  </div>
  <div class="dos-card">
    <div class="card-title">ANALOGIES</div>
    ${anHTML || '<div style="color:#7a7068;font-size:.8rem">None generated.</div>'}
  </div>
  ${threatHTML}
  <div class="dos-card verdict-card full">
    <div class="verdict-lbl">VERDICT</div>
    <div class="verdict-txt">${D.verdict}</div>
  </div>`;

// Footer sources
const foot = document.getElementById('foot');
SOURCES.forEach(s => {
  const d = document.createElement('div');
  d.className = 'foot-src';
  d.innerHTML = `<a href="${s.url}" target="_blank" rel="noopener">${s.title || s.url}</a>`;
  foot.appendChild(d);
});

// Nav active section tracking
const sections = [
  { el: document.getElementById('s1'), id: 's1' },
  { el: document.getElementById('s2'), id: 's2' },
  { el: document.getElementById('s3'), id: 's3' }
];
const navLinks = document.querySelectorAll('.nav-a');
const obs = new IntersectionObserver(entries => {
  entries.forEach(en => {
    if (en.isIntersecting) {
      navLinks.forEach(l => l.classList.remove('on'));
      const l = document.querySelector(`.nav-a[href="#${en.target.id}"]`);
      if (l) l.classList.add('on');
    }
  });
}, { threshold: 0.3 });
sections.forEach(s => s.el && obs.observe(s.el));
