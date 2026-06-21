import React, { useState, useRef } from 'react';
import SDMGraph from './components/SDMGraph.jsx';
import NodeDetail from './components/NodeDetail.jsx';
import Legend from './components/Legend.jsx';
import Controls from './components/Controls.jsx';
import Tooltip from './components/Tooltip.jsx';

const DEFAULT_VISIBLE = {
  dataProduct: true, attribute: true, policy: true,
  cdm: true, entity: true, policyChecker: true,
};

export default function App() {
  const svgRef = useRef(null);

  const [selectedNode,     setSelectedNode]     = useState(null);
  const [exploreMode,      setExploreMode]      = useState(null);
  // exploreMode: null | { seedNode, expanded: Set<string> }
  const [tooltip,          setTooltip]          = useState({ x: null, y: null, node: null });
  const [visibleTypes,     setVisibleTypes]     = useState(DEFAULT_VISIBLE);
  const [highlightLink,    setHighlightLink]    = useState(null);
  const [nodeScale,        setNodeScale]        = useState(1.0);
  const [chargeStrength,   setChargeStrength]   = useState(-350);
  const [linkDistMult,     setLinkDistMult]     = useState(1.0);
  const [showAllRelations, setShowAllRelations] = useState(false);

  function toggleType(key) {
    setVisibleTypes(prev => ({ ...prev, [key]: !prev[key] }));
    setExploreMode(null);
  }

  // Clicking a node: always show detail panel + expand it in explore mode
  function handleNodeClick(node) {
    setSelectedNode(node);
    if (['root', 'group'].includes(node.type)) return;
    setExploreMode(prev => ({
      seedNode: node,
      expanded: new Set([...(prev?.expanded ?? []), node.id]),
    }));
  }

  // Reset exploration to start fresh from a given node (used by NodeDetail)
  function handleResetExplore(node) {
    setExploreMode({ seedNode: node, expanded: new Set([node.id]) });
  }

  function handleHover(x, y, node) {
    setTooltip({ x, y, node });
  }

  const NODE_COLORS = {
    dataProduct: '#e74c3c', attribute: '#f1948a', policy: '#27ae60',
    cdm: '#e6a817', entity: '#f0c030', policyChecker: '#8e44ad',
  };
  const exploreColor = exploreMode
    ? (NODE_COLORS[exploreMode.seedNode.type] ?? NODE_COLORS[exploreMode.seedNode.category] ?? '#2c3e50')
    : null;

  return (
    <div style={{ position: 'relative', width: '100vw', height: '100vh', overflow: 'hidden' }}>

      {/* ── Title bar ─────────────────────────────────────────────────── */}
      <div style={{
        position: 'fixed', top: 0, left: 0, right: 0, height: 48,
        background: 'rgba(28,40,51,0.97)',
        display: 'flex', alignItems: 'center', padding: '0 20px',
        zIndex: 998, boxShadow: '0 2px 12px rgba(0,0,0,0.25)', gap: 12,
      }}>
        <div style={{ width: 8, height: 8, borderRadius: '50%', background: '#e74c3c' }} />
        <div style={{ width: 8, height: 8, borderRadius: '50%', background: '#27ae60' }} />
        <div style={{ width: 8, height: 8, borderRadius: '50%', background: '#e6a817' }} />
        <span style={{ color: '#fff', fontWeight: 700, fontSize: 14.5, letterSpacing: 0.3, marginLeft: 4 }}>
          HealthMesh — Semantic Data Model
        </span>
        <span style={{ color: 'rgba(255,255,255,0.38)', fontSize: 12, fontFamily: 'Roboto Mono, monospace' }}>
          EHDS AMR · DQR Governance
        </span>

        {/* Explore mode banner */}
        {exploreMode && (
          <div style={{
            marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: 10,
            background: exploreColor, borderRadius: 20,
            padding: '4px 14px 4px 10px',
          }}>
            <span style={{ fontSize: 11, color: '#fff', fontWeight: 600 }}>
              ⊹ Exploring from: {exploreMode.seedNode.label}
            </span>
            <span style={{ fontSize: 10, color: 'rgba(255,255,255,0.7)' }}>
              {exploreMode.expanded.size} opened · click any node to expand
            </span>
            <button
              onClick={() => setExploreMode(null)}
              style={{ background: 'rgba(255,255,255,0.25)', border: 'none', color: '#fff', borderRadius: '50%', width: 20, height: 20, fontSize: 13, cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center' }}
            >×</button>
          </div>
        )}

        {!exploreMode && (
          <span style={{ marginLeft: 'auto', color: 'rgba(255,255,255,0.32)', fontSize: 10.5 }}>
            Click any node to explore its edges · Drag · Scroll to zoom
          </span>
        )}
      </div>

      {/* ── Graph canvas ──────────────────────────────────────────────── */}
      <div style={{ paddingTop: 48, width: '100%', height: '100%' }}>
        <SDMGraph
          svgRef={svgRef}
          onNodeClick={handleNodeClick}
          onNodeHover={handleHover}
          visibleTypes={visibleTypes}
          highlightLink={highlightLink}
          nodeScale={nodeScale}
          chargeStrength={chargeStrength}
          linkDistMult={linkDistMult}
          exploreMode={exploreMode}
          showAllRelations={showAllRelations}
        />
      </div>

      {/* ── Panels ────────────────────────────────────────────────────── */}
      {selectedNode && (
        <NodeDetail
          node={selectedNode}
          onClose={() => setSelectedNode(null)}
          isExploreSeed={exploreMode?.seedNode.id === selectedNode.id}
          onResetExplore={handleResetExplore}
        />
      )}

      <Legend
        visibleTypes={visibleTypes}
        onToggle={toggleType}
        highlightLink={highlightLink}
        onHighlight={setHighlightLink}
        exploreMode={exploreMode}
      />

      <Controls
        nodeScale={nodeScale}        setNodeScale={setNodeScale}
        chargeStrength={chargeStrength} setChargeStrength={setChargeStrength}
        linkDistMult={linkDistMult}  setLinkDistMult={setLinkDistMult}
        svgRef={svgRef}
        showAllRelations={showAllRelations} setShowAllRelations={setShowAllRelations}
      />

      {tooltip.node && (
        <Tooltip x={tooltip.x} y={tooltip.y} node={tooltip.node} />
      )}
    </div>
  );
}
