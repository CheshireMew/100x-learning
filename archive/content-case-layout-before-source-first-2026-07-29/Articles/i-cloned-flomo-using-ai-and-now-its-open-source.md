---
authorship: "本人主导"
reference_value: "case"
content_type: "项目与产品介绍"
source_url: "https://blog.blacknico.com/ai/i-cloned-flomo-using-ai-and-now-its-open-source/"
writing_task: "介绍自制产品并复盘开发取舍"
topics: ["开源笔记", "Vibe Coding", "产品取舍"]
structure: ["现成方案为何不够", "产品入口与差异", "架构踩坑", "功能取舍与诚实结论"]
---

# 我用 AI “抄袭”了 flomo，并且 —— 开源了！

首先叠个甲：我非常喜欢 [flomo](https://flomoapp.com/) 这款产品和它的理念。但是大家都懂的，对于我们这种人来说，总有些个人和隐私的需求，数据不在自己手里总归是不放心。

也有人会说，不是有 [memos](https://github.com/usememos/memos) 和它的安卓移动端 [memoflow](https://github.com/hzc073/memoflow)这样优秀的开源笔记项目了吗？直接部署不就好了。

正如我放弃 flomo 的原因一样，别人做的产品始终是不满足自己个性化的需求的，如果在这个基础上进行改动又要费很多时间，那不如从头开始重做了。

重复造轮子也是一种乐趣。

![FireShot Capture 1715 - Bemo Notes - [localhost]](https://blog.blacknico.com/wp-content/uploads/2026/03/FireShot-Capture-1715-Bemo-Notes-localhost-1024x404.png "我用 AI“抄袭”了 flomo，并且 —— 开源了！")

我本身并不是程序员，这也是积累项目经验的好方法。

那么首先，开源仓库在这里：[Bemo](https://github.com/CheshireMew/Bemo)。

为了和 flomo 区分开来，我还特地做了另外两款主题：

![image](https://blog.blacknico.com/wp-content/uploads/2026/03/image-30-1024x603.png "我用 AI“抄袭”了 flomo，并且 —— 开源了！")

产品本身没什么好说的，就是一个普通的笔记，说一说开发过程遇到的坑和教训吧！

---

我是想做一个多端互通的笔记软件，也就是有桌面端、网页端和移动端。于是 AI 给的方案是这样：

桌面端和移动端共用同一套前端页面：Vue 3 + Vite + TypeScript，桌面端用的是 Tauri 2，也就是前端页面加一个 Rust 壳，移动端是 Capacitor 8 + Android Gradle。

但是不知道 AI 为什么一上来就给我做了一个 python 后端，所以一开始这个项目是前后端混合的，直到打包时才发现，后端没法打包进 Apk 啊！

于是只有进行重构，把所有功能，除了同步功能，都迁移到了前端。

所以还是上篇文章提到的问题：着重于前端 or 后端？最好倾向于一方，不然打包时就是地狱。

不过现在又遇到一个问题，前端无法持久化存储数据，容易丢失，好像后端依旧是必要的。

我最近也反思，笔记这个软件要多端互通确实要打包，但是其它的开源项目为什么要打包呢？所以，想让别人也能正常使用我的开源项目这种想法，实际上拖累了我。都有 AI 了，每个人自己把开源代码下下来改改就能跑了，我没必要为了别人而做适配。

OpenClaw 那么放飞自我、那么难安装的项目大家都趋之若鹜，说明问题根本不在使用门槛上，而在于是否真正解决了痛点。

---

AI 功能可能是这个软件的一大特色。

你可以选择一条或者一段时间内的笔记与 AI 进行对话复盘或者提取灵感，这也是我想做这个软件最大的初衷。

![image](https://blog.blacknico.com/wp-content/uploads/2026/03/image-28-1024x881.png "我用 AI“抄袭”了 flomo，并且 —— 开源了！")

---

软件做好了，接下来最大的问题就是三端同步。

我原本是想如果部署到服务器，那就可以直接用网页访问，并且数据也都是在服务器上也就没有同步问题。但不是所有人都有一台云服务器，这时我又看到一个叫“Bilibili 无限历史记录”的浏览器插件，它使用的是坚果云，实现了一下还不错。

不过坚果云会限流，一下子传太多笔记的话就得等一段时间，但总体来说还是可用的。

![image](https://blog.blacknico.com/wp-content/uploads/2026/03/image-29-1024x847.png "我用 AI“抄袭”了 flomo，并且 —— 开源了！")

因此关于同步方面有两套方案，一个是自己部署服务器，另一个是安装一下坚果云用它的 WebDAV。

当然我也做了导入导出功能，可以导入 flomo 的笔记，以及把笔记导出到 flomo。

---

自己做这些东西确实很难，总是遇到很多问题，目前还在实验中，希望不会有太多 bug，喜欢记笔记同时又有钱的小伙伴还是建议用 flomo。

<!-- content-case-notes -->

## 可以参考什么

参考它先回答“为什么已有产品还不够”，很快给出仓库和差异，再把大部分篇幅留给真实的架构错误、同步方案和取舍。结尾承认产品仍在实验，可信度来自不掩饰缺点。

## 适用场景

适合发布自己做的开源产品，同时复盘开发过程和未解决问题。不要借用其中的产品结论替代本次实测。
