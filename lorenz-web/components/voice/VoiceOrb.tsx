'use client';

import { useRef, useMemo, useEffect, useState } from 'react';
import { Canvas, useFrame, extend } from '@react-three/fiber';
import { shaderMaterial, Effects } from '@react-three/drei';
import * as THREE from 'three';

// Types for orb states
export type OrbState = 'idle' | 'listening' | 'speaking' | 'thinking';

interface OrbProps {
  state?: OrbState;
  inputVolume?: number;
  outputVolume?: number;
  colors?: {
    primary: string;
    secondary: string;
    glow: string;
  };
  size?: number;
}

// Default pastel colors
const defaultColors = {
  primary: '#C4B5FD',
  secondary: '#93C5FD',
  glow: '#A5B4FC'
};

// Ethereal Blob Material - soft and dreamy
const EtherealBlobMaterial = shaderMaterial(
  {
    uTime: 0,
    uSpeed: 0.2,
    uNoiseScale: 1.2,
    uNoiseStrength: 0.3,
    uIntensity: 1.0,
    uColorA: new THREE.Color('#C4B5FD'),
    uColorB: new THREE.Color('#93C5FD'),
    uColorC: new THREE.Color('#6EE7B7'),
  },
  // Vertex Shader - smooth organic movement
  `
    varying vec2 vUv;
    varying vec3 vNormal;
    varying vec3 vPosition;
    varying float vDisplacement;

    uniform float uTime;
    uniform float uSpeed;
    uniform float uNoiseScale;
    uniform float uNoiseStrength;

    // Simplex 3D noise
    vec4 permute(vec4 x) { return mod(((x*34.0)+1.0)*x, 289.0); }
    vec4 taylorInvSqrt(vec4 r) { return 1.79284291400159 - 0.85373472095314 * r; }

    float snoise(vec3 v) {
      const vec2 C = vec2(1.0/6.0, 1.0/3.0);
      const vec4 D = vec4(0.0, 0.5, 1.0, 2.0);

      vec3 i  = floor(v + dot(v, C.yyy));
      vec3 x0 = v - i + dot(i, C.xxx);

      vec3 g = step(x0.yzx, x0.xyz);
      vec3 l = 1.0 - g;
      vec3 i1 = min(g.xyz, l.zxy);
      vec3 i2 = max(g.xyz, l.zxy);

      vec3 x1 = x0 - i1 + C.xxx;
      vec3 x2 = x0 - i2 + C.yyy;
      vec3 x3 = x0 - D.yyy;

      i = mod(i, 289.0);
      vec4 p = permute(permute(permute(
                i.z + vec4(0.0, i1.z, i2.z, 1.0))
              + i.y + vec4(0.0, i1.y, i2.y, 1.0))
              + i.x + vec4(0.0, i1.x, i2.x, 1.0));

      float n_ = 1.0/7.0;
      vec3  ns = n_ * D.wyz - D.xzx;

      vec4 j = p - 49.0 * floor(p * ns.z * ns.z);

      vec4 x_ = floor(j * ns.z);
      vec4 y_ = floor(j - 7.0 * x_);

      vec4 x = x_ *ns.x + ns.yyyy;
      vec4 y = y_ *ns.x + ns.yyyy;
      vec4 h = 1.0 - abs(x) - abs(y);

      vec4 b0 = vec4(x.xy, y.xy);
      vec4 b1 = vec4(x.zw, y.zw);

      vec4 s0 = floor(b0)*2.0 + 1.0;
      vec4 s1 = floor(b1)*2.0 + 1.0;
      vec4 sh = -step(h, vec4(0.0));

      vec4 a0 = b0.xzyw + s0.xzyw*sh.xxyy;
      vec4 a1 = b1.xzyw + s1.xzyw*sh.zzww;

      vec3 p0 = vec3(a0.xy, h.x);
      vec3 p1 = vec3(a0.zw, h.y);
      vec3 p2 = vec3(a1.xy, h.z);
      vec3 p3 = vec3(a1.zw, h.w);

      vec4 norm = taylorInvSqrt(vec4(dot(p0,p0), dot(p1,p1), dot(p2,p2), dot(p3,p3)));
      p0 *= norm.x;
      p1 *= norm.y;
      p2 *= norm.z;
      p3 *= norm.w;

      vec4 m = max(0.6 - vec4(dot(x0,x0), dot(x1,x1), dot(x2,x2), dot(x3,x3)), 0.0);
      m = m * m;
      return 42.0 * dot(m*m, vec4(dot(p0,x0), dot(p1,x1), dot(p2,x2), dot(p3,x3)));
    }

    void main() {
      vUv = uv;
      vNormal = normal;

      float t = uTime * uSpeed;

      // Multiple layers of smooth noise
      float noise1 = snoise(normal * uNoiseScale + t * 0.5);
      float noise2 = snoise(normal * uNoiseScale * 2.0 + t * 0.3) * 0.5;
      float noise3 = snoise(normal * uNoiseScale * 0.5 + t * 0.7) * 0.25;

      float displacement = (noise1 + noise2 + noise3) * uNoiseStrength;
      vDisplacement = displacement;

      vec3 pos = position + normal * displacement;
      vPosition = pos;

      gl_Position = projectionMatrix * modelViewMatrix * vec4(pos, 1.0);
    }
  `,
  // Fragment Shader - soft ethereal colors
  `
    varying vec2 vUv;
    varying vec3 vNormal;
    varying vec3 vPosition;
    varying float vDisplacement;

    uniform float uTime;
    uniform float uIntensity;
    uniform vec3 uColorA;
    uniform vec3 uColorB;
    uniform vec3 uColorC;

    void main() {
      // Soft fresnel for ethereal edge
      vec3 viewDirection = normalize(cameraPosition - vPosition);
      float fresnel = pow(1.0 - max(0.0, dot(viewDirection, vNormal)), 2.5);

      // Smooth color blending
      float colorMix = vDisplacement * 2.0 + 0.5;
      colorMix += sin(vUv.y * 3.14159 + uTime * 0.3) * 0.15;

      vec3 color = mix(uColorA, uColorB, smoothstep(0.2, 0.8, colorMix));
      color = mix(color, uColorC, fresnel * 0.6);

      // Soft inner glow
      float innerGlow = 0.6 + vDisplacement * 0.3;
      color *= innerGlow;

      // Edge glow
      color += fresnel * uColorC * uIntensity * 0.4;

      // Very soft, transparent look
      float alpha = 0.75 + fresnel * 0.2;

      gl_FragColor = vec4(color, alpha);
    }
  `
);

