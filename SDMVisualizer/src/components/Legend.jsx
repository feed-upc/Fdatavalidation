import React from 'react';
import { COLORS, LINK_COLORS, EXP_LINK_COLORS } from '../data/sdmData.js';

const NODE_TYPES = [
  { key: 'dataProduct',   label: 'Data Product / Asset Metadata', color: COLORS.dataProduct },
  { key: 'attribute',     label: 'Attribute',                      color: COLORS.attribute },
  { key: 'policy',        label: 'ODRL Policy',                    color: COLORS.policy },
  { key: 'cdm',           label: 'Common Data Model',              color: COLORS.cdm },
  { key: 'entity',        label: 'CDM Entity',                     color: COLORS.entity },
  { key: 'policyChecker', label: 'Policy Checker',                 color: COLORS.policyChecker },
];

const LINK_TYPES = [
  { type: 'hierarchy',     label: 'Structural hierarchy', color: LINK_COLORS.hierarchy, dash: 'none' },
  { type: 'hasPolicy',     label: 'hasPolicy',            color: LINK_COLORS.hasPolicy,     dash: '6 4' },
  { type: 'implementedBy', label: 'implementedBy',        color: LINK_COLORS.implementedBy, dash: '6 4' },
  { type: 'mapsTo',        label: 'mapsTo (CDM)',         color: LINK_COLORS.mapsTo,        dash: '6 4' },
];

function Swatch({ color }) {
  return (
    <span style={{
      display: 'inline-block', width: 14, height: 14, borderRadius: '50%',
      background: color, marginRight: 8, flexShrink: 0, border: '1.5px solid rgba(255,255,255,0.6)',
      verticalAlign: 'middle',
    }} />
  );
}

function DashLine({ color, dash }) {
  return (
    <svg width={32} height={10} style={{ marginRight: 8, flexShrink: 0, verticalAlign: 'middle' }}>
      <line x1={0} y1={5} x2={32} y2={5}
        stroke={color} strokeWidth={2}
        strokeDasharray={dash === 'none' ? undefined : dash} />
    </svg>
  );
}

const EXP_LINK_TYPES = [
  { type: 'checks',  label: 'checks (attr.)',    color: EXP_LINK_COLORS.checks,  dash: 'none' },
  { type: 'governs', label: 'governs (CDM/attr.)', color: EXP_LINK_COLORS.governs, dash: 'none' },
  { type: 'uses',    label: 'uses (condition)',  color: EXP_LINK_COLORS.uses,    dash: 'none' },
  { type: 'counts',  label: 'counts (rows)',     color: EXP_LINK_COLORS.counts,  dash: 'none' },
];

export default function Legend({ visibleTypes, onToggle, highlightLink, onHighlight, exploreMode }) {
  return (
    <div style={{
      position: 'fixed', bottom: 16, left: 16,
      background: 'rgba(255,255,255,0.97)',
      borderRadius: 12,
      boxShadow: '0 4px 20px rgba(44,62,80,0.13)',
      padding: '14px 18px',
      zIndex: 999,
      minWidth: 260,
    }}>
      <div style={{ fontSize: 11, fontWeight: 700, color: '#7f8c8d', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 10 }}>
        Node types
      </div>
      {NODE_TYPES.map(({ key, label, color }) => (
        <label key={key} style={{ display: 'flex', alignItems: 'center', marginBottom: 6, cursor: 'pointer', userSelect: 'none' }}>
          <input
            type="checkbox"
            checked={visibleTypes[key] ?? true}
            onChange={() => onToggle(key)}
            style={{ marginRight: 8 }}
          />
          <Swatch color={color} />
          <span style={{ fontSize: 12.5, color: '#2c3e50' }}>{label}</span>
        </label>
      ))}

      <div style={{ borderTop: '1px solid #ecf0f1', margin: '12px 0 10px' }} />

      <div style={{ fontSize: 11, fontWeight: 700, color: '#7f8c8d', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 10 }}>
        Relationships
      </div>
      {LINK_TYPES.map(({ type, label, color, dash }) => (
        <div key={type}
          onClick={() => onHighlight(highlightLink === type ? null : type)}
          style={{
            display: 'flex', alignItems: 'center', marginBottom: 6,
            cursor: 'pointer', opacity: highlightLink && highlightLink !== type ? 0.4 : 1,
            transition: 'opacity 0.2s',
          }}>
          <DashLine color={color} dash={dash} />
          <span style={{ fontSize: 12.5, color: '#2c3e50', fontFamily: type === 'hierarchy' ? undefined : 'Roboto Mono, monospace' }}>
            {label}
          </span>
        </div>
      ))}
      {/* Expansion links section — only shown in explore mode */}
      {exploreMode && (
        <>
          <div style={{ borderTop: '1px solid #ecf0f1', margin: '10px 0 8px' }} />
          <div style={{ fontSize: 11, fontWeight: 700, color: '#7f8c8d', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 8 }}>
            Expansion links
          </div>
          {EXP_LINK_TYPES.map(({ type, label, color }) => (
            <div key={type} style={{ display: 'flex', alignItems: 'center', marginBottom: 5 }}>
              <svg width={32} height={10} style={{ marginRight: 8, flexShrink: 0, verticalAlign: 'middle' }}>
                <line x1={0} y1={5} x2={32} y2={5} stroke={color} strokeWidth={2.2} />
              </svg>
              <span style={{ fontSize: 12, color: '#2c3e50' }}>{label}</span>
            </div>
          ))}
        </>
      )}

      <div style={{ fontSize: 10, color: '#aaa', marginTop: 8 }}>
        Click relation to highlight · click any node to expand its edges
      </div>
    </div>
  );
}
