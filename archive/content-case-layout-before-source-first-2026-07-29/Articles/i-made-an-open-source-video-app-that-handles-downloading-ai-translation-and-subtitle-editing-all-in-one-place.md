---
authorship: "本人主导"
reference_value: "case"
content_type: "项目与产品介绍"
source_url: "https://blog.blacknico.com/guide/i-made-an-open-source-video-app-that-handles-downloading-ai-translation-and-subtitle-editing-all-in-one-place/"
writing_task: "发布开源工具并复盘开发教训"
topics: ["开源视频工具", "字幕工作流", "产品开发"]
structure: ["碎片化工作流痛点", "现有工具缺口", "功能逐项展示", "过度开发与架构教训"]
---

# 我做了一款集下载、AI 翻译、编辑字幕于一体的开源视频神器！

小伙伴们有没有好奇我最近在做什么呢？

作为一个内容创作者，少不了和视频打交道，无论你只是单纯的搬运、整理文稿还是想给自己的视频加上字幕，都没有一款工具能彻底解决所有问题。

[卡卡字幕助手（VideoCaptioner）](https://github.com/WEIFENG2333/VideoCaptioner)应该是目前最完善的工具了，集下载、AI 翻译、视频合成于一体。但是！它还是没有像 SubtitleEdit 一样的字幕校对和编辑功能，并且下载功能一直抽风。

![image](https://blog.blacknico.com/wp-content/uploads/2026/03/image-19-1024x365.png "我做了一款集下载、AI 翻译、编辑字幕于一体的开源视频神器！")

于是我想要给一个没有字幕的视频加上字幕，就需要先打开[cobalt](https://cobalt.tools/) 下载视频，卡卡字幕助手转录字幕和翻译，SubtitleEdit 编辑字幕，最后打开 Adobe Premiere 合成视频。

何等的麻烦！

是可忍熟不可忍！

于是 AI 的大手发力了！我用一个月时间做出来这款集下载、AI 翻译、编辑字幕于一体的开源视频神器 [MediaFlow](https://github.com/CheshireMew/MediaFlow)！

![image](https://blog.blacknico.com/wp-content/uploads/2026/03/image-20-1024x626.png "我做了一款集下载、AI 翻译、编辑字幕于一体的开源视频神器！")

下面就由我来向大家一一介绍它的功能。

### 功能介绍

##### 1. 视频下载

下载视频功能使用的 [yt-dlp](https://github.com/yt-dlp/yt-dlp)，支持互联网上绝大多数视频网站，包括 X（Twitter）、Youtube、Bilibili、小红书等。

我还特地为抖音和快手等 yt-dlp 不支持的网站做了适配，包括 Cookie 管理等，费了很大的功夫。实际上我并不需要这些网站的视频，但为了大而全还是做了，后续也拖了不少后腿，只能说是个教训了，应该优先做自己真正有需求的功能。

![image](https://blog.blacknico.com/wp-content/uploads/2026/03/image-21-1024x683.png "我做了一款集下载、AI 翻译、编辑字幕于一体的开源视频神器！")

##### 2. 转录字幕

这方面用的最流行的 Fast Whisper 模型，一开始用的做了 Python 内置引擎，但它的断句有一些问题。于是又下载了 CLI 版本，CLI 可以传递参数，经过不停地调整终于能输出较好的字幕，改了一次又一次，真不容易。

但还有一个潜在的问题，一句话可能过长，因此我加了一个“智能分割”按钮，可以自动分割过长的字幕。

![image](https://blog.blacknico.com/wp-content/uploads/2026/03/image-22-1024x683.png "我做了一款集下载、AI 翻译、编辑字幕于一体的开源视频神器！")

##### 3. AI 翻译

Deepseek 的 API 最便宜，推荐使用这个，并且效果也不错。

需要在“设置”里选择并填写密钥，在  [官方网站](https://platform.deepseek.com/sign_in)  购买就行了，一块钱能用好几天！

![image](https://blog.blacknico.com/wp-content/uploads/2026/03/image-23-1024x683.png "我做了一款集下载、AI 翻译、编辑字幕于一体的开源视频神器！")

##### 4. 字幕编辑

这部分是最重的功能，简单来说，你可以在”编辑选中项“里修改字幕具体的内容，在音频波形图里拖动字幕时间长短。

![image](https://blog.blacknico.com/wp-content/uploads/2026/03/image-24-1024x683.png "我做了一款集下载、AI 翻译、编辑字幕于一体的开源视频神器！")

鼠标右键还有更多丰富的功能，比如说识别某段之前没有被转录的音频、智能分割等等。

如果你不是一个完美主义者，也许前三个功能就已经能满足你了。但如果你希望字幕正确且没有瑕疵，这部分功能最重要。

修改完字幕后，就可以点击上面的按钮进行视频合成了。

##### 5. 视频合成

视频合成界面可以调整字幕的各项参数，以及最重要的，添加水印。

![image](https://blog.blacknico.com/wp-content/uploads/2026/03/image-25-1024x683.png "我做了一款集下载、AI 翻译、编辑字幕于一体的开源视频神器！")

到这里，整个功能就完善了。

我原本还想加入 AI 画质高清、视频去水印、OCR 字幕识别等功能，但这些功能不仅使用率低、依赖库庞大，并且没几个人的电脑能跑得动，也就搁置了。

![image](https://blog.blacknico.com/wp-content/uploads/2026/03/image-26-1024x683.png "我做了一款集下载、AI 翻译、编辑字幕于一体的开源视频神器！")

最后，这个项目的桌面版正在打包中，我还得花几天确认正式版没有任何 bug，相信不久就会上线了。

如果你愿意做小白鼠的话，可以直接  [下载源码](https://github.com/CheshireMew/MediaFlow)  打包或者加群试试，哈哈。

### 苦涩的教训：

从 Vibe Coding 的角度来讲，这个项目可以说是失败的，虽然对于我个人使用上来说是成功的。

如果让我再做一次这个项目，我不会再使用 Electron 做前端界面，而是直接使用 Python 做界面。

前后端架构让打包时遇到了巨大的困难，以至于我不得不一遍又一遍地重构。

更糟糕的是 Codex 为了兼容旧架构写了无数的屎山代码，简直是折磨。如果你在使用 Codex 重构，一定要让它强制迁移。

![image](https://blog.blacknico.com/wp-content/uploads/2026/03/image-27-1024x701.png "我做了一款集下载、AI 翻译、编辑字幕于一体的开源视频神器！")

给予 AI 信赖，但也不要被 AI 牵着鼻子走。

未来做项目时，都得先思考一个问题：前端 or 后端？

<!-- content-case-notes -->

## 可以参考什么

参考它用原来必须打开四个工具的麻烦证明产品需求，再按真实使用顺序展示功能。每项功能都穿插为什么这样做和哪里做过头了，发布文因此同时具备产品说明与开发复盘。

## 适用场景

适合功能较多的自制工具发布，以及需要公开取舍和失败教训的项目复盘。
