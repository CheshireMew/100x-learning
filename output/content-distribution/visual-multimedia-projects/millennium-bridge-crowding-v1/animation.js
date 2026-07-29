(() => {
  "use strict";

  const PROJECT = window.MEDIA_PROJECT;
  const root = document.documentElement;
  const canvasShell = document.querySelector("#canvasShell");
  const viewport = document.querySelector("#viewport");
  const scrubber = document.querySelector("#scrubber");
  const timeOutput = document.querySelector("#time");
  const captionText = document.querySelector("#captionText");
  const captionIndex = document.querySelector("#captionIndex");
  const captionCard = document.querySelector(".caption-card");
  const phaseProgress = document.querySelector("#phaseProgress");
  const phaseLabels = document.querySelector("#phaseLabels");
  const bridgeContext = document.querySelector("#bridgeContext");
  const feedbackWaves = document.querySelector("#feedbackWaves");
  const sharedBase = document.querySelector("#sharedBase");
  const walkersGroup = document.querySelector("#walkers");
  const walkers = Array.from(document.querySelectorAll(".walker"));
  const metronomesGroup = document.querySelector("#metronomes");
  const metronomes = Array.from(document.querySelectorAll(".metronome"));
  const connectionTag = document.querySelector("#connectionTag");
  const closing = document.querySelector("#closing");

  const query = new URLSearchParams(location.search);
  const captureMode = query.get("capture") === "1";
  const requestedTimeMs = Number(query.get("time") || 0);

  root.style.setProperty("--canvas-width", PROJECT.output.width);
  root.style.setProperty("--canvas-height", PROJECT.output.height);
  document.querySelectorAll("[data-field]").forEach((node) => {
    const key = node.dataset.field;
    if (Object.prototype.hasOwnProperty.call(PROJECT.content, key)) {
      node.textContent = PROJECT.content[key];
    }
  });
  phaseLabels.replaceChildren(...PROJECT.content.phaseLabels.map((label) => {
    const node = document.createElement("span");
    node.textContent = label;
    return node;
  }));

  if (captureMode) document.body.classList.add("capture");
  scrubber.max = String(PROJECT.output.durationMs);

  let currentMs = 0;
  let playing = false;
  let startedAt = 0;
  let animationFrame = 0;

  const clamp = (value, minimum = 0, maximum = 1) => Math.max(minimum, Math.min(maximum, value));
  const range = (time, start, end) => clamp((time - start) / Math.max(1, end - start));
  const smooth = (value) => {
    const t = clamp(value);
    return t * t * (3 - 2 * t);
  };
  const easeOut = (value) => 1 - Math.pow(1 - clamp(value), 3);
  const quantize = (value, steps = 9) => Math.round(value * steps) / steps;
  const mix = (left, right, amount) => left + (right - left) * clamp(amount);

  function currentCaption(time) {
    if (time < 2600) return 0;
    if (time < 5600) return 1;
    if (time < 9000) return 2;
    return 3;
  }

  function setCaption(time) {
    const index = currentCaption(time);
    captionText.textContent = PROJECT.content.captions[index];
    captionIndex.textContent = String(index + 1).padStart(2, "0");
    const localStart = [0, 2600, 5600, 9000][index];
    const cardReveal = easeOut(range(time, localStart, localStart + 280));
    captionCard.style.opacity = String(time >= 10850 ? 1 - smooth(range(time, 10850, 11450)) : cardReveal);
    captionCard.style.transform = `translateY(${quantize((1 - cardReveal) * 16, 6)}px) rotate(${index % 2 ? -.18 : .12}deg)`;
  }

  function setHeader(time) {
    document.querySelector(".masthead").style.opacity = "1";
    document.querySelector(".masthead").style.transform = "translateY(0)";
  }

  function setBridge(time) {
    const entrance = easeOut(range(time, 300, 1500));
    const feedback = smooth(range(time, 2800, 6200));
    const transform = smooth(range(time, 6900, 8500));
    const bridgeOpacity = 1 - smooth(range(time, 7000, 8200));
    const swayAmplitude = mix(3, 23, feedback) * (1 - transform * .45);
    const sway = quantize(Math.sin(time / 260) * swayAmplitude, 6);
    const lift = quantize((1 - entrance) * 48, 8);

    bridgeContext.style.opacity = String(entrance * bridgeOpacity);
    bridgeContext.style.transform = `translateY(${lift}px)`;
    sharedBase.style.opacity = String(entrance);
    sharedBase.style.transform = `translate(${sway}px, ${quantize(lift + transform * 64, 8)}px)`;
    feedbackWaves.style.opacity = String(feedback * (1 - transform));
    feedbackWaves.style.transform = `translateX(${sway * .65}px)`;

    walkersGroup.style.opacity = String(entrance * (1 - smooth(range(time, 7100, 8200))));
    walkers.forEach((walker, index) => {
      const baseX = [150, 282, 416, 555, 692, 830][index];
      const independentPhase = index * 1.12 + .35;
      const commonPhase = time / 285;
      const phase = mix(time / 340 + independentPhase, commonPhase, feedback);
      const step = quantize(Math.sin(phase) * 7, 5);
      const lean = quantize(Math.sin(phase) * mix(7, 12, feedback) + sway * .22, 5);
      walker.setAttribute("transform", `translate(${baseX + sway} ${385 + lift + transform * 64 + step}) rotate(${lean})`);
      const legs = walker.querySelectorAll(".leg-a, .leg-b");
      legs[0].style.transform = `rotate(${quantize(Math.sin(phase) * 15, 5)}deg)`;
      legs[1].style.transform = `rotate(${quantize(-Math.sin(phase) * 15, 5)}deg)`;
      legs.forEach((leg) => { leg.style.transformOrigin = "0px 13px"; });
    });
  }

  function setMetronomes(time) {
    const reveal = easeOut(range(time, 7350, 8750));
    const sync = smooth(range(time, 9000, 11700));
    const baseSway = quantize(Math.sin(time / 260) * mix(11, 18, sync), 6);
    metronomesGroup.style.opacity = String(reveal);
    metronomesGroup.style.transform = `translate(${baseSway * .42}px, ${quantize((1 - reveal) * 48 + 64, 7)}px)`;

    metronomes.forEach((metronome, index) => {
      const independentPhase = index * 1.31 + .5;
      const commonPhase = time / 255;
      const phase = mix(time / 300 + independentPhase, commonPhase, sync);
      const angle = quantize(Math.sin(phase) * 24, 6);
      const pendulum = metronome.querySelector(".pendulum");
      pendulum.style.transformOrigin = "0px 8px";
      pendulum.style.transform = `rotate(${angle}deg)`;
      metronome.style.transformOrigin = "center bottom";
      metronome.style.scale = String(.88 + reveal * .12);
    });

    connectionTag.style.opacity = String(smooth(range(time, 8150, 9000)));
    connectionTag.style.transform = `translateY(${quantize((1 - reveal) * 18, 6)}px)`;
  }

  function setClosing(time) {
    const reveal = smooth(range(time, 11050, 11750));
    closing.textContent = PROJECT.content.closing;
    closing.style.opacity = String(reveal);
    closing.style.transform = `translateY(${quantize((1 - reveal) * 18, 6)}px)`;
    const labels = Array.from(phaseLabels.children);
    const phase = time < 4000 ? 0 : time < 8200 ? 1 : 2;
    labels.forEach((label, index) => label.classList.toggle("active", index === phase));
  }

  function setTime(milliseconds) {
    currentMs = clamp(Number(milliseconds) || 0, 0, PROJECT.output.durationMs);
    const progress = currentMs / PROJECT.output.durationMs;
    setHeader(currentMs);
    setBridge(currentMs);
    setMetronomes(currentMs);
    setCaption(currentMs);
    setClosing(currentMs);
    phaseProgress.style.width = `${(progress * 100).toFixed(4)}%`;
    scrubber.value = String(Math.round(currentMs));
    timeOutput.value = `${(currentMs / 1000).toFixed(2)} s`;
  }

  function frame(now) {
    if (!playing) return;
    const elapsed = now - startedAt;
    if (elapsed >= PROJECT.output.durationMs) {
      setTime(PROJECT.output.durationMs);
      playing = false;
      return;
    }
    setTime(elapsed);
    animationFrame = requestAnimationFrame(frame);
  }

  function play() {
    if (playing) return;
    if (currentMs >= PROJECT.output.durationMs) currentMs = 0;
    playing = true;
    startedAt = performance.now() - currentMs;
    animationFrame = requestAnimationFrame(frame);
  }

  function pause() {
    playing = false;
    cancelAnimationFrame(animationFrame);
  }

  function reset() {
    pause();
    setTime(0);
  }

  function fitCanvas() {
    if (captureMode) return;
    const scale = Math.min(
      viewport.clientWidth / PROJECT.output.width,
      viewport.clientHeight / PROJECT.output.height,
      1
    );
    canvasShell.style.transform = `scale(${Math.max(scale, .1)})`;
  }

  document.querySelector("#play").addEventListener("click", play);
  document.querySelector("#pause").addEventListener("click", pause);
  document.querySelector("#reset").addEventListener("click", reset);
  scrubber.addEventListener("input", (event) => {
    pause();
    setTime(event.target.value);
  });

  new ResizeObserver(fitCanvas).observe(viewport);
  window.addEventListener("resize", fitCanvas);
  window.editableMediaRenderTime = setTime;
  window.editableMediaDataChanged = () => {};
  setTime(requestedTimeMs);
  fitCanvas();
})();
