window.MEDIA_PROJECT = Object.freeze({
  output: {
    width: 1080,
    height: 1350,
    durationMs: 12000,
    fps: 30,
    loop: false
  },
  content: {
    kicker: "MIT · PORTFOLIO MANAGEMENT",
    titleLine1: "每个人都在自救",
    titleLine2: "系统为什么反而失控？",
    subtitle: "千禧桥、节拍器与拥挤交易",
    phaseLabels: ["各走各的", "共同反馈", "逐渐同步"],
    captions: [
      "行人原本各走各的",
      "桥一晃，每个人都在调整脚步",
      "共同底座，把独立个体连接起来",
      "没有人发号施令，节奏仍会同步"
    ],
    closing: "相同的反应规则，会把彼此连成一个系统",
    source: "MIT 18.S096 · Lecture 16 · Portfolio Management"
  },
  narration: {
    full: "每个人都在做合理的事，为什么整个系统还会失控？伦敦千禧桥开放初期，行人原本各走各的。桥面出现轻微横向晃动后，每个人都会下意识调整脚步，让自己站稳。单看任何一个人，这个动作都很合理。可所有人都通过同一座桥连在一起：大家同时调整，桥晃得更厉害；桥越晃，大家越需要调整。节拍器也是这样。放在固定桌面上，它们各敲各的；换成能够移动的共同底座，它们会慢慢同步。它们没有意识，只是在通过底座互相影响。市场里的共同底座，可能是相似的风控模型、止损线和杠杆约束。价格一跌，很多人同时卖出；卖出又推动价格继续下跌。所以，拥挤交易不只发生在大家买了同一只股票时。只要很多人使用相同的应对规则，他们就已经连在一起。检查自己的组合时，可以多问一句：我和谁，踩在同一块会晃的底板上？",
    sampleVoiceover: "为什么一群互不认识的人，会突然做出同一个动作？伦敦千禧桥开放初期，行人原本各走各的。桥面出现轻微横向晃动后，每个人都会本能地调整脚步，让自己站稳。单看一个人，这个动作完全合理。可所有人都踩在同一座桥上：大家同时调整，桥晃得更厉害；桥越晃，大家越需要继续调整。节拍器也会出现类似现象。放在固定桌面上，它们各敲各的；放到能够移动的共同底座上，它们会慢慢同步。没有人发号施令，是底座的反馈把它们连接了起来。市场里的共同底座，可能是相似的风控模型、止损线和杠杆约束。价格一跌，许多人同时卖出；卖出又让价格继续下跌，于是更多人被迫卖出。拥挤交易并不只发生在大家买了同一只股票时。只要许多人使用相同的应对规则，他们就已经连在了一起。检查自己的组合时，可以多问一句：如果市场突然波动，我的下一步，会不会也是所有人的下一步？",
    sampleScope: "桥面晃动、行人调整、共同底座转为节拍器"
  },
  audio: {
    provider: "EdgeTTS",
    voice: "zh-CN-YunxiNeural",
    rate: "+5%",
    volume: "+0%",
    pitch: "-2Hz",
    startDelayMs: 350,
    targetVoiceDurationMs: 0
  },
  sources: [
    {
      label: "Bilibili P14 约 1:06:00–1:10:30",
      url: "https://www.bilibili.com/video/BV15SDxYAEvB/?p=14&t=3960"
    },
    {
      label: "MIT OpenCourseWare Lecture 16 transcript",
      url: "https://ocw.mit.edu/courses/18-s096-topics-in-mathematics-with-applications-in-finance-fall-2013/2aa2fec3d040b7d3746ca7ba5c192041_8TJQhQ2GZ0Y.pdf"
    }
  ]
});
