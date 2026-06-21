import React, { useEffect, useRef } from 'react';
import * as d3 from 'd3';
import { SDM_NODES, SDM_LINKS, EXPANSION_LINKS, COLORS, LINK_COLORS, EXP_LINK_COLORS } from '../data/sdmData.js';

const BASE_RADIUS = {
  root: 32, group: 24, dataProduct: 21, attribute: 9,
  policy: 19, cdm: 20, entity: 10, policyChecker: 19,
};

const LINK_DISTANCE = {
  hierarchy: 88, hasPolicy: 270, implementedBy: 230, mapsTo: 290,
};

function nodeColor(d) {
  if (d.type === 'root')  return COLORS.root;
  if (d.type === 'group') return COLORS[d.category] ?? '#546e7a';
  return COLORS[d.type] ?? '#999';
}

function nodeRadius(d, scale = 1) {
  return (BASE_RADIUS[d.type] ?? 10) * scale;
}

// Compute 2-hop neighborhood including expansion links.
// Hub nodes (root/group) are allowed INTO the neighborhood but never used
// as bridges — without this, traversing grp-pc brings in every sibling node.
function get2HopNeighborhood(centerId, simNodes, extraLinks = []) {
  const nodeIdSet = new Set(simNodes.map(n => n.id));
  const nodeType  = Object.fromEntries(simNodes.map(n => [n.id, n.type]));
  const isHub     = id => nodeType[id] === 'root' || nodeType[id] === 'group';

  const allLinks = [...SDM_LINKS, ...extraLinks].map(l => ({
    s: typeof l.source === 'object' ? l.source.id : l.source,
    t: typeof l.target === 'object' ? l.target.id : l.target,
  })).filter(l => nodeIdSet.has(l.s) && nodeIdSet.has(l.t));

  const neighborhood = new Set([centerId]);
  for (let hop = 0; hop < 2; hop++) {
    const toAdd = new Set();
    allLinks.forEach(({ s, t }) => {
      if (neighborhood.has(s) && !isHub(s)) toAdd.add(t);
      if (neighborhood.has(t) && !isHub(t)) toAdd.add(s);
    });
    toAdd.forEach(id => neighborhood.add(id));
  }
  return neighborhood;
}

