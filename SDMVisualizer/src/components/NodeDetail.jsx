import React from 'react';
import { COLORS, SDM_NODES } from '../data/sdmData.js';

const TYPE_LABELS = {
  root:          'SDM Root',
  group:         'Category Group',
  dataProduct:   'Data Product',
  attribute:     'Attribute',
  policy:        'ODRL Policy Rule',
  cdm:           'Common Data Model',
  entity:        'CDM Entity',
  policyChecker: 'Policy Checker (GX)',
};

const DIMENSION_COLORS = {
  Completeness: '#27ae60',
  Compliance:   '#2980b9',
  Consistency:  '#e67e22',
  Fairness:     '#9b59b6',
  Currentness:  '#16a085',
  Timeliness:   '#1abc9c',
  Accuracy:     '#c0392b',
};

const PATTERN_DESC = {
  DQRP1: 'Data Age Threshold',
  DQRP2: 'Completeness (Not Null)',
  DQRP3: 'Value Standard Compliance',
  DQRP4: 'Conditional Consistency',
  DQRP5: 'Sufficient Sample Size',
  DQRP6: 'Distribution Fairness',
};

function Section({ title, children }) {
  return (
    <div style={{ marginBottom: 14 }}>
      <div style={{ fontSize: 10, fontWeight: 700, color: '#95a5a6', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 6 }}>
        {title}
      </div>
      {children}
    </div>
  );
}

function KV({ label, value }) {
  if (value === undefined || value === null || value === '') return null;
  return (
    <div style={{ display: 'flex', gap: 8, marginBottom: 5, fontSize: 12.5 }}>
      <span style={{ color: '#7f8c8d', minWidth: 105, flexShrink: 0 }}>{label}</span>
      <span style={{ color: '#2c3e50', fontFamily: 'Roboto Mono, monospace', wordBreak: 'break-all' }}>
        {String(value)}
      </span>
    </div>
  );
}

function Badge({ text, color, style = {} }) {
  return (
    <span style={{
      display: 'inline-block',
      background: color, color: '#fff',
      borderRadius: 20, padding: '3px 11px',
      fontSize: 11, fontWeight: 600, marginRight: 6, marginBottom: 4,
      ...style,
    }}>
      {text}
    </span>
  );
}

function CodeBlock({ children }) {
  return (
    <div style={{
      background: '#1e2733', color: '#a8d8ea',
      borderRadius: 7, padding: '10px 12px',
      fontFamily: 'Roboto Mono, monospace', fontSize: 11.5,
      lineHeight: 1.6, overflowX: 'auto', whiteSpace: 'pre-wrap',
      wordBreak: 'break-all',
    }}>
      {children}
    </div>
  );
}

// ── Type-specific body sections ────────────────────────────────────────────────

function PolicyBody({ node }) {
  const d = node.detail ?? {};
  return (
    <>
      {d.statement && (
        <Section title="Policy statement">
          <p style={{ fontSize: 13, color: '#34495e', lineHeight: 1.6, fontStyle: 'italic', margin: 0 }}>
            "{d.statement}"
          </p>
        </Section>
      )}
      <Section title="Classification">
        <div style={{ marginBottom: 6 }}>
          {d.dimension && <Badge text={d.dimension} color={DIMENSION_COLORS[d.dimension] ?? '#7f8c8d'} />}
          {d.pattern && (
            <Badge
              text={`${d.pattern} · ${PATTERN_DESC[d.pattern] ?? ''}`}
              color="#546e7a"
            />
          )}
        </div>
      </Section>
      <Section title="Provenance">
        <KV label="DQR ID"    value={d.derivedFrom} />
        <KV label="Source"    value={d.source} />
      </Section>
    </>
  );
}

function PolicyCheckerBody({ node }) {
  const d = node.detail ?? {};
  const expectFull = d.expectation ?? '';
  return (
    <>
      <Section title="Great Expectations check">
        <CodeBlock>{expectFull}</CodeBlock>
      </Section>
      <Section title="Parameters">
        <KV label="Column"      value={d.column} />
        <KV label="Value set"   value={d.valueSet} />
        <KV label="Condition"   value={d.condition} />
        <KV label="Min value"   value={d.minValue ?? d.min} />
        <KV label="Max value"   value={d.maxValue ?? d.max} />
        <KV label="Threshold"   value={d.threshold} />
        <KV label="Distribution" value={d.distribution} />
        <KV label="Mostly"      value={d.mostly} />
      </Section>
      <Section title="Traceability">
        <KV label="DQR"         value={d.dqr} />
        <KV label="Data product" value={d.dataProduct} />
        <KV label="Service ID"  value={d.serviceId} />
      </Section>
    </>
  );
}

function DataProductBody({ node }) {
  const d = node.detail ?? {};
  const attrs = SDM_NODES.filter(n => n.type === 'attribute' && n.parentDP === node.id);
  return (
    <>
      {d.description && (
        <p style={{ fontSize: 12.5, color: '#555', lineHeight: 1.55, marginBottom: 12, fontStyle: 'italic' }}>
          {d.description}
        </p>
      )}
      <Section title="Metadata">
        <KV label="Format"     value={d.format} />
        <KV label="Owner"      value={d.owner} />
        <KV label="Identifier" value={d.identifier} />
        <KV label="Path"       value={d.path} />
      </Section>
      {attrs.length > 0 && (
        <Section title={`Attributes (${attrs.length})`}>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 5 }}>
            {attrs.map(a => (
              <span key={a.id} style={{
                background: '#fde8e8', color: '#c0392b',
                borderRadius: 4, padding: '2px 8px', fontSize: 11,
                fontFamily: 'Roboto Mono, monospace',
              }}>
                {a.label}
              </span>
            ))}
          </div>
        </Section>
      )}
    </>
  );
}

