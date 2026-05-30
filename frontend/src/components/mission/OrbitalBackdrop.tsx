import { Canvas, useFrame } from "@react-three/fiber";
import { useMemo, useRef } from "react";
import type { Group, Points } from "three";

function StarField() {
  const ref = useRef<Points>(null);
  const positions = useMemo(() => {
    const data = new Float32Array(360 * 3);
    for (let i = 0; i < 360; i += 1) {
      const radius = 2.8 + Math.random() * 4.5;
      const theta = Math.random() * Math.PI * 2;
      const phi = Math.acos(2 * Math.random() - 1);
      data[i * 3] = radius * Math.sin(phi) * Math.cos(theta);
      data[i * 3 + 1] = radius * Math.sin(phi) * Math.sin(theta);
      data[i * 3 + 2] = radius * Math.cos(phi);
    }
    return data;
  }, []);

  useFrame((_state, delta) => {
    if (ref.current) {
      ref.current.rotation.y += delta * 0.012;
      ref.current.rotation.x += delta * 0.004;
    }
  });

  return (
    <points ref={ref}>
      <bufferGeometry>
        <bufferAttribute attach="attributes-position" args={[positions, 3]} />
      </bufferGeometry>
      <pointsMaterial size={0.018} color="#7cefff" transparent opacity={0.72} />
    </points>
  );
}

function OrbitRings() {
  const ref = useRef<Group>(null);

  useFrame((_state, delta) => {
    if (ref.current) {
      ref.current.rotation.z += delta * 0.02;
    }
  });

  return (
    <group ref={ref} rotation={[0.9, 0.4, 0.1]}>
      {[1.25, 1.72, 2.22].map((radius, index) => (
        <mesh key={radius} rotation={[Math.PI / 2, 0, index * 0.35]}>
          <torusGeometry args={[radius, 0.003, 8, 144]} />
          <meshBasicMaterial color={index === 1 ? "#8ff0c1" : "#42f2ff"} transparent opacity={0.22} />
        </mesh>
      ))}
    </group>
  );
}

export function OrbitalBackdrop() {
  if (import.meta.env.MODE === "test") {
    return <div data-testid="orbital-backdrop" className="fixed inset-0 -z-10 bg-void" />;
  }

  return (
    <div aria-hidden="true" className="fixed inset-0 -z-10 overflow-hidden bg-void">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_72%_18%,rgba(66,242,255,0.10),transparent_34%),radial-gradient(circle_at_20%_90%,rgba(143,240,193,0.08),transparent_28%),linear-gradient(180deg,#03070f_0%,#050c18_55%,#02050b_100%)]" />
      <div className="absolute inset-0 bg-console-grid bg-[length:62px_62px] opacity-35" />
      <Canvas camera={{ position: [0, 0, 4.7], fov: 55 }} dpr={[1, 1.45]} gl={{ antialias: false }}>
        <StarField />
        <OrbitRings />
      </Canvas>
      <div className="absolute inset-0 bg-gradient-to-b from-transparent via-void/35 to-void" />
    </div>
  );
}
