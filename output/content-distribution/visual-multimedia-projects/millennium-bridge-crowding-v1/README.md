# 千禧桥与拥挤交易｜动效样稿

这是 1080×1350 的网页动效样稿。12 秒无声 H.264 预览位于 `preview/millennium-bridge-crowding-motion-sample.mp4`，初版短旁白位于 `preview/millennium-bridge-crowding-motion-sample-with-voice.mp4`。完整解释版位于 `preview/millennium-bridge-crowding-extended-with-voice.mp4`：它保留自然语速的 67 秒 EdgeTTS 旁白，并循环使用同一段网页动画，最终时长 68.33 秒。

打开 `index.html` 可以播放、暂停、重置或拖动时间轴。追加 `?capture=1&time=6000` 可以在指定毫秒隐藏控制栏并捕获画布。

内容、口播和 EdgeTTS 参数集中在 `project-data.js`，视觉规则集中在 `style-profile.json` 和 `styles.css`，确定性动画集中在 `animation.js`，结构化编辑能力由 `editable-media.json` 声明。`render-preview.js` 从同一个网页捕获关键状态或逐帧画面，`build-audio.js` 生成旁白并装配现有视频；后续修改仍从这些真源重新生成，不直接修改派生成品。
