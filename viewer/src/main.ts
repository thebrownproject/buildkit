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
  OBCF.RendererWith2D
>();

// 3. Scene
world.scene = new OBC.SimpleScene(components);
world.scene.setup();
world.scene.three.background = new THREE.Color(0x1a1d23);

// 4. Renderer — use bim-viewport as container
const viewport = document.createElement("bim-viewport");
world.renderer = new OBCF.RendererWith2D(components, viewport);

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

// Clipping state
let clippingEnabled = false;

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

// 12b. Clipper (section cuts)
const clipper = components.get(OBC.Clipper);
clipper.setup({
  color: new THREE.Color("#202932"),
  opacity: 0.2,
  size: 5,
});

// 12c. Measurement tools
const lengthMeasurer = components.get(OBCF.LengthMeasurement);
lengthMeasurer.world = world;
lengthMeasurer.color = new THREE.Color("#494cb6");
lengthMeasurer.units = "mm";
lengthMeasurer.rounding = 0;
lengthMeasurer.enabled = false;

const areaMeasurer = components.get(OBCF.AreaMeasurement);
areaMeasurer.world = world;
areaMeasurer.color = new THREE.Color("#49b664");
areaMeasurer.units = "m2";
areaMeasurer.rounding = 2;
areaMeasurer.enabled = false;

// 12d. Mode management
type ViewerMode = "select" | "measure-length" | "measure-area";
let currentMode: ViewerMode = "select";

function setMode(mode: ViewerMode) {
  currentMode = mode;

  // Disable all modes first
  highlighter.enabled = false;
  hoverer.enabled = false;
  lengthMeasurer.enabled = false;
  areaMeasurer.enabled = false;

  switch (mode) {
    case "select":
      highlighter.enabled = true;
      hoverer.enabled = true;
      break;
    case "measure-length":
      lengthMeasurer.enabled = true;
      break;
    case "measure-area":
      areaMeasurer.enabled = true;
      break;
  }
}

// Start in select mode
setMode("select");

viewport.addEventListener("dblclick", () => {
  if (clipper.enabled) {
    clipper.create(world);
  } else if (lengthMeasurer.enabled) {
    lengthMeasurer.create();
  } else if (areaMeasurer.enabled) {
    areaMeasurer.create();
  }
});

window.addEventListener("keydown", (event) => {
  if (event.code === "Delete" || event.code === "Backspace") {
    if (clipper.enabled) clipper.delete(world);
    if (lengthMeasurer.enabled) lengthMeasurer.delete();
    if (areaMeasurer.enabled) areaMeasurer.delete();
  }
  if (event.code === "Enter" || event.code === "NumpadEnter") {
    if (areaMeasurer.enabled) areaMeasurer.endCreation();
  }
  if (event.code === "Escape") {
    setMode("select");
    // Update tool button active states in the UI
    document.querySelectorAll("[data-tool-btn]").forEach((btn) => {
      (btn as BUI.Button).active = (btn as HTMLElement).dataset.toolBtn === "select";
    });
  }
});

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

// 15b. Screenshot handler — force render then capture
function takeScreenshot() {
  world.renderer!.three.render(world.scene.three, world.camera.three);
  world.renderer!.three.domElement.toBlob((blob) => {
    if (!blob) return;
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `buildkit-screenshot-${Date.now()}.png`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  }, "image/png");
}

// 15c. Load IFC from URL (also supports ?url= query parameter)
async function loadIfcFromUrl(url: string) {
  try {
    const response = await fetch(url);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const data = await response.arrayBuffer();
    const buffer = new Uint8Array(data);
    const name = url.split("/").pop() || "model.ifc";
    await ifcLoader.load(buffer, true, name);
    await updateVisibilityPanel();
  } catch (err) {
    console.error("Failed to load IFC from URL:", err);
  }
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

// 16b. Tool button state helper
function updateToolButtons(activeBtn: BUI.Button) {
  document.querySelectorAll("[data-tool-btn]").forEach((btn) => {
    (btn as BUI.Button).active = false;
  });
  activeBtn.active = true;
}

// 17. Build UI panels using BUI.Component.create + BUI.html

// Left panel — tree + load button
const treePanel = BUI.Component.create(() => {
  return BUI.html`
    <bim-panel label="Model">
      <bim-panel-section label="Import" icon="solar:import-bold">
        <bim-button label="Load IFC" icon="mdi:file-upload"
          @click=${() => fileInput.click()}>
        </bim-button>
        <bim-button label="Load Sample" icon="mdi:home"
          @click=${() => loadIfcFromUrl(`${import.meta.env.BASE_URL}demo_house.ifc`)}>
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
        <bim-button label="Screenshot" icon="mdi:camera"
          @click=${() => takeScreenshot()}>
        </bim-button>
        <bim-text-input placeholder="IFC URL..." debounce="0"
          @keydown=${async (e: KeyboardEvent) => {
            if (e.key === "Enter") {
              const input = e.target as BUI.TextInput;
              if (input.value) await loadIfcFromUrl(input.value);
            }
          }}>
        </bim-text-input>
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
      <bim-panel-section label="Tools" icon="mdi:tools">
        <bim-button
          data-tool-btn="select"
          label="Select"
          icon="mdi:cursor-default"
          active
          @click=${(e: Event) => {
            setMode("select");
            updateToolButtons(e.target as BUI.Button);
          }}>
        </bim-button>
        <bim-button
          label="Section Cut"
          icon="mdi:box-cutter"
          @click=${(e: Event) => {
            clippingEnabled = !clippingEnabled;
            clipper.enabled = clippingEnabled;
            const btn = e.target as BUI.Button;
            btn.active = clippingEnabled;
          }}>
        </bim-button>
        <bim-button
          data-tool-btn="measure-length"
          label="Measure Distance"
          icon="mdi:ruler"
          @click=${(e: Event) => {
            setMode("measure-length");
            updateToolButtons(e.target as BUI.Button);
          }}>
        </bim-button>
        <bim-button
          data-tool-btn="measure-area"
          label="Measure Area"
          icon="mdi:vector-square"
          @click=${(e: Event) => {
            setMode("measure-area");
            updateToolButtons(e.target as BUI.Button);
          }}>
        </bim-button>
        <bim-button
          label="Clear Sections"
          icon="mdi:delete-outline"
          @click=${() => {
            clipper.deleteAll();
          }}>
        </bim-button>
        <bim-button
          label="Clear Measurements"
          icon="mdi:eraser"
          @click=${() => {
            lengthMeasurer.list.clear();
            areaMeasurer.list.clear();
          }}>
        </bim-button>
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

// 19. Auto-load from ?url= query parameter only (otherwise start empty)
const urlParam = new URLSearchParams(window.location.search).get("url");
if (urlParam) {
  loadIfcFromUrl(urlParam);
}
