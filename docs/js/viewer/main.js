import * as THREE from 'https://cdn.jsdelivr.net/npm/three@0.164.1/build/three.module.js';
import { OrbitControls } from 'https://cdn.jsdelivr.net/npm/three@0.164.1/examples/jsm/controls/OrbitControls.js';
import { SceneManager } from './SceneManager.js';
import { createTurbineScene } from './scenes/turbineScene.js';
import { createSolarSystemScene } from './scenes/solarSystemScene.js';

const canvas = document.getElementById('viewport');
const modelPicker = document.getElementById('modelPicker');
const speedSlider = document.getElementById('speed');
const speedValue = document.getElementById('speedValue');

const renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.outputColorSpace = THREE.SRGBColorSpace;

const scene = new THREE.Scene();
scene.background = new THREE.Color(0x090f1d);

const camera = new THREE.PerspectiveCamera(48, window.innerWidth / window.innerHeight, 0.1, 300);
camera.position.set(8, 5, 10);

const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;
controls.target.set(0, 1.6, 0);

const manager = new SceneManager(scene);
manager.setScene(createTurbineScene);

let speedMultiplier = Number(speedSlider.value);
const clock = new THREE.Clock();

function onResize() {
  camera.aspect = window.innerWidth / window.innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(window.innerWidth, window.innerHeight);
}
window.addEventListener('resize', onResize);

modelPicker.addEventListener('change', () => {
  if (modelPicker.value === 'solar') manager.setScene(createSolarSystemScene);
  else manager.setScene(createTurbineScene);
});

speedSlider.addEventListener('input', () => {
  speedMultiplier = Number(speedSlider.value);
  speedValue.textContent = `${speedMultiplier.toFixed(1)}x`;
});

function animate() {
  requestAnimationFrame(animate);
  const delta = clock.getDelta();
  controls.update();
  manager.update(delta, speedMultiplier);
  renderer.render(scene, camera);
}
animate();
