(() => {
  "use strict";

  const nodes = new Map(
    Array.from(document.querySelectorAll("[data-editable-id]")).map((node) => [
      node.dataset.editableId,
      node,
    ])
  );
  const defaults = new Map();
  let state = {
    layers: {}, animations: {}, theme: {}, theme_bindings: {}, data: {},
    layout: {}, locks: {}, revision: 0,
  };
  let currentTimeMs = 0;
  let editMode = false;
  let selectedLayerId = null;
  let drag = null;
  let capabilities = {};
  const overlay = document.createElement("div");
  const resizeHandle = document.createElement("button");
  const rotateHandle = document.createElement("button");
  const guideX = document.createElement("div");
  const guideY = document.createElement("div");

  overlay.setAttribute("aria-hidden", "true");
  Object.assign(overlay.style, {
    position: "fixed", pointerEvents: "none", border: "2px solid #315efb",
    zIndex: "2147483645", display: "none",
  });
  [resizeHandle, rotateHandle].forEach((handle) => Object.assign(handle.style, {
    position: "absolute", width: "14px", height: "14px", padding: "0",
    border: "2px solid white", borderRadius: "50%", background: "#315efb",
    pointerEvents: "auto",
  }));
  Object.assign(resizeHandle.style, { right: "-8px", bottom: "-8px", cursor: "nwse-resize" });
  Object.assign(rotateHandle.style, { left: "calc(50% - 7px)", top: "-28px", cursor: "grab" });
  [guideX, guideY].forEach((guide) => Object.assign(guide.style, {
    position: "fixed", display: "none", background: "#ff3b7f",
    zIndex: "2147483644", pointerEvents: "none",
  }));
  Object.assign(guideX.style, { top: "0", bottom: "0", width: "1px" });
  Object.assign(guideY.style, { left: "0", right: "0", height: "1px" });
  overlay.append(resizeHandle, rotateHandle);
  document.body.append(guideX, guideY, overlay);

  function clone(value) {
    return JSON.parse(JSON.stringify(value));
  }

  function cubicCoordinate(t, p1, p2) {
    const inverse = 1 - t;
    return 3 * inverse * inverse * t * p1 + 3 * inverse * t * t * p2 + t * t * t;
  }

  function easingProgress(progress, easing) {
    const bounded = Math.max(0, Math.min(1, progress));
    const kind = easing?.kind || "linear";
    if (kind === "step") return bounded < 1 ? 0 : 1;
    if (kind === "ease_in") return bounded * bounded * bounded;
    if (kind === "ease_out") return 1 - Math.pow(1 - bounded, 3);
    if (kind === "ease_in_out") {
      return bounded < .5 ? 4 * bounded * bounded * bounded
        : 1 - Math.pow(-2 * bounded + 2, 3) / 2;
    }
    if (kind !== "cubic_bezier") return bounded;
    const x1 = Number(easing.x1 ?? .25);
    const y1 = Number(easing.y1 ?? .1);
    const x2 = Number(easing.x2 ?? .25);
    const y2 = Number(easing.y2 ?? 1);
    let low = 0;
    let high = 1;
    let parameter = bounded;
    for (let index = 0; index < 18; index += 1) {
      parameter = (low + high) / 2;
      const x = cubicCoordinate(parameter, x1, x2);
      if (x < bounded) low = parameter;
      else high = parameter;
    }
    return cubicCoordinate(parameter, y1, y2);
  }

  function animatedValue(track) {
    const keyframes = track?.keyframes || [];
    if (!keyframes.length) return undefined;
    if (currentTimeMs <= keyframes[0].time_ms) return keyframes[0].value;
    const last = keyframes[keyframes.length - 1];
    if (currentTimeMs >= last.time_ms) return last.value;
    for (let index = 0; index < keyframes.length - 1; index += 1) {
      const left = keyframes[index];
      const right = keyframes[index + 1];
      if (currentTimeMs < left.time_ms || currentTimeMs > right.time_ms) continue;
      if (track.interpolation === "discrete") return left.value;
      const duration = Math.max(1, right.time_ms - left.time_ms);
      const progress = easingProgress((currentTimeMs - left.time_ms) / duration, left.easing);
      return Number(left.value) + (Number(right.value) - Number(left.value)) * progress;
    }
    return last.value;
  }

  function effectiveLayer(id) {
    const value = { ...(state.layers[id] || {}) };
    const tracks = state.animations[id] || {};
    Object.entries(tracks).forEach(([field, track]) => {
      const animated = animatedValue(track);
      if (animated !== undefined) value[field] = animated;
    });
    return value;
  }

  function fieldLocked(id, field) {
    return (state.locks[id] || []).includes(field);
  }

  function applyThemeAndData() {
    Object.entries(state.theme_bindings || {}).forEach(([id, cssVariable]) => {
      if (Object.prototype.hasOwnProperty.call(state.theme, id)) {
        document.documentElement.style.setProperty(cssVariable, String(state.theme[id]));
      }
    });
    document.querySelectorAll("[data-editable-data]").forEach((node) => {
      const value = state.data[node.dataset.editableData];
      if (value !== undefined) node.textContent = typeof value === "string" ? value : JSON.stringify(value);
    });
    if (typeof window.editableMediaDataChanged === "function") {
      window.editableMediaDataChanged(clone(state.data));
    }
    if (state.layout?.id) {
      document.documentElement.dataset.editableLayout = state.layout.id;
      document.documentElement.style.setProperty("--editable-canvas-width", String(state.layout.width));
      document.documentElement.style.setProperty("--editable-canvas-height", String(state.layout.height));
      document.documentElement.style.setProperty("--canvas-width", String(state.layout.width));
      document.documentElement.style.setProperty("--canvas-height", String(state.layout.height));
    }
  }

  function captureDefaults() {
    nodes.forEach((node, id) => {
      const rect = node.getBoundingClientRect();
      const style = getComputedStyle(node);
      defaults.set(id, {
        content: node.textContent,
        image: node instanceof HTMLImageElement ? node.getAttribute("src") : null,
        color: style.color,
        fontFamily: style.fontFamily,
        fontSize: style.fontSize,
        opacity: style.opacity,
        zIndex: style.zIndex,
        display: style.display,
        visibility: style.visibility,
        rect: { x: rect.x, y: rect.y, width: rect.width, height: rect.height },
      });
    });
  }

  function applyLayer(id) {
    const node = nodes.get(id);
    const base = defaults.get(id);
    if (!node || !base) return;
    const value = effectiveLayer(id);
    if (Object.prototype.hasOwnProperty.call(value, "content")) {
      node.textContent = value.content ?? base.content;
    } else if (node.children.length === 0 && !(node instanceof HTMLImageElement)) {
      node.textContent = base.content;
    }
    if (node instanceof HTMLImageElement) node.src = value.image ?? base.image ?? "";
    node.style.color = value.color ?? base.color;
    node.style.fontFamily = value.font_family ?? base.fontFamily;
    node.style.fontSize = value.font_size == null ? base.fontSize : `${value.font_size}px`;
    node.style.width = value.width == null ? "" : `${value.width}px`;
    node.style.height = value.height == null ? "" : `${value.height}px`;
    node.style.translate = `${(value.x ?? base.rect.x) - base.rect.x}px ${(value.y ?? base.rect.y) - base.rect.y}px`;
    node.style.rotate = value.rotation == null ? "" : `${value.rotation}deg`;
    node.style.opacity = String(value.opacity ?? base.opacity);
    node.style.zIndex = value.z_index == null ? base.zIndex : String(value.z_index);
    const insideTime = (value.enter_ms == null || currentTimeMs >= value.enter_ms)
      && (value.exit_ms == null || currentTimeMs <= value.exit_ms);
    node.style.visibility = (value.visible ?? true) && insideTime ? base.visibility : "hidden";
    node.style.setProperty("--editable-delay-ms", String(value.delay_ms ?? 0));
    node.style.setProperty("--editable-duration-ms", String(value.duration_ms ?? 0));
    node.toggleAttribute("data-editable-selected", selectedLayerId === id);
    if (selectedLayerId === id) updateOverlay();
  }

  function applyState() {
    applyThemeAndData();
    nodes.forEach((_node, id) => applyLayer(id));
  }

  function getState() {
    return clone(state);
  }

  function setState(nextState) {
    state = {
      layers: clone(nextState?.layers || {}),
      animations: clone(nextState?.animations || {}),
      theme: clone(nextState?.theme || {}),
      theme_bindings: clone(nextState?.theme_bindings || {}),
      data: clone(nextState?.data || {}),
      layout: clone(nextState?.layout || {}),
      locks: clone(nextState?.locks || {}),
      revision: Number(nextState?.revision || 0),
    };
    applyState();
    return getState();
  }

  function setTime(milliseconds) {
    currentTimeMs = Math.max(0, Number(milliseconds) || 0);
    document.documentElement.style.setProperty("--editable-media-time-ms", String(currentTimeMs));
    if (typeof window.editableMediaRenderTime === "function") {
      window.editableMediaRenderTime(currentTimeMs);
    }
    applyState();
    return currentTimeMs;
  }

  function getBounds() {
    return Object.fromEntries(
      Array.from(nodes, ([id, node]) => {
        const rect = node.getBoundingClientRect();
        return [id, {
          x: rect.x,
          y: rect.y,
          width: rect.width,
          height: rect.height,
          rotation: Number(effectiveLayer(id).rotation || 0),
        }];
      })
    );
  }

  function emit(name, detail) {
    window.dispatchEvent(new CustomEvent(name, { detail: clone(detail) }));
  }

  function updateOverlay() {
    if (!editMode || !selectedLayerId || !nodes.has(selectedLayerId)) {
      overlay.style.display = "none";
      return;
    }
    const rect = nodes.get(selectedLayerId).getBoundingClientRect();
    Object.assign(overlay.style, {
      display: "block", left: `${rect.x}px`, top: `${rect.y}px`,
      width: `${rect.width}px`, height: `${rect.height}px`,
      transform: `rotate(${Number(effectiveLayer(selectedLayerId).rotation || 0)}deg)`,
    });
    const fields = capabilities[selectedLayerId] || [];
    resizeHandle.style.display = fields.includes("width") && fields.includes("height") ? "block" : "none";
    rotateHandle.style.display = fields.includes("rotation") ? "block" : "none";
  }

  function snapMove(x, y, width, height) {
    const tolerance = 6;
    const xTargets = [0, innerWidth / 2, innerWidth];
    const yTargets = [0, innerHeight / 2, innerHeight];
    const xPoints = [x, x + width / 2, x + width];
    const yPoints = [y, y + height / 2, y + height];
    guideX.style.display = "none";
    guideY.style.display = "none";
    for (let pointIndex = 0; pointIndex < xPoints.length; pointIndex += 1) {
      const target = xTargets.find((candidate) => Math.abs(candidate - xPoints[pointIndex]) <= tolerance);
      if (target !== undefined) {
        x += target - xPoints[pointIndex];
        guideX.style.left = `${target}px`;
        guideX.style.display = "block";
        break;
      }
    }
    for (let pointIndex = 0; pointIndex < yPoints.length; pointIndex += 1) {
      const target = yTargets.find((candidate) => Math.abs(candidate - yPoints[pointIndex]) <= tolerance);
      if (target !== undefined) {
        y += target - yPoints[pointIndex];
        guideY.style.top = `${target}px`;
        guideY.style.display = "block";
        break;
      }
    }
    return { x, y };
  }

  function selectLayer(id) {
    selectedLayerId = nodes.has(id) ? id : null;
    applyState();
    emit("editablemediaselection", { layerId: selectedLayerId });
  }

  function setEditMode(enabled) {
    editMode = Boolean(enabled);
    document.documentElement.toggleAttribute("data-editable-mode", editMode);
    updateOverlay();
    return editMode;
  }

  function setEditCapabilities(value) {
    capabilities = clone(value || {});
    updateOverlay();
  }

  resizeHandle.addEventListener("pointerdown", (event) => {
    if (!selectedLayerId || fieldLocked(selectedLayerId, "width")
      || fieldLocked(selectedLayerId, "height")) return;
    const fields = capabilities[selectedLayerId] || [];
    if (!fields.includes("width") || !fields.includes("height")) return;
    const bounds = getBounds()[selectedLayerId];
    drag = {
      type: "resize", id: selectedLayerId, startX: event.clientX, startY: event.clientY,
      width: bounds.width, height: bounds.height,
    };
    resizeHandle.setPointerCapture(event.pointerId);
    event.stopPropagation();
    event.preventDefault();
  });

  rotateHandle.addEventListener("pointerdown", (event) => {
    if (!selectedLayerId || fieldLocked(selectedLayerId, "rotation")) return;
    if (!(capabilities[selectedLayerId] || []).includes("rotation")) return;
    const bounds = getBounds()[selectedLayerId];
    const centerX = bounds.x + bounds.width / 2;
    const centerY = bounds.y + bounds.height / 2;
    drag = {
      type: "rotate", id: selectedLayerId, centerX, centerY,
      startAngle: Math.atan2(event.clientY - centerY, event.clientX - centerX),
      rotation: Number(state.layers[selectedLayerId]?.rotation || 0),
    };
    rotateHandle.setPointerCapture(event.pointerId);
    event.stopPropagation();
    event.preventDefault();
  });

  document.addEventListener("pointerdown", (event) => {
    if (!editMode) return;
    const node = event.target.closest("[data-editable-id]");
    if (!node) return;
    const id = node.dataset.editableId;
    selectLayer(id);
    if (fieldLocked(id, "x") || fieldLocked(id, "y")) return;
    const fields = capabilities[id] || [];
    if (!fields.includes("x") || !fields.includes("y")) return;
    const bounds = getBounds()[id];
    drag = {
      type: "move", id, startX: event.clientX, startY: event.clientY,
      x: bounds.x, y: bounds.y, width: bounds.width, height: bounds.height,
    };
    node.setPointerCapture(event.pointerId);
    event.preventDefault();
  });

  document.addEventListener("pointermove", (event) => {
    if (!drag) return;
    const layer = { ...(state.layers[drag.id] || {}) };
    if (drag.type === "move") {
      const snapped = snapMove(
        drag.x + event.clientX - drag.startX,
        drag.y + event.clientY - drag.startY,
        drag.width,
        drag.height
      );
      layer.x = snapped.x;
      layer.y = snapped.y;
    } else if (drag.type === "resize") {
      layer.width = Math.max(8, drag.width + event.clientX - drag.startX);
      layer.height = Math.max(8, drag.height + event.clientY - drag.startY);
    } else if (drag.type === "rotate") {
      const angle = Math.atan2(event.clientY - drag.centerY, event.clientX - drag.centerX);
      layer.rotation = drag.rotation + (angle - drag.startAngle) * 180 / Math.PI;
    }
    state.layers[drag.id] = layer;
    applyLayer(drag.id);
    emit("editablemediapreviewchange", { layerId: drag.id, state: getState() });
  });

  document.addEventListener("pointerup", () => {
    if (!drag) return;
    const layerId = drag.id;
    drag = null;
    guideX.style.display = "none";
    guideY.style.display = "none";
    emit("editablemediachange", { layerId, state: getState() });
  });

  const ready = Promise.all([
    document.fonts.ready,
    Promise.all(Array.from(document.images).map((image) => image.decode())),
  ]).then(() => {
    captureDefaults();
    applyState();
    return true;
  });

  window.editableMedia = Object.freeze({
    ready,
    getState,
    setState,
    setTime,
    getBounds,
    setEditMode,
    setEditCapabilities,
    selectLayer,
  });
})();