extend({ EtherealBlobMaterial });

declare global {
  namespace JSX {
    interface IntrinsicElements {
      etherealBlobMaterial: any;
    }
  }
}

// Ethereal blob mesh
function EtherealBlob({
  state = 'idle',
  inputVolume = 0,
  outputVolume = 0,
  colors = defaultColors,
  size = 1
}: OrbProps) {
  const meshRef = useRef<THREE.Mesh>(null);
  const materialRef = useRef<any>(null);

  const colorA = useMemo(() => new THREE.Color(colors.primary), [colors.primary]);
  const colorB = useMemo(() => new THREE.Color(colors.secondary), [colors.secondary]);
  const colorC = useMemo(() => new THREE.Color(colors.glow), [colors.glow]);

  useFrame((_, delta) => {
    if (!materialRef.current) return;

    materialRef.current.uTime += delta;

    const volume = state === 'speaking' ? outputVolume : inputVolume;
    const targetSpeed = { idle: 0.12, listening: 0.25, speaking: 0.35, thinking: 0.4 }[state];
    const targetStrength = { idle: 0.2, listening: 0.3, speaking: 0.4, thinking: 0.35 }[state];

    // Smooth interpolation
    materialRef.current.uSpeed += (targetSpeed + volume * 0.15 - materialRef.current.uSpeed) * 0.08;
    materialRef.current.uNoiseStrength += (targetStrength + volume * 0.2 - materialRef.current.uNoiseStrength) * 0.08;
    materialRef.current.uIntensity += ((1.0 + volume * 0.6) - materialRef.current.uIntensity) * 0.08;

    if (meshRef.current) {
      meshRef.current.rotation.y += delta * 0.05;
      meshRef.current.rotation.x += delta * 0.02;
    }
  });

  return (
    <mesh ref={meshRef} scale={size}>
      <icosahedronGeometry args={[1, 64]} />
      <etherealBlobMaterial
        ref={materialRef}
        uColorA={colorA}
        uColorB={colorB}
        uColorC={colorC}
        transparent
        side={THREE.DoubleSide}
        depthWrite={false}
        blending={THREE.AdditiveBlending}
      />
    </mesh>
  );
}

