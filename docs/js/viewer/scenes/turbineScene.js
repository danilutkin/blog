import * as THREE from 'https://cdn.jsdelivr.net/npm/three@0.164.1/build/three.module.js';

export function createTurbineScene() {
  const root = new THREE.Group();
  root.name = 'turbine-scene';

  const sharedGeo = {
    blade: new THREE.BoxGeometry(0.45, 2.4, 0.16),
    root: new THREE.BoxGeometry(0.7, 0.5, 0.4),
    base: new THREE.CylinderGeometry(1.4, 1.4, 0.2, 40),
  };

  const sharedMat = {
    blade: new THREE.MeshStandardMaterial({ color: 0xa9b4c4, metalness: 0.82, roughness: 0.22 }),
    root: new THREE.MeshStandardMaterial({ color: 0x6c788a, metalness: 0.7, roughness: 0.35 }),
    base: new THREE.MeshStandardMaterial({ color: 0x2a3447, metalness: 0.35, roughness: 0.9 }),
  };

  const blade = new THREE.Mesh(sharedGeo.blade, sharedMat.blade);
  blade.position.y = 1.25;
  blade.rotation.z = 0.18;

  const bladeRoot = new THREE.Mesh(sharedGeo.root, sharedMat.root);
  bladeRoot.position.y = 0.15;

  const base = new THREE.Mesh(sharedGeo.base, sharedMat.base);
  base.position.y = -0.1;

  root.add(blade, bladeRoot, base);

  const ambient = new THREE.AmbientLight(0xffffff, 0.45);
  const key = new THREE.DirectionalLight(0xffffff, 1.6);
  key.position.set(2.5, 3.5, 2.4);
  root.add(ambient, key);

  return {
    root,
    update(delta, speedMultiplier) {
      root.rotation.y += delta * 0.45 * speedMultiplier;
      blade.rotation.y += delta * 1.0 * speedMultiplier;
    },
    dispose() {
      root.traverse((obj) => {
        if (!obj.isMesh) return;
        obj.geometry?.dispose();
        if (Array.isArray(obj.material)) obj.material.forEach((m) => m.dispose());
        else obj.material?.dispose();
      });
      root.removeFromParent();
    },
  };
}
