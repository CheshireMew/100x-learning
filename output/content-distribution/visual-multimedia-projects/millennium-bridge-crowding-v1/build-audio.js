const { spawnSync } = require("child_process");
const fs = require("fs");
const path = require("path");

global.window = {};
require("./project-data.js");
const PROJECT = global.window.MEDIA_PROJECT;

const projectDir = __dirname;
const audioDir = path.join(projectDir, "audio");
const previewDir = path.join(projectDir, "preview");
const edgeTts = "D:\\Tools\\Python310\\Scripts\\edge-tts.exe";
const ffmpeg = "D:\\Code\\MediaFlow\\bin\\ffmpeg.exe";
const ffprobe = "D:\\Code\\MediaFlow\\bin\\ffprobe.exe";
const rawVoice = path.join(audioDir, "voice-extended-edge-tts.mp3");
const subtitles = path.join(audioDir, "voice-extended-edge-tts.vtt");
const inputVideo = path.join(previewDir, "millennium-bridge-crowding-motion-sample.mp4");
const outputVideo = path.join(previewDir, "millennium-bridge-crowding-extended-with-voice.mp4");

function run(command, args, label) {
  const result = spawnSync(command, args, { encoding: "utf8" });
  if (result.status !== 0) {
    process.stderr.write(`${label} failed\n${result.stdout || ""}${result.stderr || ""}`);
    process.exit(result.status || 1);
  }
  return result.stdout.trim();
}

function probeDuration(file) {
  return Number(run(ffprobe, [
    "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", file
  ], "ffprobe"));
}

fs.mkdirSync(audioDir, { recursive: true });

run(edgeTts, [
  "--text", PROJECT.narration.sampleVoiceover,
  "--voice", PROJECT.audio.voice,
  `--rate=${PROJECT.audio.rate}`,
  `--volume=${PROJECT.audio.volume}`,
  `--pitch=${PROJECT.audio.pitch}`,
  "--write-media", rawVoice,
  "--write-subtitles", subtitles
], "EdgeTTS");

const rawDuration = probeDuration(rawVoice);
const targetSeconds = PROJECT.audio.targetVoiceDurationMs / 1000;
const tempo = targetSeconds > 0
  ? Math.max(.82, Math.min(1.35, rawDuration / targetSeconds))
  : 1;
const delay = Math.max(0, Math.round(PROJECT.audio.startDelayMs));
const adjustedVoiceDuration = rawDuration / tempo;
const finalDuration = Math.ceil((delay / 1000 + adjustedVoiceDuration + .55) * PROJECT.output.fps) / PROJECT.output.fps;
const fadeOutStart = Math.max(.1, finalDuration - .45);

run(ffmpeg, [
  "-hide_banner", "-loglevel", "error", "-y",
  "-stream_loop", "-1", "-i", inputVideo,
  "-i", rawVoice,
  "-filter_complex",
  `[1:a]atempo=${tempo.toFixed(6)},loudnorm=I=-16:TP=-1.5:LRA=11,adelay=${delay}|${delay},apad,atrim=0:${finalDuration.toFixed(6)},afade=t=in:st=${(delay / 1000).toFixed(3)}:d=0.12,afade=t=out:st=${fadeOutStart.toFixed(3)}:d=0.4[a]`,
  "-map", "0:v:0", "-map", "[a]",
  "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
  "-t", finalDuration.toFixed(6), "-movflags", "+faststart",
  outputVideo
], "audio mux");

const actualFinalDuration = probeDuration(outputVideo);
process.stdout.write(JSON.stringify({
  provider: PROJECT.audio.provider,
  voice: PROJECT.audio.voice,
  text: PROJECT.narration.sampleVoiceover,
  rawVoiceDurationSeconds: Number(rawDuration.toFixed(3)),
  tempo: Number(tempo.toFixed(6)),
  visualLoopDurationSeconds: Number(probeDuration(inputVideo).toFixed(3)),
  finalVideoDurationSeconds: Number(actualFinalDuration.toFixed(3)),
  outputVideo
}, null, 2));
