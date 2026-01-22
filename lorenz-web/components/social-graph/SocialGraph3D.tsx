'use client';

import { useRef, useState, useMemo, useCallback, Suspense } from 'react';
import { Canvas, useFrame, useThree } from '@react-three/fiber';
import { OrbitControls, Text, Html, Line, Sphere, Stars } from '@react-three/drei';
import * as THREE from 'three';

// Types
interface GraphNode {
  id: string;
  name: string;
  email?: string;
  company?: string;
  role?: string;
  relationship_type: string;
  total_interactions: number;
  x: number;
  y: number;
  z: number;
  size: number;
  color: string;
  avatar?: string;
  linkedin?: string;
  twitter?: string;
}

interface GraphEdge {
  source: string;
  target: string;
  type?: string;
  weight?: number;
}

interface GraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
  stats: {
    total_contacts: number;
    total_interactions: number;
    by_relationship: Record<string, number>;
  };
}

interface SocialGraph3DProps {
  data: GraphData;
  onNodeClick?: (node: GraphNode) => void;
  onNodeHover?: (node: GraphNode | null) => void;
  showLabels?: boolean;
  showEdges?: boolean;
  highlightRelationship?: string | null;
}

// Individual Node Component
function ContactNode({
  node,
  onClick,
  onHover,
  showLabel,
  isHighlighted,
  isSelected,
}: {
  node: GraphNode;
  onClick: (node: GraphNode) => void;
  onHover: (node: GraphNode | null) => void;
  showLabel: boolean;
  isHighlighted: boolean;
  isSelected: boolean;
}) {
  const meshRef = useRef<THREE.Mesh>(null);
  const [hovered, setHovered] = useState(false);

  // Pulse animation for selected/hovered nodes
  useFrame((state) => {
    if (meshRef.current) {
      if (hovered || isSelected) {
        meshRef.current.scale.setScalar(
          node.size * (1.2 + Math.sin(state.clock.elapsedTime * 3) * 0.1)
        );
      } else {
        meshRef.current.scale.setScalar(node.size);
      }
    }
  });

  const handlePointerOver = useCallback(() => {
    setHovered(true);
    onHover(node);
    document.body.style.cursor = 'pointer';
  }, [node, onHover]);

  const handlePointerOut = useCallback(() => {
    setHovered(false);
    onHover(null);
    document.body.style.cursor = 'auto';
  }, [onHover]);

  const opacity = isHighlighted || hovered || isSelected ? 1 : 0.6;

  return (
    <group position={[node.x, node.y, node.z]}>
      {/* Main sphere */}
      <mesh
        ref={meshRef}
        onClick={() => onClick(node)}
        onPointerOver={handlePointerOver}
        onPointerOut={handlePointerOut}
      >
        <sphereGeometry args={[1, 32, 32]} />
        <meshStandardMaterial
          color={node.color}
          transparent
          opacity={opacity}
          emissive={node.color}
          emissiveIntensity={hovered || isSelected ? 0.5 : 0.2}
          roughness={0.4}
          metalness={0.3}
        />
      </mesh>

      {/* Glow effect */}
      <mesh scale={node.size * 1.5}>
        <sphereGeometry args={[1, 16, 16]} />
        <meshBasicMaterial
          color={node.color}
          transparent
          opacity={0.15}
          side={THREE.BackSide}
        />
      </mesh>

      {/* Label */}
      {(showLabel || hovered || isSelected) && (
        <Text
          position={[0, node.size + 0.8, 0]}
          fontSize={0.4}
          color="white"
          anchorX="center"
          anchorY="bottom"
          outlineWidth={0.05}
          outlineColor="#000000"
        >
          {node.name}
        </Text>
      )}

      {/* Tooltip on hover */}
      {hovered && (
        <Html position={[node.size + 1, 0, 0]} distanceFactor={15}>
          <div className="bg-gray-900/95 backdrop-blur-sm px-4 py-3 rounded-lg shadow-xl border border-gray-700 min-w-[200px]">
            <div className="font-semibold text-white">{node.name}</div>
            {node.company && (
              <div className="text-gray-400 text-sm">{node.company}</div>
            )}
            {node.role && (
              <div className="text-gray-400 text-sm">{node.role}</div>
            )}
            <div className="text-xs text-gray-500 mt-2">
              <span className="inline-flex items-center gap-1">
                <span
                  className="w-2 h-2 rounded-full"
                  style={{ backgroundColor: node.color }}
                />
                {node.relationship_type.replace('_', ' ')}
              </span>
            </div>
            <div className="text-xs text-gray-500 mt-1">
              {node.total_interactions} interactions
            </div>
          </div>
        </Html>
      )}
    </group>
  );
}

// Edge Component
function GraphEdge({
  start,
  end,
  color = '#ffffff',
  opacity = 0.2,
}: {
  start: [number, number, number];
  end: [number, number, number];
  color?: string;
  opacity?: number;
}) {
  return (
    <Line
      points={[start, end]}
      color={color}
      lineWidth={1}
      transparent
      opacity={opacity}
    />
  );
}