function CDMBody({ node }) {
  const d = node.detail ?? {};
  const entities = SDM_NODES.filter(n => n.type === 'entity' && n.parentE === node.id);
  return (
    <>
      {d.description && (
        <p style={{ fontSize: 12.5, color: '#555', lineHeight: 1.55, marginBottom: 12, fontStyle: 'italic' }}>
          {d.description}
        </p>
      )}
      <Section title="Metadata">
        <KV label="Owner"      value={d.owner} />
        <KV label="Identifier" value={d.identifier} />
      </Section>
      {entities.length > 0 && (
        <Section title="Top-level entities">
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 5 }}>
            {entities.map(e => (
              <span key={e.id} style={{
                background: '#fef9e7', color: '#b7950b',
                border: '1px solid #f9e79f',
                borderRadius: 4, padding: '2px 8px', fontSize: 11,
              }}>
                {e.label}
              </span>
            ))}
          </div>
        </Section>
      )}
    </>
  );
}

function EntityBody({ node }) {
  const children = SDM_NODES.filter(n => n.type === 'entity' && n.parentE === node.id);
  const parent   = SDM_NODES.find(n => n.id === node.parentE);
  return (
    <>
      <Section title="Hierarchy">
        <KV label="Parent" value={parent?.label} />
      </Section>
      {children.length > 0 && (
        <Section title="Child entities">
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 5 }}>
            {children.map(c => (
              <span key={c.id} style={{
                background: '#fef9e7', color: '#b7950b',
                borderRadius: 4, padding: '2px 8px', fontSize: 11,
              }}>
                {c.label}
              </span>
            ))}
          </div>
        </Section>
      )}
    </>
  );
}

// ── Main export ────────────────────────────────────────────────────────────────
export default function NodeDetail({ node, onClose, isExploreSeed, onResetExplore }) {
  if (!node) return null;

  const color = node.type === 'group'
    ? (COLORS[node.category] ?? '#546e7a')
    : (COLORS[node.type] ?? '#546e7a');

  const typeLabel   = TYPE_LABELS[node.type] ?? node.type;
  const explorable  = !['root','group'].includes(node.type);

  return (
    <div style={{
      position: 'fixed', top: 64, right: 16,
      width: 330, maxHeight: 'calc(100vh - 80px)',
      background: '#fff',
      borderRadius: 14,
      boxShadow: '0 8px 40px rgba(44,62,80,0.18)',
      overflow: 'auto',
      zIndex: 1000,
    }}>
      {/* Header */}
      <div style={{
        background: color, borderRadius: '14px 14px 0 0',
        padding: '14px 16px 12px',
        display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between',
        position: 'sticky', top: 0, zIndex: 1,
      }}>
        <div>
          <div style={{ fontSize: 9.5, color: 'rgba(255,255,255,0.7)', textTransform: 'uppercase', letterSpacing: 1.2, marginBottom: 4 }}>
            {typeLabel}
          </div>
          <div style={{ fontSize: 15.5, fontWeight: 700, color: '#fff', lineHeight: 1.3 }}>
            {node.label}
          </div>
          {explorable && isExploreSeed && (
            <button
              onClick={() => onResetExplore(node)}
              style={{
                marginTop: 8,
                background: 'rgba(255,255,255,0.22)',
                border: '1.5px solid rgba(255,255,255,0.6)',
                color: '#fff', borderRadius: 20,
                padding: '3px 12px', fontSize: 11, fontWeight: 600,
                cursor: 'pointer', display: 'inline-flex', alignItems: 'center', gap: 5,
              }}
            >
              ↺ Reset exploration here
            </button>
          )}
        </div>
        <button
          onClick={onClose}
          style={{ background: 'rgba(255,255,255,0.2)', border: 'none', color: '#fff', fontSize: 18, cursor: 'pointer', borderRadius: '50%', width: 28, height: 28, display: 'flex', alignItems: 'center', justifyContent: 'center', marginLeft: 8, flexShrink: 0 }}
        >×</button>
      </div>

      {/* Body */}
      <div style={{ padding: '16px 18px' }}>
        {node.type === 'policy'        && <PolicyBody        node={node} />}
        {node.type === 'policyChecker' && <PolicyCheckerBody node={node} />}
        {node.type === 'dataProduct'   && <DataProductBody   node={node} />}
        {node.type === 'cdm'           && <CDMBody           node={node} />}
        {node.type === 'entity'        && <EntityBody        node={node} />}
        {node.type === 'attribute'     && (
          <Section title="Column">
            <KV label="Name"       value={node.label} />
            <KV label="DataProduct" value={node.parentDP} />
          </Section>
        )}
        {['root', 'group'].includes(node.type) && (
          <p style={{ fontSize: 12.5, color: '#555', lineHeight: 1.55 }}>
            {node.detail?.description ?? node.detail?.title ?? ''}
          </p>
        )}
      </div>
    </div>
  );
}
