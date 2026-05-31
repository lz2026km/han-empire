/* =============================================
   FactionRelationDiagram Component
   派系关系图 - 可视化派系势力和关系
   ============================================= */

import React, { useState, useEffect } from 'react';

interface FactionNode {
  id: string;
  name: string;
  influence: number;
  color: string;
  ministers: string[];
  description?: string;
}

interface FactionRelation {
  source: string;
  target: string;
  type: 'alliance' | 'rival' | 'neutral';
  strength: number;
}

interface FactionRelationDiagramProps {
  factions: FactionNode[];
  relations?: FactionRelation[];
  width?: number;
  height?: number;
}

export function FactionRelationDiagram({
  factions,
  relations = [],
  width = 600,
  height = 400,
}: FactionRelationDiagramProps) {
  const [hoveredFaction, setHoveredFaction] = useState<string | null>(null);
  const [selectedFaction, setSelectedFaction] = useState<string | null>(null);

  // Calculate node positions in a circle
  const getNodePosition = (index: number, total: number, radius: number) => {
    const angle = (2 * Math.PI * index) / total - Math.PI / 2;
    const x = radius * Math.cos(angle) + width / 2;
    const y = radius * Math.sin(angle) + height / 2;
    return { x, y };
  };

  const radius = Math.min(width, height) * 0.35;

  const getRelationPath = (source: FactionNode, target: FactionNode) => {
    const sourcePos = getNodePosition(
      factions.findIndex(f => f.id === source.id),
      factions.length,
      radius
    );
    const targetPos = getNodePosition(
      factions.findIndex(f => f.id === target.id),
      factions.length,
      radius
    );

    const midX = (sourcePos.x + targetPos.x) / 2;
    const midY = (sourcePos.y + targetPos.y) / 2;

    const dx = targetPos.x - sourcePos.x;
    const dy = targetPos.y - sourcePos.y;
    const dist = Math.sqrt(dx * dx + dy * dy);
    const curveOffset = dist * 0.2;

    const controlX = midX + curveOffset;
    const controlY = midY - curveOffset;

    return `M ${sourcePos.x} ${sourcePos.y} Q ${controlX} ${controlY} ${targetPos.x} ${targetPos.y}`;
  };

  const renderRelation = (relation: FactionRelation) => {
    const source = factions.find(f => f.id === relation.source);
    const target = factions.find(f => f.id === relation.target);
    if (!source || !target) return null;

    const isHighlighted = hoveredFaction === relation.source || hoveredFaction === relation.target;

    const strokeColor = relation.type === 'alliance'
      ? '#4a9c5d'
      : relation.type === 'rival'
        ? '#c42b2b'
        : '#6b5f4f';

    const strokeDash = relation.type === 'neutral' ? '5,5' : '';

    return (
      <g key={`${relation.source}-${relation.target}`}>
        <path
          d={getRelationPath(source, target)}
          fill="none"
          stroke={strokeColor}
          strokeWidth={isHighlighted ? 3 : 1.5}
          strokeDasharray={strokeDash}
          opacity={isHighlighted ? 1 : 0.4}
          style={{
            transition: 'all 0.2s ease',
            cursor: 'pointer',
          }}
          onMouseEnter={() => setHoveredFaction(relation.source)}
          onMouseLeave={() => setHoveredFaction(null)}
        />
        {/* Arrow or indicator at midpoint */}
        <circle
          cx={(getNodePosition(factions.findIndex(f => f.id === source.id), factions.length, radius).x +
               getNodePosition(factions.findIndex(f => f.id === target.id), factions.length, radius).x) / 2}
          cy={(getNodePosition(factions.findIndex(f => f.id === source.id), factions.length, radius).y +
               getNodePosition(factions.findIndex(f => f.id === target.id), factions.length, radius).y) / 2}
          r={4}
          fill={strokeColor}
          opacity={isHighlighted ? 0.8 : 0.3}
        />
      </g>
    );
  };

  return (
    <div className="faction-relation-diagram">
      <svg width={width} height={height} className="faction-diagram-svg">
        {/* Background pattern */}
        <defs>
          <pattern id="grid" width="20" height="20" patternUnits="userSpaceOnUse">
            <circle cx="1" cy="1" r="1" fill="rgba(201, 168, 76, 0.1)" />
          </pattern>
          <radialGradient id="centerGlow">
            <stop offset="0%" stopColor="rgba(201, 168, 76, 0.1)" />
            <stop offset="100%" stopColor="rgba(0, 0, 0, 0)" />
          </radialGradient>
        </defs>

        <rect width={width} height={height} fill="url(#grid)" />
        <circle cx={width / 2} cy={height / 2} r={radius * 0.5} fill="url(#centerGlow)" />

        {/* Render relations first (behind nodes) */}
        <g className="relations-layer">
          {relations.map(renderRelation)}
        </g>

        {/* Center circle (Emperor) */}
        <circle
          cx={width / 2}
          cy={height / 2}
          r={40}
          fill="var(--color-bg-tertiary)"
          stroke="var(--color-gold)"
          strokeWidth={2}
          className="emperor-center"
        />
        <text
          x={width / 2}
          y={height / 2 + 5}
          textAnchor="middle"
          fill="var(--color-gold)"
          fontSize={14}
          fontWeight="bold"
        >
          天子
        </text>

        {/* Render faction nodes */}
        <g className="nodes-layer">
          {factions.map((faction, index) => {
            const pos = getNodePosition(index, factions.length, radius);
            const isHovered = hoveredFaction === faction.id;
            const isSelected = selectedFaction === faction.id;
            const nodeRadius = 35 + faction.influence * 0.3;

            return (
              <g
                key={faction.id}
                transform={`translate(${pos.x}, ${pos.y})`}
                className="faction-node"
                onMouseEnter={() => setHoveredFaction(faction.id)}
                onMouseLeave={() => setHoveredFaction(null)}
                onClick={() => setSelectedFaction(selectedFaction === faction.id ? null : faction.id)}
                style={{ cursor: 'pointer' }}
              >
                {/* Glow effect */}
                <circle
                  r={nodeRadius + 10}
                  fill={faction.color}
                  opacity={isHovered || isSelected ? 0.3 : 0}
                  className="node-glow"
                />

                {/* Main circle */}
                <circle
                  r={nodeRadius}
                  fill="var(--color-bg-card)"
                  stroke={faction.color}
                  strokeWidth={isHovered || isSelected ? 3 : 2}
                  className="node-circle"
                />

                {/* Influence bar */}
                <circle
                  r={nodeRadius - 5}
                  fill="none"
                  stroke={faction.color}
                  strokeWidth={4}
                  strokeDasharray={`${(faction.influence / 100) * 2 * Math.PI * (nodeRadius - 5)} ${2 * Math.PI * (nodeRadius - 5)}`}
                  strokeDashoffset={0}
                  opacity={0.6}
                  transform={`rotate(-90)`}
                />

                {/* Faction name */}
                <text
                  y={-5}
                  textAnchor="middle"
                  fill="var(--color-gold)"
                  fontSize={11}
                  fontWeight="bold"
                  className="faction-name"
                >
                  {faction.name}
                </text>

                {/* Influence value */}
                <text
                  y={10}
                  textAnchor="middle"
                  fill="var(--color-text-secondary)"
                  fontSize={10}
                >
                  {faction.influence}
                </text>

                {/* Minister count */}
                <text
                  y={25}
                  textAnchor="middle"
                  fill="var(--color-text-muted)"
                  fontSize={9}
                >
                  {faction.ministers.length}人
                </text>
              </g>
            );
          })}
        </g>
      </svg>

      {/* Legend */}
      <div className="faction-legend">
        <div className="legend-item">
          <span className="legend-line alliance"></span>
          <span>同盟</span>
        </div>
        <div className="legend-item">
          <span className="legend-line rival"></span>
          <span>对立</span>
        </div>
        <div className="legend-item">
          <span className="legend-line neutral"></span>
          <span>中立</span>
        </div>
      </div>

      {/* Tooltip */}
      {hoveredFaction && (
        <div className="faction-tooltip">
          {factions.find(f => f.id === hoveredFaction)?.description}
        </div>
      )}
    </div>
  );
}

