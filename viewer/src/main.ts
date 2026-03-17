import * as THREE from "three";
import * as OBC from "@thatopen/components";
import * as OBCF from "@thatopen/components-front";
import * as BUI from "@thatopen/ui";
import * as BUIC from "@thatopen/ui-obc";
import fragmentWorkerUrl from "@thatopen/fragments/worker?url";

// 1. Init BUI (registers custom elements — MUST be first)
BUI.Manager.init();

// 2. Components + World
const components = new OBC.Components();
const worlds = components.get(OBC.Worlds);
const world = worlds.create<
  OBC.SimpleScene,
  OBC.OrthoPerspectiveCamera,
  OBC.SimpleRenderer
>();

// 3. Scene
world.scene = new OBC.SimpleScene(components);
world.scene.setup();
world.scene.three.background = new THREE.Color(0x1a1d23);

// 4. Renderer — use bim-viewport as container
const viewport = document.createElement("bim-viewport");
world.renderer = new OBC.SimpleRenderer(components, viewport);

// 5. Camera
world.camera = new OBC.OrthoPerspectiveCamera(components);

// 6. Handle viewport resize
viewport.addEventListener("resize", () => {
  world.renderer!.resize();
  world.camera.updateAspect();
});

// 7. Grid + init
const grid = components.get(OBC.Grids).create(world);
grid.config.color = new THREE.Color(0x888888);
components.init();

// Theme state
let isDarkTheme = true;

// 8. Fragments
const fragments = components.get(OBC.FragmentsManager);
fragments.init(fragmentWorkerUrl);

// Camera-driven fragment updates (replaces the frozen approach)
world.camera.controls.addEventListener("update", () =>
  fragments.core.update(),
);

// Model loading — scene setup only; classification happens after load completes
fragments.list.onItemSet.add(({ value: model }) => {
  model.useCamera(world.camera.three);
  world.scene.three.add(model.object);
  fragments.core.update(true);
});

// 9. IFC Loader
const ifcLoader = components.get(OBC.IfcLoader);
await ifcLoader.setup({
  autoSetWasm: false,
  wasm: {
    path: "https://unpkg.com/web-ifc@0.0.77/",
    absolute: true,
  },
});

// 10. Highlighter (click to select)
const highlighter = components.get(OBCF.Highlighter);
highlighter.setup({ world });
highlighter.zoomToSelection = true;

// 11. Hoverer (hover to preview)
const hoverer = components.get(OBCF.Hoverer);
hoverer.world = world;
hoverer.enabled = true;
hoverer.material = new THREE.MeshBasicMaterial({
  color: 0x6528d7,
  transparent: true,
  opacity: 0.5,
  depthTest: false,
});

// 12. Classifier + Hider (visibility toggles)
const classifier = components.get(OBC.Classifier);
const hider = components.get(OBC.Hider);

// Visibility container for dynamic checkboxes (populated after model loads)
const visibilityContainer = document.createElement("div");

function formatCategoryName(name: string): string {
  // Raw names are ALL CAPS like "IFCFURNISHINGELEMENT"
  // Convert to Title Case: strip IFC prefix, lowercase, then capitalize words
  const stripped = name
    .replace("IFCWALLSTANDARDCASE", "IFCWALL")
    .replace(/^IFC/, "");
  // Insert space before each uppercase-to-lowercase boundary in camelCase,
  // or just split known compound words for ALL CAPS input
  const words = stripped
    .replace(/([a-z])([A-Z])/g, "$1 $2")  // camelCase split
    .replace(/([A-Z]+)([A-Z][a-z])/g, "$1 $2")  // consecutive caps split
    .split(/(?=[A-Z][a-z])/)  // split before Cap+lowercase
    .join(" ")
    .trim();
  // If still all caps (no camelCase detected), just title-case it
  if (words === words.toUpperCase()) {
    return words.charAt(0) + words.slice(1).toLowerCase();
  }
  return words;
}

async function updateVisibilityPanel() {
  await classifier.byCategory();
  const categories = classifier.list.get("Categories");
  if (!categories) return;

  visibilityContainer.innerHTML = "";

  for (const [categoryName, groupData] of categories) {
    const checkbox = document.createElement("bim-checkbox") as BUI.Checkbox;
    checkbox.label = formatCategoryName(categoryName);
    checkbox.checked = true;
    checkbox.addEventListener("change", async () => {
      const visible = checkbox.checked;
      const items = await classifier.find({ Categories: [categoryName] });
      await hider.set(visible, items);
    });
    visibilityContainer.appendChild(checkbox);
  }
}

// "Show All" reset button
const showAllBtn = document.createElement("bim-button") as BUI.Button;
showAllBtn.label = "Show All";
showAllBtn.icon = "mdi:eye";
showAllBtn.addEventListener("click", async () => {
  await hider.set(true);
  visibilityContainer.querySelectorAll("bim-checkbox").forEach((cb) => {
    (cb as BUI.Checkbox).checked = true;
  });
});

// 13. Hover Tooltip — driven by mousemove with debounce, not Hoverer events
const tooltip = document.createElement("div");
tooltip.className = "hover-tooltip";
document.body.appendChild(tooltip);

const raycasters = components.get(OBC.Raycasters);
const caster = raycasters.get(world);

let tooltipTimer: ReturnType<typeof setTimeout> | null = null;
let lastTooltipId: number | null = null;

