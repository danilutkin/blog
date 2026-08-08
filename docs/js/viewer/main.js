import * as THREE from 'https://cdn.jsdelivr.net/npm/three@0.164.1/build/three.module.js';
import { SceneManager } from './SceneManager.js';
import { createTurbineScene } from './scenes/turbineScene.js';
import { createSolarSystemScene } from './scenes/solarSystemScene.js';

const canvas = document.getElementById('viewport');
const modelPicker = document.getElementById('modelPicker');
const speedSlider = document.getElementById('speed');
const speedValue = document.getElementById('speedValue');

const renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.outputColorSpace = THREE.SRGBColorSpace;

const scene = new THREE.Scene();
scene.background = new THREE.Color(0x090f1d);

const camera = new THREE.PerspectiveCamera(48, window.innerWidth / window.innerHeight, 0.1, 300);
const target = new THREE.Vector3(0, 1.6, 0);
let radius = 13.5;
let theta = 0.68;
let phi = 1.08;

function updateCamera() {
  const sinPhi = Math.sin(phi);
  camera.position.set(
    target.x + radius * sinPhi * Math.sin(theta),
    target.y + radius * Math.cos(phi),
    target.z + radius * sinPhi * Math.cos(theta),
  );
  camera.lookAt(target);
}
updateCamera();

let dragging = false;
let lastX = 0;
let lastY = 0;

canvas.style.touchAction = 'none';
canvas.addEventListener('pointerdown', (event) => {
  dragging = true;
  lastX = event.clientX;
  lastY = event.clientY;
  canvas.setPointerCapture?.(event.pointerId);
});

canvas.addEventListener('pointermove', (event) => {
  if (!dragging) return;
  const dx = event.clientX - lastX;
  const dy = event.clientY - lastY;
  lastX = event.clientX;
  lastY = event.clientY;

  theta -= dx * 0.008;
  phi = THREE.MathUtils.clamp(phi + dy * 0.008, 0.2, Math.PI - 0.2);
  updateCamera();
});

function stopDragging(event) {
  dragging = false;
  canvas.releasePointerCapture?.(event.pointerId);
}
canvas.addEventListener('pointerup', stopDragging);
canvas.addEventListener('pointercancel', stopDragging);

canvas.addEventListener('wheel', (event) => {
  event.preventDefault();
  radius = THREE.MathUtils.clamp(radius * Math.exp(event.deltaY * 0.001), 3.5, 40);
  updateCamera();
}, { passive: false });

let pinchDistance = null;
const activeTouches = new Map();
canvas.addEventListener('pointerdown', (event) => {
  if (event.pointerType === 'touch') activeTouches.set(event.pointerId, { x: event.clientX, y: event.clientY });
});
canvas.addEventListener('pointermove', (event) => {
  if (event.pointerType !== 'touch' || !activeTouches.has(event.pointerId)) return;
  activeTouches.set(event.pointerId, { x: event.clientX, y: event.clientY });
  if (activeTouches.size === 2) {
    const [a, b] = [...activeTouches.values()];
    const distance = Math.hypot(a.x - b.x, a.y - b.y);
    if (pinchDistance !== null && distance > 0) {
      radius = THREE.MathUtils.clamp(radius * (pinchDistance / distance), 3.5, 40);
      updateCamera();
    }
    pinchDistance = distance;
  }
});
function clearTouch(event) {
  activeTouches.delete(event.pointerId);
  if (activeTouches.size < 2) pinchDistance = null;
}
canvas.addEventListener('pointerup', clearTouch);
canvas.addEventListener('pointercancel', clearTouch);

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
  if (modelPicker.value === 'solar') {
    target.set(0, 0, 0);
    radius = 16;
    phi = 1.1;
    manager.setScene(createSolarSystemScene);
  } else {
    target.set(0, 1.6, 0);
    radius = 13.5;
    phi = 1.08;
    manager.setScene(createTurbineScene);
  }
  updateCamera();
});

speedSlider.addEventListener('input', () => {
  speedMultiplier = Number(speedSlider.value);
  speedValue.textContent = `${speedMultiplier.toFixed(1)}x`;
});

function animate() {
  requestAnimationFrame(animate);
  const delta = Math.min(clock.getDelta(), 0.1);
  manager.update(delta, speedMultiplier);
  renderer.render(scene, camera);
}
animate();
