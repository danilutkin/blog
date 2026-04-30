export class SceneManager {
  constructor(scene) {
    this.scene = scene;
    this.current = null;
  }

  setScene(createSceneFn) {
    if (this.current) {
      this.current.dispose();
      this.current = null;
    }

    this.current = createSceneFn();
    this.scene.add(this.current.root);
  }

  update(delta, speedMultiplier) {
    if (this.current?.update) {
      this.current.update(delta, speedMultiplier);
    }
  }
}
