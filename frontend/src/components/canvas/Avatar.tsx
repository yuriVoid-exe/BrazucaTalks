// src/components/canvas/Avatar.tsx
import React, { useMemo, useEffect, useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import { useGLTF, useAnimations } from '@react-three/drei';
import * as THREE from 'three';

interface AvatarProps {
  url: string;
  animationUrl: string;
  audioAnalyser: AnalyserNode | null;
}

export default function Avatar({ url, animationUrl, audioAnalyser }: AvatarProps) {
  const { scene } = useGLTF(url);
  const { animations: mixamoAnimations } = useGLTF(animationUrl);
  const { actions } = useAnimations(mixamoAnimations, scene);
  const headRef = useRef<THREE.Object3D | null>(null);

  const targets = useMemo(() => {
    const map: any = { speech: [], blink: [], expression: [] };
    scene.traverse((obj: any) => {
      if (obj.isMesh && obj.morphTargetDictionary) {
        const dict = obj.morphTargetDictionary;
        if (dict['viseme_aa'] !== undefined) map.speech.push({ mesh: obj, index: dict['viseme_aa'] });
        if (dict['eyeBlinkLeft'] !== undefined) map.blink.push({ mesh: obj, index: dict['eyeBlinkLeft'] });
        if (dict['eyeBlinkRight'] !== undefined) map.blink.push({ mesh: obj, index: dict['eyeBlinkRight'] });
        if (dict['mouthSmile'] !== undefined) map.expression.push({ mesh: obj, index: dict['mouthSmile'] });
      }
      if (obj.name.toLowerCase().includes('head')) headRef.current = obj;
    });
      return map;
  }, [scene]);

  useEffect(() => {
    if (actions) {
      const animName = Object.keys(actions)[0];
      if (animName) actions[animName]?.reset().fadeIn(0.5).play();
    }
  }, [actions]);

  useFrame((state) => {
    const t = state.clock.elapsedTime;

    if (headRef.current) {
      const target = new THREE.Vector3(state.mouse.x * 0.4, state.mouse.y * 0.2 + 1.2, 2);
      headRef.current.lookAt(target);
    }

    const blinkStrength = Math.sin(t * 1.5) > 0.98 ? 1 : 0;
    targets.blink.forEach((b: any) => {
      b.mesh.morphTargetInfluences[b.index] = THREE.MathUtils.lerp(
        b.mesh.morphTargetInfluences[b.index], blinkStrength, 0.5
      );
    });

    if (audioAnalyser && targets.speech.length > 0) {
      const dataArray = new Uint8Array(audioAnalyser.frequencyBinCount);
      audioAnalyser.getByteFrequencyData(dataArray);
      const volume = dataArray.reduce((a, b) => a + b) / dataArray.length;
      const influence = Math.min(1, (volume / 100) * 2.8);
      targets.speech.forEach((s: any) => {
        s.mesh.morphTargetInfluences[s.index] = THREE.MathUtils.lerp(
          s.mesh.morphTargetInfluences[s.index], influence, 0.8
        );
      });
    }

    targets.expression.forEach((e: any) => {
      e.mesh.morphTargetInfluences[e.index] = 0.2;
    });
  });

  // --- ALTERAÇÃO DE ENQUADRAMENTO ---
  // Scale 3.2 e Position Y em -4.5 para mostrar da cintura para cima
  return <primitive object={scene} scale={2.8} position={[0, -3.8, 0]} />;
}