viewport.addEventListener("mousemove", (e) => {
  tooltip.style.left = `${e.clientX + 15}px`;
  tooltip.style.top = `${e.clientY + 15}px`;

  // Debounce the raycast — only query after mouse settles for 80ms
  if (tooltipTimer) clearTimeout(tooltipTimer);
  tooltipTimer = setTimeout(async () => {
    try {
      const result = await caster.castRay();
      if (!result || !("fragments" in result)) {
        tooltip.style.display = "none";
        lastTooltipId = null;
        return;
      }
      const { fragments: model, localId } = result as any;
      // Skip if same element as last time
      if (localId === lastTooltipId) return;
      lastTooltipId = localId;
      const items = await model.getItemsData([localId], {
        attributes: ["Name", "_category"],
        attributesDefault: false,
      });
      if (items.length > 0) {
        const item = items[0];
        const name = item.Name?.value ?? "Unnamed";
        const type = (item._category?.value ?? "Unknown")
          .replace("IFC", "")
          .replace(/([A-Z])/g, " $1")
          .trim();
        tooltip.innerHTML = `<strong>${name}</strong><br/>${type}`;
        tooltip.style.display = "block";
      }
    } catch {
      tooltip.style.display = "none";
      lastTooltipId = null;
    }
  }, 80);
});

viewport.addEventListener("mouseleave", () => {
  if (tooltipTimer) clearTimeout(tooltipTimer);
  tooltip.style.display = "none";
  lastTooltipId = null;
});

// 13. Spatial Tree
const [spatialTree] = BUIC.tables.spatialTree({
  components,
  models: [],
});
spatialTree.preserveStructureOnFilter = true;

// 14. Properties Table
const [propertiesTable, updatePropertiesTable] = BUIC.tables.itemsData({
  components,
  modelIdMap: {},
});
propertiesTable.preserveStructureOnFilter = true;
propertiesTable.indentationInText = false;

// Wire properties to selection
highlighter.events.select.onHighlight.add((modelIdMap) => {
  updatePropertiesTable({ modelIdMap });
});
highlighter.events.select.onClear.add(() => {
  updatePropertiesTable({ modelIdMap: {} });
});

// 15. IFC file loading function (used by drag-drop and button)
async function loadIfc(file: File) {
  const data = await file.arrayBuffer();
  const buffer = new Uint8Array(data);
  await ifcLoader.load(buffer, true, file.name);
  // Classify after load completes — model data is fully available at this point
  await updateVisibilityPanel();
}

// 16. Drag-and-drop on viewport
viewport.addEventListener("dragover", (e) => {
  e.preventDefault();
  e.stopPropagation();
});
viewport.addEventListener("drop", async (e) => {
  e.preventDefault();
  e.stopPropagation();
  const file = e.dataTransfer?.files[0];
  if (!file || !file.name.toLowerCase().endsWith(".ifc")) return;
  await loadIfc(file);
});

// File picker (hidden input)
const fileInput = document.createElement("input");
fileInput.type = "file";
fileInput.accept = ".ifc";
fileInput.addEventListener("change", async () => {
  const file = fileInput.files?.[0];
  if (!file) return;
  await loadIfc(file);
});

// 17. Build UI panels using BUI.Component.create + BUI.html

// Left panel — tree + load button
const treePanel = BUI.Component.create(() => {
  return BUI.html`
    <bim-panel label="Model">
      <bim-panel-section label="Import" icon="solar:import-bold">
        <bim-button label="Load IFC" icon="mdi:file-upload"
          @click=${() => fileInput.click()}>
        </bim-button>
        <bim-button label="Toggle Theme" icon="mdi:weather-sunny"
          tooltip-title="Toggle Theme"
          @click=${(e: Event) => {
            // Track state ourselves — toggleTheme animates with delay so class check is unreliable
            isDarkTheme = !isDarkTheme;
            BUI.Manager.toggleTheme();
            const btn = e.target as BUI.Button;
            btn.icon = isDarkTheme ? "mdi:weather-sunny" : "mdi:weather-night";
            world.scene.three.background = new THREE.Color(isDarkTheme ? 0x1a1d23 : 0xf0f0f0);
            grid.config.color = new THREE.Color(isDarkTheme ? 0x666666 : 0xbbbbbb);
          }}>
        </bim-button>
      </bim-panel-section>
      <bim-panel-section label="Spatial Tree" icon="ph:tree-structure-bold">
        <bim-text-input
          placeholder="Search..."
          debounce="200"
          @input=${(e: Event) => {
            spatialTree.queryString = (e.target as BUI.TextInput).value;
          }}>
        </bim-text-input>
        ${spatialTree}
      </bim-panel-section>
      <bim-panel-section label="Visibility" icon="mdi:eye">
        ${showAllBtn}
        ${visibilityContainer}
      </bim-panel-section>
    </bim-panel>
  `;
});

// Right panel — properties
const propertiesPanel = BUI.Component.create(() => {
  return BUI.html`
    <bim-panel label="Properties">
      <bim-panel-section label="Element Data" icon="fluent:document-data-16-filled">
        <bim-text-input
          placeholder="Search property..."
          debounce="250"
          @input=${(e: Event) => {
            propertiesTable.queryString =
              (e.target as BUI.TextInput).value || null;
          }}>
        </bim-text-input>
        ${propertiesTable}
      </bim-panel-section>
    </bim-panel>
  `;
});

// 18. Assemble grid layout
const app = document.getElementById("app") as BUI.Grid<["main"]>;
app.layouts = {
  main: {
    template: `
      "treePanel viewport propertiesPanel"
      / 20rem 1fr 25rem
    `,
    elements: { treePanel, viewport, propertiesPanel },
  },
};
app.layout = "main";
