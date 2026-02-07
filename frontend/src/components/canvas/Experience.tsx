import { Suspense } from 'react';
import { Canvas } from '@react-three/fiber';
import { Environment, ContactShadows } from '@react-three/drei';
import Avatar from './Avatar';

const AVATAR_URL = "https://models.readyplayer.me/68b78306f223bbc6cb587ac4.glb";

export default function Experience({ analyser }: { analyser: any }) {
  return (
    <Canvas camera={{ position: [0, 0, 3], fov: 40 }} dpr={[1, 1.5]}>
      <ambientLight intensity={0.5} />
      <Environment preset="city" />
      <Suspense fallback={null}>
        <Avatar url={AVATAR_URL} audioAnalyser={analyser} />
      </Suspense>
      <ContactShadows opacity={0.5} scale={10} blur={2.5} far={4} />
    </Canvas>
  );
}
