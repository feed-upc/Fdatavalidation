import React, { useState } from 'react';

function Slider({ label, value, min, max, step, unit, onChange, format }) {
  const pct = ((value - min) / (max - min)) * 100;
  return (
    <div style={{ marginBottom: 12 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
        <span style={{ fontSize: 11.5, color: '#555' }}>{label}</span>
        <span style={{ fontSize: 11, fontFamily: 'Roboto Mono, monospace', color: '#2c3e50', fontWeight: 600 }}>
          {format ? format(value) : `${value}${unit ?? ''}`}
        </span>
      </div>
      <div style={{ position: 'relative', height: 4, background: '#ecf0f1', borderRadius: 2 }}>
        <div style={{ position: 'absolute', left: 0, top: 0, height: '100%', width: `${pct}%`, background: '#3498db', borderRadius: 2 }} />
      </div>
      <input
        type="range" min={min} max={max} step={step} value={value}
        onChange={e => onChange(Number(e.target.value))}
        style={{ width: '100%', margin: '4px 0 0', cursor: 'pointer', accentColor: '#3498db' }}
      />
    </div>
  );
}

export default function Controls({ nodeScale, setNodeScale, chargeStrength, setChargeStrength, linkDistMult, setLinkDistMult, svgRef, showAllRelations, setShowAllRelations }) {
  const [collapsed, setCollapsed] = useState(false);

  function exportSVG() {
    const svgEl = svgRef.current;
    if (!svgEl) return;
    // Inline a minimal style so exported SVG is self-contained
    const clone = svgEl.cloneNode(true);
    clone.setAttribute('xmlns', 'http://www.w3.org/2000/svg');
    const style = document.createElementNS('http://www.w3.org/2000/svg', 'style');
    style.textContent = `text { font-family: sans-serif; } .node { cursor: default; }`;
    clone.insertBefore(style, clone.firstChild);
    const serializer = new XMLSerializer();
    const svgStr = serializer.serializeToString(clone);
    const blob = new Blob([svgStr], { type: 'image/svg+xml' });
    const url  = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url; a.download = 'sdm-graph.svg'; a.click();
    URL.revokeObjectURL(url);
  }

  function exportPNG() {
    const svgEl = svgRef.current;
    if (!svgEl) return;
    const w = svgEl.clientWidth, h = svgEl.clientHeight;
    const serializer = new XMLSerializer();
    const svgStr = serializer.serializeToString(svgEl);
    const blob = new Blob([svgStr], { type: 'image/svg+xml;charset=utf-8' });
    const url  = URL.createObjectURL(blob);
    const img  = new Image();
    img.onload = () => {
      const canvas = document.createElement('canvas');
      canvas.width  = w * 2;
      canvas.height = h * 2;
      const ctx = canvas.getContext('2d');
      ctx.fillStyle = '#f0f2f5';
      ctx.fillRect(0, 0, canvas.width, canvas.height);
      ctx.scale(2, 2);
      ctx.drawImage(img, 0, 0, w, h);
      URL.revokeObjectURL(url);
      canvas.toBlob(pngBlob => {
        const a = document.createElement('a');
        a.href = URL.createObjectURL(pngBlob);
        a.download = 'sdm-graph.png'; a.click();
      }, 'image/png');
    };
    img.src = url;
  }

  const btnStyle = {
    flex: 1, padding: '7px 0', borderRadius: 7, border: 'none', cursor: 'pointer',
    fontSize: 12, fontWeight: 600, transition: 'opacity 0.15s',
  };

  return (
    <div style={{
      position: 'fixed', bottom: 16, right: 16,
      background: 'rgba(255,255,255,0.97)',
      borderRadius: 12,
      boxShadow: '0 4px 20px rgba(44,62,80,0.14)',
      padding: collapsed ? '10px 14px' : '14px 18px',
      zIndex: 999,
      width: 250,
    }}>
      {/* Header */}
      <div
        style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', cursor: 'pointer', marginBottom: collapsed ? 0 : 12 }}
        onClick={() => setCollapsed(c => !c)}
      >
        <span style={{ fontSize: 11, fontWeight: 700, color: '#7f8c8d', textTransform: 'uppercase', letterSpacing: 1 }}>
          Controls
        </span>
        <span style={{ color: '#bdc3c7', fontSize: 14 }}>{collapsed ? '▲' : '▼'}</span>
      </div>

      {!collapsed && (
        <>
          <Slider
            label="Node size"
            value={nodeScale} min={0.5} max={2.0} step={0.05}
            format={v => `${v.toFixed(2)}×`}
            onChange={setNodeScale}
          />
          <Slider
            label="Charge (repulsion)"
            value={chargeStrength} min={-1000} max={-80} step={20}
            format={v => String(v)}
            onChange={setChargeStrength}
          />
          <Slider
            label="Link distance"
            value={linkDistMult} min={0.4} max={2.2} step={0.05}
            format={v => `${Math.round(v * 100)}%`}
            onChange={setLinkDistMult}
          />

          <button
            onClick={() => setShowAllRelations(v => !v)}
            style={{
              width: '100%', padding: '7px 0', borderRadius: 7, border: 'none',
              cursor: 'pointer', fontSize: 12, fontWeight: 600,
              marginBottom: 8, transition: 'background 0.2s',
              background: showAllRelations ? '#8e44ad' : '#ecf0f1',
              color: showAllRelations ? '#fff' : '#555',
            }}
          >
            {showAllRelations ? '◉ All relations ON' : '◎ Show all relations'}
          </button>

          <div style={{ display: 'flex', gap: 8, marginTop: 0 }}>
            <button onClick={exportSVG} style={{ ...btnStyle, background: '#2c3e50', color: '#fff' }}>
              ↓ SVG
            </button>
            <button onClick={exportPNG} style={{ ...btnStyle, background: '#3498db', color: '#fff' }}>
              ↓ PNG
            </button>
          </div>
        </>
      )}
    </div>
  );
}
