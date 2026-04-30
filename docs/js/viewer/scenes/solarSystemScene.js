import * as THREE from 'https://cdn.jsdelivr.net/npm/three@0.164.1/build/three.module.js';

const sharedGeometry = new THREE.SphereGeometry(1, 32, 32);

function createPlanet({ radius, distance, color, orbitSpeed, selfSpeed }) {
  const pivot = new THREE.Object3D();

  const material = new THREE.MeshStandardMaterial({ color, roughness: 0.85, metalness: 0.05 });
  const mesh = new THREE.Mesh(sharedGeometry, material);
  mesh.scale.setScalar(radius);
  mesh.position.x = distance;

  pivot.add(mesh);

  return { pivot, mesh, orbitSpeed, selfSpeed, material };
}

export function createSolarSystemScene() {
  const root = new THREE.Group();
  root.name = 'solar-system-scene';

  const sunGeo = new THREE.SphereGeometry(1.4, 48, 48);
  const sunMat = new THREE.MeshStandardMaterial({ emissive: 0xffb347, emissiveIntensity: 2.3, color: 0x33210a });
  const sun = new THREE.Mesh(sunGeo, sunMat);
  root.add(sun);

  const sunLight = new THREE.PointLight(0xffcc66, 2.8, 180, 2);
  sunLight.position.set(0, 0, 0);
  root.add(sunLight);
  root.add(new THREE.AmbientLight(0x223044, 0.28));

  const planets = [
    createPlanet({ radius: 0.25, distance: 2.5, color: 0xc0c0c0, orbitSpeed: 1.2, selfSpeed: 2.0 }),
    createPlanet({ radius: 0.34, distance: 3.4, color: 0xdcb98f, orbitSpeed: 0.9, selfSpeed: 1.8 }),
    createPlanet({ radius: 0.37, distance: 4.4, color: 0x5b8cff, orbitSpeed: 0.7, selfSpeed: 2.3 }),
    createPlanet({ radius: 0.31, distance: 5.3, color: 0xb95432, orbitSpeed: 0.55, selfSpeed: 1.7 }),
    createPlanet({ radius: 0.76, distance: 7.2, color: 0xcfb476, orbitSpeed: 0.22, selfSpeed: 2.8 }),
  ];

  planets.forEach((p) => root.add(p.pivot));

  return {
    root,
    update(delta, speedMultiplier) {
      sun.rotation.y += delta * 0.2 * speedMultiplier;
      planets.forEach((planet) => {
        planet.pivot.rotation.y += delta * planet.orbitSpeed * speedMultiplier;
        planet.mesh.rotation.y += delta * planet.selfSpeed * speedMultiplier;
      });
    },
    dispose() {
      planets.forEach((p) => p.material.dispose());
      sunGeo.dispose();
      sunMat.dispose();
      root.removeFromParent();
    },
  };
}