// ── Main component ────────────────────────────────────────────────────────────
export default function SDMGraph({
  svgRef, onNodeClick, onNodeHover,
  visibleTypes, highlightLink,
  nodeScale, chargeStrength, linkDistMult,
  exploreMode, showAllRelations,
}) {
  const simulationRef     = useRef(null);
  const nodesMapRef       = useRef({});    // id → D3 sim node (has live x,y)
  const simNodesRef       = useRef([]);
  const allNodesRef       = useRef(null);  // D3 selection of .node groups
  const labelsRef         = useRef(null);
  const hierLinksRef      = useRef(null);
  const crossLinksRef     = useRef(null);
  const crossLabelsRef    = useRef(null);
  const allExpGRef        = useRef(null);  // DOM element of global show-all <g>
  const expansionGRef     = useRef(null);  // DOM element of focus expansion <g>
  const neighborhoodRef   = useRef(null);  // Set of visible neighbor IDs | null
  const pinnedNodeRef     = useRef(null);  // currently pinned sim node

  // ── Full rebuild ──────────────────────────────────────────────────────────
  useEffect(() => {
    const width  = svgRef.current?.parentElement?.clientWidth  || window.innerWidth;
    const height = (svgRef.current?.parentElement?.clientHeight || window.innerHeight) - 48;

    const svg = d3.select(svgRef.current).attr('width', width).attr('height', height);
    svg.selectAll('*').remove();

    const defs = svg.append('defs');
    // Cross-link arrows
    ['hasPolicy','implementedBy','mapsTo'].forEach(type => {
      defs.append('marker').attr('id',`arrow-${type}`).attr('viewBox','0 -5 10 10').attr('refX',22).attr('refY',0).attr('markerWidth',6).attr('markerHeight',6).attr('orient','auto')
        .append('path').attr('d','M0,-5L10,0L0,5').attr('fill',LINK_COLORS[type]);
    });
    // Expansion-link arrows
    Object.entries(EXP_LINK_COLORS).forEach(([type, color]) => {
      defs.append('marker').attr('id',`arrow-exp-${type}`).attr('viewBox','0 -5 10 10').attr('refX',18).attr('refY',0).attr('markerWidth',5).attr('markerHeight',5).attr('orient','auto')
        .append('path').attr('d','M0,-5L10,0L0,5').attr('fill',color);
    });

    const g = svg.append('g');
    svg.call(d3.zoom().scaleExtent([0.12,3.5]).on('zoom', ev => g.attr('transform', ev.transform)));

    // Filter nodes/links
    const active = new Set(Object.entries(visibleTypes).filter(([,v])=>v).map(([k])=>k));
    const visNodes = SDM_NODES.filter(n => n.type==='root'||n.type==='group'||active.has(n.category??n.type));
    const visIds   = new Set(visNodes.map(n=>n.id));
    const visLinks = SDM_LINKS.filter(l => visIds.has(l.source)&&visIds.has(l.target));

    const nodes = visNodes.map(d=>({...d}));
    const links = visLinks.map(d=>({...d}));

    // Store for expansion effect
    simNodesRef.current = nodes;
    nodesMapRef.current = {};
    nodes.forEach(n => { nodesMapRef.current[n.id] = n; });

    const charge = d3.forceManyBody().strength(d => {
      if (d.type==='root')  return chargeStrength*3.4;
      if (d.type==='group') return chargeStrength*2.3;
      return chargeStrength;
    });
    const linkForce = d3.forceLink(links).id(d=>d.id)
      .distance(d=>(LINK_DISTANCE[d.type]??88)*linkDistMult)
      .strength(d=>({hierarchy:1.0,hasPolicy:0.18,implementedBy:0.18,mapsTo:0.12}[d.type]??0.5));

    const simulation = d3.forceSimulation(nodes)
      .force('link',    linkForce)
      .force('charge',  charge)
      .force('center',  d3.forceCenter(width/2, height/2))
      .force('collide', d3.forceCollide().radius(d=>nodeRadius(d,nodeScale)+26))
      .force('x', d3.forceX(width/2).strength(0.03))
      .force('y', d3.forceY(height/2).strength(0.03));
    simulationRef.current = simulation;

    // ── Hier links ──────────────────────────────────────────────────────
    const hierLinks = g.append('g').attr('class','hier-links')
      .selectAll('line').data(links.filter(l=>l.type==='hierarchy')).enter().append('line')
      .attr('stroke', LINK_COLORS.hierarchy).attr('stroke-width',1.3).attr('opacity',0.5);
    hierLinksRef.current = hierLinks;

    // ── Cross-domain links ───────────────────────────────────────────────
    const crossTypes = ['hasPolicy','implementedBy','mapsTo'];
    const crossData  = links.filter(l=>crossTypes.includes(l.type));
    const crossLinks = g.append('g').attr('class','cross-links')
      .selectAll('line').data(crossData).enter().append('line')
      .attr('stroke',d=>LINK_COLORS[d.type]).attr('stroke-width',1.6).attr('stroke-dasharray','6,4')
      .attr('opacity',d=>(highlightLink===null||highlightLink===d.type)?0.72:0.1)
      .attr('marker-end',d=>`url(#arrow-${d.type})`);
    crossLinksRef.current = crossLinks;

    const crossLabels = g.append('g').attr('class','cross-labels')
      .selectAll('text').data(crossData).enter().append('text')
      .attr('font-size',8.5).attr('fill',d=>LINK_COLORS[d.type]).attr('font-family','Roboto Mono, monospace')
      .attr('text-anchor','middle').attr('pointer-events','none')
      .attr('opacity',d=>(highlightLink===null||highlightLink===d.type)?0.8:0)
      .text(d=>d.label??d.type);
    crossLabelsRef.current = crossLabels;

    // ── Global show-all expansion links (managed by show-all effect) ────
    const allExpG = g.append('g').attr('class','all-exp-links');
    allExpGRef.current = allExpG.node();

    // ── Focus expansion links group (populated by expansion effect) ──────
    const expG = g.append('g').attr('class','expansion-links');
    expansionGRef.current = expG.node();

    // ── Node groups ──────────────────────────────────────────────────────
    const nodeGroup = g.append('g').attr('class','nodes')
      .selectAll('.node').data(nodes).enter().append('g')
      .attr('class','node').style('cursor','pointer')
      .on('click',(_,d)=>onNodeClick(d))
      .on('mouseenter',(event,d)=>{
        if(onNodeHover) onNodeHover(event.pageX, event.pageY, d);
        d3.select(event.currentTarget).select('circle.main').attr('stroke-width',3.5);
      })
      .on('mouseleave',event=>{
        if(onNodeHover) onNodeHover(null,null,null);
        d3.select(event.currentTarget).select('circle.main').attr('stroke-width',d=>(d.type==='root'||d.type==='group')?2.5:1.5);
      })
      .call(d3.drag()
        .on('start',(ev,d)=>{ if(!ev.active) simulation.alphaTarget(0.3).restart(); d.fx=d.x; d.fy=d.y; })
        .on('drag', (ev,d)=>{ d.fx=ev.x; d.fy=ev.y; })
        .on('end',  (ev,d)=>{ if(!ev.active) simulation.alphaTarget(0); d.fx=null; d.fy=null; })
      );
    allNodesRef.current = nodeGroup;

    nodeGroup.filter(d=>d.type==='root'||d.type==='group')
      .append('circle').attr('r',d=>nodeRadius(d,nodeScale)+6).attr('fill','none')
      .attr('stroke',d=>nodeColor(d)).attr('stroke-width',1.5).attr('opacity',0.28);

    nodeGroup.append('circle').attr('class','main')
      .attr('r',d=>nodeRadius(d,nodeScale)).attr('fill',d=>nodeColor(d))
      .attr('stroke','#fff').attr('stroke-width',d=>(d.type==='root'||d.type==='group')?2.5:1.5)
      .attr('filter',d=>(d.type==='root'||d.type==='group')?'drop-shadow(0 2px 6px rgba(0,0,0,0.25))':null);

    nodeGroup.filter(d=>d.type==='root'||d.type==='group')
      .append('text')
      .attr('text-anchor','middle').attr('dominant-baseline','central')
      .attr('font-size',d=>d.type==='root'?20:14)
      .attr('fill','rgba(255,255,255,0.9)').attr('pointer-events','none')
      .text(d=>d.icon??'');

    const labels = g.append('g').attr('class','labels')
      .selectAll('text').data(nodes).enter().append('text')
      .attr('font-size',d=>['root','group'].includes(d.type)?12:['attribute','entity'].includes(d.type)?8.5:10.5)
      .attr('fill','#2c3e50')
      .attr('font-family',d=>['attribute','entity'].includes(d.type)?'Roboto Mono, monospace':'Inter, sans-serif')
      .attr('font-weight',d=>['root','group'].includes(d.type)?'700':'500')
      .attr('text-anchor','middle').attr('pointer-events','none')
      .text(d=>d.label);
    labelsRef.current = labels;

    // ── Tick ────────────────────────────────────────────────────────────
    simulation.on('tick', () => {
      hierLinks .attr('x1',d=>d.source.x).attr('y1',d=>d.source.y).attr('x2',d=>d.target.x).attr('y2',d=>d.target.y);
      crossLinks.attr('x1',d=>d.source.x).attr('y1',d=>d.source.y).attr('x2',d=>d.target.x).attr('y2',d=>d.target.y);
      crossLabels.attr('x',d=>(d.source.x+d.target.x)/2).attr('y',d=>(d.source.y+d.target.y)/2-5);
      nodeGroup.attr('transform',d=>`translate(${d.x},${d.y})`);
      labels.attr('x',d=>d.x).attr('y',d=>d.y+nodeRadius(d,nodeScale)+12);
    });

    return () => simulation.stop();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [visibleTypes, nodeScale]);

  // ── Hot-update physics ────────────────────────────────────────────────────
  useEffect(() => {
    const sim = simulationRef.current;
    if (!sim) return;
    sim.force('charge').strength(d=>{
      if(d.type==='root')  return chargeStrength*3.4;
      if(d.type==='group') return chargeStrength*2.3;
      return chargeStrength;
    });
    sim.force('link').distance(d=>(LINK_DISTANCE[d.type]??88)*linkDistMult);
    sim.alpha(0.45).restart();
  }, [chargeStrength, linkDistMult]);

  // ── Dynamic exploration mode ──────────────────────────────────────────────
  useEffect(() => {
    const sim  = simulationRef.current;
    const cl   = crossLinksRef.current;
    const clb  = crossLabelsRef.current;
    const an   = allNodesRef.current;
    const la   = labelsRef.current;
    const hl   = hierLinksRef.current;
    const expG = d3.select(expansionGRef.current);
    if (!sim || !cl) return;

    sim.force('focus-x', null);
    sim.force('focus-y', null);
    sim.on('tick.expansion', null);
    expG.selectAll('*').remove();

    if (!exploreMode) {
      neighborhoodRef.current = null;
      an?.attr('opacity', 1);
      la?.attr('opacity', 1);
      hl?.attr('opacity', 0.5);
      cl.attr('stroke-width', d=>highlightLink===d.type?2.6:1.6)
        .attr('opacity', d=>(highlightLink===null||highlightLink===d.type)?0.72:0.1);
      clb.attr('opacity', d=>(highlightLink===null||highlightLink===d.type)?0.8:0);
      sim.alpha(0.2).restart();
      return;
    }

    const { seedNode, expanded } = exploreMode;
    const simNodes  = simNodesRef.current ?? [];
    const nodeIdSet = new Set(simNodes.map(n => n.id));
    const nm        = nodesMapRef.current;

    // Build full bidirectional adjacency from all link types
    const adj = {};
    simNodes.forEach(n => { adj[n.id] = new Set(); });
    [...SDM_LINKS, ...EXPANSION_LINKS].forEach(l => {
      const s = typeof l.source === 'object' ? l.source.id : l.source;
      const t = typeof l.target === 'object' ? l.target.id : l.target;
      if (!nodeIdSet.has(s) || !nodeIdSet.has(t)) return;
      adj[s].add(t);
      adj[t].add(s);
    });

    // Visible = every expanded node + all their direct neighbors
    const visible = new Set();
    expanded.forEach(id => {
      if (!nodeIdSet.has(id)) return;
      visible.add(id);
      adj[id]?.forEach(nid => visible.add(nid));
    });
    neighborhoodRef.current = visible;

    an?.attr('opacity', d => visible.has(d.id) ? 1 : 0.04);
    la?.attr('opacity', d => visible.has(d.id) ? 1 : 0.03);
    hl?.attr('opacity', d => {
      const s = d.source?.id ?? d.source, t = d.target?.id ?? d.target;
      return (visible.has(s) && visible.has(t)) ? 0.5 : 0.03;
    });
    cl.attr('stroke-width', d => highlightLink === d.type ? 2.6 : 1.6)
      .attr('opacity', d => {
        const s = d.source?.id ?? d.source, t = d.target?.id ?? d.target;
        if (!visible.has(s) || !visible.has(t)) return 0.03;
        return (highlightLink === null || highlightLink === d.type) ? 0.75 : 0.1;
      });
    clb.attr('opacity', d => {
      const s = d.source?.id ?? d.source, t = d.target?.id ?? d.target;
      if (!visible.has(s) || !visible.has(t)) return 0;
      return (highlightLink === null || highlightLink === d.type) ? 0.8 : 0;
    });

    // Expansion links between all visible nodes
    const visExpLinks = EXPANSION_LINKS.filter(l =>
      visible.has(l.source) && visible.has(l.target) &&
      nodeIdSet.has(l.source) && nodeIdSet.has(l.target)
    );

    const expLines = expG.selectAll('line.exp').data(visExpLinks).enter()
      .append('line').attr('class', 'exp')
      .attr('stroke', d => EXP_LINK_COLORS[d.type] ?? '#999')
      .attr('stroke-width', 2.0).attr('opacity', 0.85)
      .attr('marker-end', d => `url(#arrow-exp-${d.type})`);

    const expLabels = expG.selectAll('text.exp').data(visExpLinks).enter()
      .append('text').attr('class', 'exp')
      .attr('font-size', 9).attr('fill', d => EXP_LINK_COLORS[d.type] ?? '#999')
      .attr('font-family', 'Roboto Mono, monospace').attr('text-anchor', 'middle')
      .attr('pointer-events', 'none').attr('font-weight', '600')
      .text(d => d.label ?? d.type);

    const expLabelBg = expG.selectAll('rect.exp').data(visExpLinks).enter()
      .insert('rect', 'text.exp').attr('class', 'exp')
      .attr('rx', 3).attr('ry', 3).attr('height', 13)
      .attr('fill', '#fff').attr('opacity', 0.75).attr('pointer-events', 'none');

    // Parameter satellites for the explore seed if it is a policyChecker
    let paramLines = null, paramCircles = null, paramIcons = null;
    let paramLbls  = null, paramSubs    = null;
    const PR = 80;

    if (seedNode.type === 'policyChecker') {
      const det = seedNode.detail ?? {};
      const GX_SHORT = {
        'ExpectColumnValuesToNotBeNull':            'not null',
        'ExpectColumnValuesToBeInSet':              'in set',
        'ExpectColumnValuesToBeNull':               'is null',
        'ExpectColumnValuesToBeNull (conditional)': 'cond. null',
        'ExpectTableRowCountToBeBetween':           'row count',
        'ExpectColumnKLDivergenceToBeLessThan':     'KL diverge',
        'ExpectColumnValuesToBeBetween':            'between',
      };
      const params = [
        det.expectation  && { label: GX_SHORT[det.expectation] ?? det.expectation, sublabel: 'GX operation', icon: '⚙', color: '#5c6bc0' },
        det.column       && { label: det.column,      sublabel: 'column',       icon: '⊏', color: '#00897b' },
        det.valueSet     && { label: det.valueSet,    sublabel: 'value set',    icon: '≡', color: '#e64a19' },
        det.condition    && { label: det.condition,   sublabel: 'condition',    icon: '?', color: '#f9a825' },
        (det.min !== undefined || det.minValue !== undefined) && {
          label: `${det.min ?? det.minValue} – ${det.max ?? det.maxValue}`,
          sublabel: 'range', icon: '↔', color: '#388e3c',
        },
        det.threshold !== undefined && { label: String(det.threshold), sublabel: 'threshold',    icon: '≤', color: '#7b1fa2' },
        det.distribution            && { label: det.distribution,      sublabel: 'distribution', icon: '∿', color: '#00695c' },
        det.mostly      && { label: det.mostly,      sublabel: 'mostly',   icon: '%', color: '#0277bd' },
        det.dqr         && { label: det.dqr,         sublabel: 'DQR ref',  icon: '#', color: '#6d4c41' },
        det.dataProduct && { label: det.dataProduct, sublabel: 'dataset',  icon: '▤', color: '#37474f' },
      ].filter(Boolean);

      if (params.length > 0) {
        params.forEach((p, i) => {
          p.angle = -Math.PI / 2 + (2 * Math.PI * i) / params.length;
        });
        paramLines = expG.selectAll('.param-line').data(params).enter()
          .append('line').attr('class','param-line')
          .attr('stroke', d=>d.color).attr('stroke-width',1.5)
          .attr('stroke-dasharray','4 3').attr('opacity',0.7);
        paramCircles = expG.selectAll('.param-circle').data(params).enter()
          .append('circle').attr('class','param-circle')
          .attr('r',13).attr('fill', d=>d.color)
          .attr('stroke','#fff').attr('stroke-width',2).attr('opacity',0.9);
        paramIcons = expG.selectAll('.param-icon').data(params).enter()
          .append('text').attr('class','param-icon')
          .attr('text-anchor','middle').attr('dominant-baseline','central')
          .attr('font-size',10).attr('fill','#fff').attr('pointer-events','none')
          .text(d=>d.icon);
        paramLbls = expG.selectAll('.param-lbl').data(params).enter()
          .append('text').attr('class','param-lbl')
          .attr('text-anchor','middle').attr('dominant-baseline','auto')
          .attr('font-size',9.5).attr('fill', d=>d.color)
          .attr('font-family','Roboto Mono, monospace').attr('font-weight','700')
          .attr('pointer-events','none')
          .text(d => d.label.length > 15 ? d.label.slice(0,13)+'…' : d.label);
        paramSubs = expG.selectAll('.param-sub').data(params).enter()
          .append('text').attr('class','param-sub')
          .attr('text-anchor','middle').attr('dominant-baseline','auto')
          .attr('font-size',7.5).attr('fill','#95a5a6').attr('pointer-events','none')
          .text(d=>d.sublabel);
      }
    }

    sim.on('tick.expansion', () => {
      expLines
        .attr('x1', d=>nm[d.source]?.x??0).attr('y1', d=>nm[d.source]?.y??0)
        .attr('x2', d=>nm[d.target]?.x??0).attr('y2', d=>nm[d.target]?.y??0);
      expLabels
        .attr('x', d=>((nm[d.source]?.x??0)+(nm[d.target]?.x??0))/2)
        .attr('y', d=>((nm[d.source]?.y??0)+(nm[d.target]?.y??0))/2 - 6);
      expLabelBg
        .attr('x', d=>((nm[d.source]?.x??0)+(nm[d.target]?.x??0))/2 - 28)
        .attr('y', d=>((nm[d.source]?.y??0)+(nm[d.target]?.y??0))/2 - 17)
        .attr('width', d=>(d.label?.length??4)*5.6 + 6);
      if (paramLines) {
        const cx = nm[seedNode.id]?.x ?? 0, cy = nm[seedNode.id]?.y ?? 0;
        paramLines.attr('x1',cx).attr('y1',cy)
          .attr('x2', d=>cx+PR*Math.cos(d.angle)).attr('y2', d=>cy+PR*Math.sin(d.angle));
        paramCircles.attr('cx', d=>cx+PR*Math.cos(d.angle)).attr('cy', d=>cy+PR*Math.sin(d.angle));
        paramIcons.attr('x', d=>cx+PR*Math.cos(d.angle)).attr('y', d=>cy+PR*Math.sin(d.angle));
        paramLbls.attr('x', d=>cx+(PR+22)*Math.cos(d.angle)).attr('y', d=>cy+(PR+22)*Math.sin(d.angle)+2);
        paramSubs.attr('x', d=>cx+(PR+22)*Math.cos(d.angle)).attr('y', d=>cy+(PR+22)*Math.sin(d.angle)+13);
      }
    });

    sim.alpha(0.3).restart();
    return () => { sim.on('tick.expansion', null); };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [exploreMode, visibleTypes, nodeScale]);

  // ── Global "show all relations" ───────────────────────────────────────────
  useEffect(() => {
    const sim    = simulationRef.current;
    const allExpG = d3.select(allExpGRef.current);
    if (!sim || !allExpGRef.current) return;

    sim.on('tick.showall', null);
    allExpG.selectAll('*').remove();

    if (!showAllRelations || exploreMode) return; // explore mode takes priority

    const nodeIdSet = new Set(simNodesRef.current.map(n => n.id));
    const allLinks  = EXPANSION_LINKS.filter(l => nodeIdSet.has(l.source) && nodeIdSet.has(l.target));

    const saLines = allExpG.selectAll('line').data(allLinks).enter().append('line')
      .attr('stroke', d => EXP_LINK_COLORS[d.type] ?? '#999')
      .attr('stroke-width', 1.8).attr('opacity', 0.72)
      .attr('marker-end', d => `url(#arrow-exp-${d.type})`);

    const saLabels = allExpG.selectAll('text').data(allLinks).enter().append('text')
      .attr('font-size', 8.5).attr('fill', d => EXP_LINK_COLORS[d.type] ?? '#999')
      .attr('font-family', 'Roboto Mono, monospace').attr('text-anchor', 'middle')
      .attr('pointer-events', 'none').attr('font-weight', '600')
      .text(d => d.label ?? d.type);

    const nm = nodesMapRef.current;
    sim.on('tick.showall', () => {
      saLines
        .attr('x1', d => nm[d.source]?.x ?? 0).attr('y1', d => nm[d.source]?.y ?? 0)
        .attr('x2', d => nm[d.target]?.x ?? 0).attr('y2', d => nm[d.target]?.y ?? 0);
      saLabels
        .attr('x', d => ((nm[d.source]?.x ?? 0) + (nm[d.target]?.x ?? 0)) / 2)
        .attr('y', d => ((nm[d.source]?.y ?? 0) + (nm[d.target]?.y ?? 0)) / 2 - 5);
    });

    sim.alpha(0.15).restart();
    return () => { sim.on('tick.showall', null); };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [showAllRelations, exploreMode, visibleTypes, nodeScale]);

  // ── Hot-update link highlight (normal mode only) ──────────────────────────
  useEffect(() => {
    if (exploreMode) return; // explore mode owns opacity
    const cl  = crossLinksRef.current;
    const clb = crossLabelsRef.current;
    if (!cl) return;
    cl.attr('stroke-width', d=>highlightLink===d.type?2.6:1.6)
      .attr('opacity', d=>(highlightLink===null||highlightLink===d.type)?0.72:0.1);
    clb.attr('opacity', d=>(highlightLink===null||highlightLink===d.type)?0.8:0);
  }, [highlightLink, exploreMode]);

  return (
    <svg ref={svgRef}
      style={{ display:'block', background:'linear-gradient(135deg,#f0f2f5 0%,#e8edf2 100%)' }}
    />
  );
}