/* =============================================
   FactionRelationDiagram Styles
   ============================================= */

.faction-relation-diagram {
  position: relative;
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: var(--border-radius);
  padding: 16px;
}

.faction-diagram-svg {
  display: block;
  margin: 0 auto;
}

.faction-node {
  transition: transform 0.2s ease;
}

.faction-node:hover {
  transform: scale(1.1);
}

.node-circle {
  transition: all 0.2s ease;
}

.node-glow {
  transition: opacity 0.2s ease;
}

.emperor-center {
  animation: emperorCenterPulse 3s ease-in-out infinite;
}

@keyframes emperorCenterPulse {
  0%, 100% {
    filter: drop-shadow(0 0 5px rgba(201, 168, 76, 0.3));
  }
  50% {
    filter: drop-shadow(0 0 15px rgba(201, 168, 76, 0.5));
  }
}

.faction-legend {
  display: flex;
  justify-content: center;
  gap: 24px;
  margin-top: 16px;
  padding-top: 12px;
  border-top: 1px solid var(--color-border);
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: var(--color-text-secondary);
}

.legend-line {
  width: 24px;
  height: 3px;
  border-radius: 2px;
}

.legend-line.alliance {
  background: #4a9c5d;
}

.legend-line.rival {
  background: #c42b2b;
}

.legend-line.neutral {
  background: #6b5f4f;
  background-image: repeating-linear-gradient(
    90deg,
    #6b5f4f 0,
    #6b5f4f 5px,
    transparent 5px,
    transparent 10px
  );
}

.faction-tooltip {
  position: absolute;
  bottom: 8px;
  left: 50%;
  transform: translateX(-50%);
  padding: 8px 12px;
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-gold-dim);
  border-radius: var(--border-radius);
  font-size: 12px;
  color: var(--color-text-secondary);
  max-width: 300px;
  text-align: center;
}