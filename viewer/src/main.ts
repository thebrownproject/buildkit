import * as THREE from "three";
import * as OBC from "@thatopen/components";

// 1. Create components + world
const components = new OBC.Components();
const worlds = components.get(OBC.Worlds);
const world = worlds.create<
  OBC.SimpleScene,
  OBC.OrthoPerspectiveCamera,
  OBC.SimpleRenderer
>();

// 2. Set up scene with dark background
world.scene = new OBC.SimpleScene(components);
world.scene.setup();
world.scene.three.background = new THREE.Color(0x1a1d23);

// 3. Set up renderer with the container div
const container = document.getElementById("container")!;
world.renderer = new OBC.SimpleRenderer(components, container);

// 4. Set up camera
world.camera = new OBC.OrthoPerspectiveCamera(components);

// 5. Add grid
const grids = components.get(OBC.Grids);
grids.create(world);

// 6. Init components
components.init();

// 7. Set up FragmentsManager with worker
const fragments = components.get(OBC.FragmentsManager);
fragments.init("/node_modules/@thatopen/fragments/dist/Worker/worker.mjs");

// 8. Handle model loading — when a model is added, show it in the scene
fragments.list.onItemSet.add(({ value: model }) => {
  model.useCamera(world.camera.three);
  world.scene.three.add(model.object);
  fragments.core.update(true);
});

// 9. Camera update triggers fragment LOD update
world.camera.controls.addEventListener("update", () =>
  fragments.core.update()
);

// 10. Set up IFC loader with CDN WASM
const ifcLoader = components.get(OBC.IfcLoader);
await ifcLoader.setup({
  autoSetWasm: false,
  wasm: {
    path: "https://unpkg.com/web-ifc@0.0.77/",
    absolute: true,
  },
});

// 11. Drag-and-drop handler
container.addEventListener("dragover", (e) => {
  e.preventDefault();
  e.stopPropagation();
  container.classList.add("drag-over");
});

container.addEventListener("dragleave", () => {
  container.classList.remove("drag-over");
});

container.addEventListener("drop", async (e) => {
  e.preventDefault();
  e.stopPropagation();
  container.classList.remove("drag-over");
  const file = e.dataTransfer?.files[0];
  if (!file || !file.name.toLowerCase().endsWith(".ifc")) return;
  const data = await file.arrayBuffer();
  const buffer = new Uint8Array(data);
  await ifcLoader.load(buffer, true, file.name);
});

// 12. File picker button handler
const loadBtn = document.getElementById("load-btn")!;
const fileInput = document.createElement("input");
fileInput.type = "file";
fileInput.accept = ".ifc";
fileInput.addEventListener("change", async () => {
  const file = fileInput.files?.[0];
  if (!file) return;
  const data = await file.arrayBuffer();
  const buffer = new Uint8Array(data);
  await ifcLoader.load(buffer, true, file.name);
});
loadBtn.addEventListener("click", () => fileInput.click());