// Center User Node
function CenterNode() {
  const meshRef = useRef<THREE.Mesh>(null);

  useFrame((state) => {
    if (meshRef.current) {
      meshRef.current.rotation.y = state.clock.elapsedTime * 0.2;
      meshRef.current.rotation.x = Math.sin(state.clock.elapsedTime * 0.3) * 0.1;
    }
  });

  return (
    <group position={[0, 0, 0]}>
      {/* Core */}
      <mesh ref={meshRef}>
        <icosahedronGeometry args={[1.5, 1]} />
        <meshStandardMaterial
          color="#6366f1"
          emissive="#6366f1"
          emissiveIntensity={0.8}
          wireframe
        />
      </mesh>

      {/* Outer glow */}
      <mesh>
        <sphereGeometry args={[2, 32, 32]} />
        <meshBasicMaterial
          color="#6366f1"
          transparent
          opacity={0.15}
          side={THREE.BackSide}
        />
      </mesh>

      {/* Inner sphere */}
      <mesh>
        <sphereGeometry args={[1, 32, 32]} />
        <meshStandardMaterial
          color="#8b5cf6"
          emissive="#8b5cf6"
          emissiveIntensity={0.5}
          roughness={0.2}
          metalness={0.8}
        />
      </mesh>

      <Text
        position={[0, 3, 0]}
        fontSize={0.6}
        color="#8b5cf6"
        anchorX="center"
        anchorY="bottom"
        outlineWidth={0.05}
        outlineColor="#000000"
      >
        YOU
      </Text>
    </group>
  );
}

// Camera animation on load
function CameraAnimation() {
  const { camera } = useThree();

  useFrame((state) => {
    // Gentle floating motion
    camera.position.y += Math.sin(state.clock.elapsedTime * 0.3) * 0.002;
  });

  return null;
}

// Main Graph Scene
function GraphScene({
  data,
  onNodeClick,
  onNodeHover,
  showLabels,
  showEdges,
  highlightRelationship,
  selectedNode,
}: SocialGraph3DProps & { selectedNode: GraphNode | null }) {
  // Create node position map for edges
  const nodePositions = useMemo(() => {
    const map = new Map<string, [number, number, number]>();
    data.nodes.forEach((node) => {
      map.set(node.id, [node.x, node.y, node.z]);
    });
    return map;
  }, [data.nodes]);

  // Filter nodes based on highlight
  const filteredNodes = useMemo(() => {
    if (!highlightRelationship) return data.nodes;
    return data.nodes.filter(
      (n) => n.relationship_type === highlightRelationship
    );
  }, [data.nodes, highlightRelationship]);

  return (
    <>
      {/* Lighting */}
      <ambientLight intensity={0.3} />
      <pointLight position={[10, 10, 10]} intensity={1} />
      <pointLight position={[-10, -10, -10]} intensity={0.5} color="#8b5cf6" />
      <pointLight position={[0, 20, 0]} intensity={0.3} color="#06b6d4" />

      {/* Background stars */}
      <Stars
        radius={100}
        depth={50}
        count={2000}
        factor={4}
        saturation={0}
        fade
        speed={1}
      />

      {/* Center user node */}
      <CenterNode />

      {/* Edges */}
      {showEdges &&
        data.edges.map((edge, i) => {
          const start = nodePositions.get(edge.source);
          const end = nodePositions.get(edge.target);
          if (!start || !end) return null;

          return (
            <GraphEdge
              key={`edge-${i}`}
              start={start}
              end={end}
              opacity={0.15}
            />
          );
        })}

      {/* Edges from center to nodes */}
      {data.nodes.map((node, i) => (
        <GraphEdge
          key={`center-edge-${i}`}
          start={[0, 0, 0]}
          end={[node.x, node.y, node.z]}
          color={node.color}
          opacity={
            highlightRelationship && node.relationship_type !== highlightRelationship
              ? 0.05
              : 0.1
          }
        />
      ))}

      {/* Contact Nodes */}
      {data.nodes.map((node) => (
        <ContactNode
          key={node.id}
          node={node}
          onClick={onNodeClick || (() => {})}
          onHover={onNodeHover || (() => {})}
          showLabel={showLabels || false}
          isHighlighted={
            !highlightRelationship ||
            node.relationship_type === highlightRelationship
          }
          isSelected={selectedNode?.id === node.id}
        />
      ))}

      {/* Camera controls */}
      <OrbitControls
        makeDefault
        minDistance={5}
        maxDistance={100}
        enablePan
        enableZoom
        enableRotate
        autoRotate
        autoRotateSpeed={0.3}
        zoomSpeed={0.5}
      />

      <CameraAnimation />
    </>
  );
}

// Loading fallback
function LoadingFallback() {
  return (
    <div className="absolute inset-0 flex items-center justify-center bg-gray-900">
      <div className="text-center">
        <div className="w-16 h-16 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin mx-auto" />
        <p className="mt-4 text-gray-400">Loading Social Graph...</p>
      </div>
    </div>
  );
}

// Main Component
export default function SocialGraph3D({
  data,
  onNodeClick,
  onNodeHover,
  showLabels = false,
  showEdges = true,
  highlightRelationship = null,
}: SocialGraph3DProps) {
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);

  const handleNodeClick = useCallback(
    (node: GraphNode) => {
      setSelectedNode(node);
      onNodeClick?.(node);
    },
    [onNodeClick]
  );

  return (
    <div className="w-full h-full relative">
      <Canvas
        camera={{ position: [30, 20, 30], fov: 60 }}
        gl={{ antialias: true, alpha: true }}
        style={{ background: 'linear-gradient(to bottom, #0f172a, #1e1b4b)' }}
      >
        <Suspense fallback={null}>
          <GraphScene
            data={data}
            onNodeClick={handleNodeClick}
            onNodeHover={onNodeHover}
            showLabels={showLabels}
            showEdges={showEdges}
            highlightRelationship={highlightRelationship}
            selectedNode={selectedNode}
          />
        </Suspense>
      </Canvas>
    </div>
  );
}