// Soft glow particles
function GlowParticles({ state, colors, size = 1 }: OrbProps) {
  const particlesRef = useRef<THREE.Points>(null);
  const count = 150;

  const positions = useMemo(() => {
    const positions = new Float32Array(count * 3);
    for (let i = 0; i < count; i++) {
      const theta = Math.random() * Math.PI * 2;
      const phi = Math.acos(2 * Math.random() - 1);
      const r = (size || 1) * (1.2 + Math.random() * 0.5);
      positions[i * 3] = r * Math.sin(phi) * Math.cos(theta);
      positions[i * 3 + 1] = r * Math.sin(phi) * Math.sin(theta);
      positions[i * 3 + 2] = r * Math.cos(phi);
    }
    return positions;
  }, [size]);

  useFrame((_, delta) => {
    if (particlesRef.current) {
      particlesRef.current.rotation.y += delta * 0.03;
      particlesRef.current.rotation.x += delta * 0.015;
    }
  });

  const isActive = state === 'speaking' || state === 'listening' || state === 'thinking';

  return (
    <points ref={particlesRef}>
      <bufferGeometry>
        <bufferAttribute
          attach="attributes-position"
          count={count}
          array={positions}
          itemSize={3}
        />
      </bufferGeometry>
      <pointsMaterial
        size={0.03}
        color={colors?.glow || defaultColors.glow}
        transparent
        opacity={isActive ? 0.5 : 0.25}
        sizeAttenuation
        blending={THREE.AdditiveBlending}
        depthWrite={false}
      />
    </points>
  );
}

// Inner core glow
function InnerCore({ colors, size = 1 }: OrbProps) {
  const meshRef = useRef<THREE.Mesh>(null);

  useFrame((state) => {
    if (meshRef.current) {
      const scale = 0.4 + Math.sin(state.clock.elapsedTime * 1.2) * 0.06;
      meshRef.current.scale.setScalar(scale * (size || 1));
    }
  });

  return (
    <mesh ref={meshRef}>
      <sphereGeometry args={[0.6, 32, 32]} />
      <meshBasicMaterial
        color={colors?.primary || defaultColors.primary}
        transparent
        opacity={0.3}
        blending={THREE.AdditiveBlending}
        depthWrite={false}
      />
    </mesh>
  );
}

// Scene
function OrbScene(props: OrbProps) {
  return (
    <>
      <ambientLight intensity={0.2} />
      <pointLight position={[5, 5, 5]} intensity={0.4} color="#ffffff" />
      <pointLight position={[-5, -5, -5]} intensity={0.2} color={props.colors?.secondary || defaultColors.secondary} />

      <InnerCore {...props} />
      <EtherealBlob {...props} />
      <GlowParticles {...props} />
    </>
  );
}

// Main component with CSS glow effect
export default function VoiceOrb({
  state = 'idle',
  inputVolume = 0,
  outputVolume = 0,
  colors = defaultColors,
  size = 1,
  className = ''
}: OrbProps & { className?: string }) {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  // Dynamic glow intensity based on state and volume
  const volume = state === 'speaking' ? outputVolume : inputVolume;
  const glowIntensity = state === 'idle' ? 0.4 : 0.6 + volume * 0.4;
  const blurAmount = 20 + volume * 15;

  if (!mounted) {
    return (
      <div className={`relative ${className}`}>
        <div
          className="w-full h-full rounded-full animate-pulse"
          style={{
            background: `radial-gradient(circle, ${colors?.primary || defaultColors.primary} 0%, ${colors?.secondary || defaultColors.secondary} 100%)`,
          }}
        />
      </div>
    );
  }

  return (
    <div className={`relative ${className}`}>
      {/* Outer glow layer */}
      <div
        className="absolute inset-0 rounded-full pointer-events-none"
        style={{
          background: `radial-gradient(circle, ${colors?.glow || defaultColors.glow}${Math.round(glowIntensity * 60).toString(16).padStart(2, '0')} 0%, transparent 70%)`,
          filter: `blur(${blurAmount}px)`,
          transform: 'scale(1.3)',
        }}
      />

      {/* Secondary glow */}
      <div
        className="absolute inset-0 rounded-full pointer-events-none"
        style={{
          background: `radial-gradient(circle, ${colors?.primary || defaultColors.primary}40 0%, transparent 60%)`,
          filter: `blur(${blurAmount * 0.7}px)`,
          transform: 'scale(1.15)',
        }}
      />

      {/* Canvas container with blur backdrop */}
      <div
        className="relative w-full h-full"
        style={{
          filter: `blur(${1 + volume * 2}px)`,
        }}
      >
        <Canvas
          camera={{ position: [0, 0, 3], fov: 50 }}
          style={{ background: 'transparent' }}
          gl={{
            antialias: true,
            alpha: true,
            powerPreference: 'high-performance',
          }}
        >
          <OrbScene
            state={state}
            inputVolume={inputVolume}
            outputVolume={outputVolume}
            colors={colors}
            size={size}
          />
        </Canvas>
      </div>

      {/* Inner soft glow overlay */}
      <div
        className="absolute inset-0 rounded-full pointer-events-none"
        style={{
          background: `radial-gradient(circle at 30% 30%, ${colors?.glow || defaultColors.glow}20 0%, transparent 50%)`,
        }}
      />
    </div>
  );
}

export type { OrbProps };
