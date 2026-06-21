import React from 'react';
import { COLORS } from '../data/sdmData.js';

const TYPE_SHORT = {
  root:          'SDM Root',
  group:         'Group',
  dataProduct:   'Data Product',
  attribute:     'Attribute',
  policy:        'ODRL Policy',
  cdm:           'CDM',
  entity:        'Entity',
  policyChecker: 'Policy Checker',
};

const DIMENSION_COLORS = {
  Completeness: '#27ae60', Compliance: '#2980b9', Consistency: '#e67e22',
  Fairness: '#9b59b6', Currentness: '#16a085', Timeliness: '#1abc9c',
};

function quickFact(node) {
  const d = node.detail ?? {};
  if (node.type === 'policy')        return d.dimension ? `Dimension: ${d.dimension}` : null;
  if (node.type === 'policyChecker') return d.dqr ? `DQR: ${d.dqr}` : null;
  if (node.type === 'dataProduct')   return d.format ?? null;
  if (node.type === 'cdm')           return `Owner: ${d.owner ?? '—'}`;
  if (node.type === 'attribute')     return `Column of ${node.parentDP ?? '?'}`;
  if (node.type === 'entity')        return `Entity in CDM`;
  return null;
}

export default function Tooltip({ x, y, node }) {
  if (!node) return null;

  const color = node.type === 'group'
    ? (COLORS[node.category] ?? '#546e7a')
    : (COLORS[node.type] ?? '#546e7a');

  const fact  = quickFact(node);
  const dim   = node.detail?.dimension;
  const dimColor = dim ? (DIMENSION_COLORS[dim] ?? '#555') : null;

  // Keep tooltip inside viewport
  const tx = Math.min(x + 14, window.innerWidth  - 230);
  const ty = Math.max(y - 55, 58);

  return (
    <div style={{
      position: 'fixed', left: tx, top: ty,
      background: '#fff',
      borderRadius: 9,
      boxShadow: '0 4px 20px rgba(44,62,80,0.22)',
      padding: '9px 13px',
      zIndex: 2000,
      maxWidth: 220,
      pointerEvents: 'none',
      borderLeft: `4px solid ${color}`,
    }}>
      <div style={{ fontSize: 9, color: color, textTransform: 'uppercase', letterSpacing: 1, fontWeight: 700, marginBottom: 3 }}>
        {TYPE_SHORT[node.type] ?? node.type}
      </div>
      <div style={{ fontSize: 13, fontWeight: 600, color: '#2c3e50', marginBottom: dim || fact ? 5 : 0 }}>
        {node.label}
      </div>
      {dim && (
        <span style={{ display: 'inline-block', background: dimColor, color: '#fff', borderRadius: 10, padding: '1px 8px', fontSize: 10, marginBottom: fact ? 3 : 0 }}>
          {dim}
        </span>
      )}
      {fact && !dim && (
        <div style={{ fontSize: 11, color: '#7f8c8d', fontFamily: 'Roboto Mono, monospace' }}>
          {fact}
        </div>
      )}
    </div>
  );
}
