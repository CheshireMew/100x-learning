---
authorship: "本人主导"
reference_value: "case"
content_type: "教程与操作指南"
source_url: "https://blog.blacknico.com/guide/installing-openclaw-on-a-cloud-server/"
writing_task: "写实测安装避坑教程"
topics: ["OpenClaw", "云服务器", "Telegram 机器人"]
structure: ["真实使用动机", "按步骤推进", "坑点就地出现", "完成后给可见结果"]
---

# OpenClaw 云服务器最新安装避坑指南

OpenClaw 火了有一阵子了，这个时候写安装教程也是赶不上热度。

但为了参加最近各种奖励丰厚的活动，还是咬咬牙装上了小龙虾。你别说，用来做  [群聊机器人](https://t.me/CheshireBTC)  还是挺不错的，大家都很喜欢。

![image](https://blog.blacknico.com/wp-content/uploads/2026/03/image-9-1024x680.png "OpenClaw 云服务器最新安装避坑指南")

安装 OpenClaw 现在其实一点都不难了，一行命令即可，但是坑比较多，下面让我一一为你道来。

### 1. 服务器选择

为什么要用云服务器呢？因为这玩意儿权限这么高，并且还有隐私泄露风险，所以必须要用一个封闭测试环境。而 OpenClaw 对 Windows 支持不好，我又不是苹果用户不买 Mac mini，那就只有上 Linux 了。

服务器我选择了  [RackNerd 这款 3 核心](https://www.racknerdcn.com/all-coupons.html) 的，$29.98 一年。我不是劝你买哪家的，因为这时候，第一个坑来了！

![image](https://blog.blacknico.com/wp-content/uploads/2026/03/image-11-1024x394.png "OpenClaw 云服务器最新安装避坑指南")

RackNerd 的大部分服务器在美国，这就导致很多在美国受限的服务没法使用，比如币安相关的 skill，这就很尴尬了。

但谁让它便宜呢，我忍了！

我之前买的部署博客网站的服务器是 Hostinger，使用这个链接注册可以获得 20% 折扣：<https://hostinger.my?REFERRALCODE=LKCDYLANZEU2>

买的时候还可以用优惠码: HOANWP (10% 折扣)，把语言改成马来西亚，会便宜一些；其实改成印度更便宜，但只支持 Paypal 支付。

不过价格相对来讲就没那么美丽，大家自行选择。

购买服务器后你会收到相关信息，这时候打开终端管理员 Powershell，输入`ssh root@你的 VPS_IP -p 你的 SSH 端口`，再输入服务器的密码就可以连接上云服务器了。

### 2. 安装 OpenClaw

在终端输入 `curl -fsSL https://openclaw.ai/install.sh | bash` 就可以一键安装龙虾，包括所有的配置。建议使用 Powershell，因为安装 OpenClaw 的时间很长，用其它工具连接可能会断开。

不过断开了也没关系，重新执行这个命令就可以继续。

安装完成后会让你选择，一路点“Yes”就可以了。

![image](https://blog.blacknico.com/wp-content/uploads/2026/03/image-12-1024x504.png "OpenClaw 云服务器最新安装避坑指南")

### 3. 配置大模型

国产模型比较便宜，我选择了据说和 Claude 最像的 [MiniMax](https://www.minimax.io/pricing)。然后坑爹的又来了，无论我在网页上怎么点击它那个购买按钮都没反应，只好到手机上购买。

我选择了 49 块钱一个月的套餐，每 5 小时可以调用 100 次，我对国产模型也不奢望太多，量大价低管饱就行。

![image](https://blog.blacknico.com/wp-content/uploads/2026/03/image-13-1024x374.png "OpenClaw 云服务器最新安装避坑指南")

购买套餐后可以在用户中心找到密钥，复制一下，然后在终端输入`openclaw config`。

![image](https://blog.blacknico.com/wp-content/uploads/2026/03/image-14.png "OpenClaw 云服务器最新安装避坑指南")

接着选择 Local – Model – MiniMax，然后输入密钥就配置上大模型了，其他模型同理，也可以自定义模型，具体还有不懂的可以问 AI。

### 4. 连接 Telegram

虽然我们现在接上了 AI，但是在 Linux 里面跟龙虾聊天确实比较麻烦，我们可以把聊天放到 Telegram 或者飞书里。这里就先只说 Telegram，飞书如果大家感兴趣的话可以留言，到时候再出一篇。

首先在 Telegram 中和 @BotFather 聊天，发送 `/newbot`，按照它的指示一步一步创建一个机器人，完成后它会给你一个 HTTP API 密钥，点击复制。

然后同样是在终端输入`openclaw config`，接着选择 Local – Channels – Configure/link，第一个就是 Telegram，同样是输入密钥，流程很简单。

![image](https://blog.blacknico.com/wp-content/uploads/2026/03/image-15.png "OpenClaw 云服务器最新安装避坑指南")

然后随便发送点什么给机器人，它回复给你的信息最后一行有一串指令，把它复制并输入到终端里。

![image](https://blog.blacknico.com/wp-content/uploads/2026/03/image-16-1024x1002.png "OpenClaw 云服务器最新安装避坑指南")

再次和它对话它就会回复了！

我同样把它拉进了 Telegram 群组，想体验的可以来群里调戏一下：<https://t.me/CheshireBTC>

<!-- content-case-notes -->

## 可以参考什么

参考它用一次已经完成的安装作为主线，按照服务器、安装、模型和聊天入口推进。坑点出现在对应步骤旁边，并带着当时的选择和代价，不另开一章泛泛总结“注意事项”。

## 适用场景

适合软件安装、部署和配置类实测教程。命令、价格和平台限制具有时效性，写新教程时必须重新验证。
