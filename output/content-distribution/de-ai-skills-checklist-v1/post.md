# 我扒了 12 个“去 AI 味”项目，真正属于文字去味 Skill 的只有 7 个

AI 写的东西为什么总能被一眼认出来？

不是它写错了，而是它太像标准答案：开头先来一句“在当今快速发展的时代”，中间“值得注意的是”，结尾再“让我们深入探讨”。

我把 12 个经常被放进“去 AI 味 Skill”清单的项目逐个拆开，结果发现，真正直接处理文字的去味 Skill 只有 7 个。剩下 5 个分别是 Prompt、完整写作系统、AI 检测器、人物蒸馏工具和前端设计 Skill。

别再看见 Humanizer、Slop、Taste 这些词就全装一遍了。下面这份才是它们真正的分工。

## 真正直接改稿的 7 个 Skill

1. [Humanizer](https://github.com/blader/humanizer)

英文去 AI 味的基础款。它按照常见 AI 写作特征，检查意义拔高、宣传腔、模糊归因、套路句式和机械节奏。主要写英文，可以先从它开始。

2. [Humanizer-zh](https://github.com/op7418/Humanizer-zh)

Humanizer 的中文改编版，适合公众号、口播稿和中文长文。不过它不是一套完全独立的新方法：项目自己注明了“翻译自 Humanizer，参考 Stop-Slop”。

3. [Stop-Slop](https://github.com/hardikpandya/stop-slop)

更像一位下手很重的英文编辑。开场废话、二元对比、假装深刻的短句、被动语态和整齐得过头的节奏，看到就删。适合已经写完、准备做最后清理的英文稿。

4. [说人话](https://github.com/MrGeDiao/shuorenhua)

中文用户更值得先看的一个。它不只删“赋能、闭环、系统性升级”，还会先保护数字、版本、命令和责任关系，避免 AI 味没了，事实也被改没了。仓库里还能看到公开用例、误杀检查和失败记录。

5. [De-AI Prompt Enhancer](https://github.com/OUBIGFA/De-AI-Prompt-Enhancer-Writer-Booster-SKILL)

它有两种模式：一种负责去模板腔，另一种从真实文章中提取作者风格。适合已经有稳定样稿，想让 AI 长期靠近某种具体文风的人。它的上游也是 Humanizer-zh。

6. [no-ai-slop](https://github.com/petergyang/no-ai-slop)

它最有价值的一点是“尽量少改”。先保留作者原来的词、节奏、幽默和锋芒，再处理问题句；也可以只标出 AI 痕迹，不直接重写。

它和 Humanizer、Stop-Slop 的规则重叠不少，更适合看成一份重新整理过的整合替代品。

7. [deslop](https://github.com/xingpt88/deslop)

一份方便安装的中文规则合集，整合了 Humanizer、Stop-Slop、avoid-ai-writing 和 talk-normal，重点处理“不是 X，而是 Y”、废话铺垫、商业黑话和模板句。

优点是集中，缺点是目前没有公开的独立评测。可以试，但别直接把它说成“实测最强”。

## 能改稿，但它不是 Skill

8. [AI Flavor Remover](https://github.com/hylarucoder/ai-flavor-remover)

它本质上是一段中文润色 Prompt，不是完整的 Skill 项目。复制到模型里就能用，门槛低；作者只写明在 Gemini 2.5 Pro 上测试过，所以换模型后效果需要重新判断。

## 和去 AI 味有关，但解决的是别的问题

9. [Writing Agent](https://github.com/dongbeixiaohuo/writing-agent)

它把选题、证据、结构、起草、去味、审稿和终稿导出全包了。想建立完整写作生产线再看它，只想改一段话就没必要上这么重。

10. [ChatGPT Comparison Detection](https://github.com/Hello-SimpleAI/chatgpt-comparison-detection)

这是 HC3 人类与 ChatGPT 对比语料和检测模型的研究仓库。它负责判断文本更接近哪一类，不负责把文章改好，更不是一个可直接调用的去味 Skill。

11. [Nuwa Skill](https://github.com/alchaincyf/nuwa-skill)

Nuwa 会研究一个人的公开材料，提取他的思维模型、判断规则和表达特征，再制作成人物视角 Skill。

它回答的是“这个人会怎样思考和说话”。普通去 AI 味处理的是一篇现成稿件，两者方向不同。

12. [Taste Skill](https://github.com/Leonxlnx/taste-skill)

它确实在反 AI Slop，但反的是前端页面里的模板化设计：千篇一律的布局、字体、间距和动效。做网站很有用，改文章帮不上忙。

## 最后给个选择结论

- 写中文：先试“说人话”或 Humanizer-zh。
- 写英文：Humanizer、Stop-Slop、no-ai-slop 三选一，不用全装。
- 想保留个人文风：看 De-AI Prompt Enhancer。
- 想从选题一路做到发布：看 Writing Agent。
- 只想复制一段 Prompt 立即试：AI Flavor Remover。
- Nuwa、Taste Skill 和 ChatGPT Comparison Detection，不要再当成文章去味工具。

装满 12 个 Skill 意义不大。先判断自己的稿子到底缺什么：套话太多、中文腔太重、个人风格消失，还是整个写作流程根本没建立起来。

这份清单建议先收藏。下一次再看到“10 个去 AI 味神器”，先检查它究竟能不能改文字，别被名字里的 Slop 带跑了。
