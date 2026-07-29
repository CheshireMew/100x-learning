---
authorship: "本人主导"
reference_value: "case"
content_type: "项目与产品介绍"
source_url: "https://blog.blacknico.com/guide/aicreatewebsite/"
writing_task: "把亲手完成的项目写成经历式教程"
topics: ["个人建站", "AI 辅助实践", "WordPress"]
structure: ["多年愿望与现实痛点", "关键选择与理由", "边做边解决问题", "成品与下一步"]
---

# AI 控制我搭建了这个网站！

好吧，这个标题确实是我想耸人听闻一下。

这是我搭建好的网站，欢迎来玩：blacknico.com

![blacknico-image](https://blog.blacknico.com/wp-content/uploads/2025/12/blacknico-image-1024x490.jpg "AI 控制我搭建了这个网站！")

搭建网站这个想法一直根植在我心中很多年，奈何受到的教育不多资金有限。终于，我忍受不了 Substack 文章无法被谷歌收录，决定搭建属于我自己的一个博客。
整个过程完全在 ChatGPT 的建议下进行，我本人不会一点代码，它帮助我完成了这个网站！感谢 AI！

---

## 选择域名和服务器

我的理想是建一个网站，我的余生都可以在这个网站上更新，运气好的话大概是几十年吧。
因此我需要稳定的服务。
很多人都推荐 NotionNext，但我希望自由度能更高一点。
我的野心并不只是搭建一个简单的博客，而是幻想，如果有一天我 Vibe coding 出来一个牛逼的在线工具，不就能把它放到我网站上了。

### 服务器

虽然还是看了其他几家便宜的服务器提供商，最终还是选择 [Hostinger](https://hostinger.my?REFERRALCODE=LKCDYLANZEU2)。
刚工作有了一点钱的时候其实在 Hostinger 搭过一个网站，但当时什么都不懂，也没尽力瞎折腾，钱就这么被浪费掉了。当时买的还是 4 核 16 G 的高配 VPS，现在想想也蛮离谱的。
如果你也打算使用 Hostinger，可以使用我的这个链接注册，获得 20% 折扣：<https://hostinger.my?REFERRALCODE=LKCDYLANZEU2>
买的时候还可以用优惠码: **HOANWP** (10% 折扣)

**另外，还有一个小技巧：**
注册之前把语言改成马来西亚，会便宜一些；其实改成印度更便宜，但只支持 Paypal 支付，而我的 Paypal 账号被永久限制了 /(ㄒ o ㄒ)/~~

下一个选择是使用能一键搭好 WordPress 的虚拟主机还是 VPS 服务器，出于自由度的考虑我再次选择了 VPS。

![image](https://blog.blacknico.com/wp-content/uploads/2025/12/image-1024x612.jpg "AI 控制我搭建了这个网站！")

考虑到性能问题，选择了 2 核 8 G 的 2 年，活动叠加优惠码花费 539.78 马来西亚林吉特，差不多 930 人民币。

### 域名

买完服务器后本想在 Hostinger 上继续买域名，发现相比于买服务器之前贵了不少，感觉被坑了。送的一年免费域名竟然是 .cloud（虚拟主机应该是会送 .com 之类的域名的），遂开始找其他的域名服务商。
看了不少文章都说要优先选 .com 域名，更容易被谷歌收录。
最后敲定在 Cloudflare Registrar 买，反正最后还是要找 Cloudflare 解析域名，而且后续续费也是成本价。
不过买了他家就没法用其他的 DNS 服务商了，后面带来了一些小麻烦。

![image](https://blog.blacknico.com/wp-content/uploads/2025/12/image-2-993x1024.png "AI 控制我搭建了这个网站！")

#### 域名选择

说实话我想不出来什么好听的域名，好一点的 .com 域名都很贵。
这时候我脑子里蹦出来一句日语歌，其中有一句 blackneko（意思是黑猫，英语 black + 日语ねこ，neko），然后我就想不出其他的来了，那就 Blacknico 吧！
选择买了 10 年，想逼自己一把，长期建设这个网站。要是有 20 年的我恐怕也会脑子一热买了。
花费 104.6 美元，大约 738 人名币。

10 年域名和 2 年的服务器，总计 1668 人民币，希望这钱花得值！

**上述所有选择都询问过 GPT 的意见，它确实帮助我下定了决心。**

---

## VPS 设置和解析域名

VPS 买好后，按照 Hostinger 的指示一步一步来就行了。
添加 SSH 秘钥这一步不是很懂，问了 GPT。

![image](https://blog.blacknico.com/wp-content/uploads/2025/12/image-4-1024x511.jpg "AI 控制我搭建了这个网站！")

原来是先在自己的电脑上生成一对 SSH 密钥（钥匙对），然后把公钥粘贴到这里。

**步骤：**
在自己的电脑上打开终端（Windows 可用 PowerShell）。
执行命令：

```
ssh-keygen -t ed25519 -C " 你的邮箱 @example.com"
```

一路回车即可（不懂就先不要设置密码短语）。
生成后，会在你电脑的 `~/.ssh` 目录下多出两个文件：
`id_ed25519`（私钥，不能给别人）
`id_ed25519.pub`（公钥，可以复制）
用文本编辑器打开 `id_ed25519.pub`，复制整行内容，粘贴到弹窗里的“SSH key content”。
Name 随便起一个名字，比如 my-laptop-key，然后点 Save。

在验证域名，Hostinger 让我删除域名服务器替换为它的域名服务器，但上面也说了 Cloudflare 改不了。

![image](https://blog.blacknico.com/wp-content/uploads/2025/12/image-1-1024x534.jpg "AI 控制我搭建了这个网站！")

GPT 告诉我要在 Cloudflare 上设置：

1. 在 Hostinger VPS 面板里记下你的 VPS 公网 IP（IPv4 地址）；
2. 登录 Cloudflare → 选中站点 → 左侧点「DNS」→ 记录；
3. 新增或修改一条 A 记录：
   > Name：@（代表根域名 blacknico.com）
   > IPv4 address：填你的 VPS 公网 IP
   > Proxy 可以先开着（橙色小云），以后要关再说；
4. 再加一条 www 的 CNAME，让 www.blacknico.com 也指向根域（或直接做一条指向 IP 的 A 记录）。

![image](https://blog.blacknico.com/wp-content/uploads/2025/12/image-2-1024x298.jpg "AI 控制我搭建了这个网站！")

因为我打算让博客在子域名 blog.blacknico.com 下，因此又加了一个 blog 指向我的 VPS 公网 IP。

---

## SSH 登陆

我一开始用的 XShell，但是很卡，后来换了 FinalShell，在 Bilibili 上看见的，推荐一下，免费版本就够用了。

![image](https://blog.blacknico.com/wp-content/uploads/2025/12/image-3-1024x583.jpg "AI 控制我搭建了这个网站！")

导入刚刚添加 SSH 秘钥步骤产生的私钥，填入一个名字和刚刚设置的秘钥密码；
链接，输入设置的 VPS 密码，就可以使用 SSH 登陆上 VPS 了。

---

## 安装 Nginx

（即使我不知道 Nginx 是什么）
我选择的系统是 Debian，如果你想装系统面板啥的可以先装个宝塔面板之类的，我没装后面有问题可累死我了。
输入下面的命令：

```
apt update
apt install -y nginx
systemctl enable nginx
systemctl start nginx
```

启动之后，在浏览器访问：

```
http:// 你的 VPS 公网 IP
```

如果看到“Welcome to nginx!”页面，就说明：

> 外网 → 服务器 IP → Nginx 这条链路是通的。

如果这时候访问 `https:// 你的域名` 时会出现 Cloudflare 的 **521 错误**（Web server is down）。

因为用的是 `https` 而不是 `http`，这时候还没有装证书。

---

## 安装 MariaDB 数据库

接下来要搭 WordPress，就需要一个数据库。我第一次听说是 MariaDB 而不是 MySQL，GPT 告诉我它是从 MySQL fork 出来的高度兼容版本。
安装命令很简单：

```
apt install -y mariadb-server
```

装完之后，要跑一遍 MariaDB 自带的安全配置脚本：

```
mariadb-secure-installation
```

它会问一串问题，这样选择：

- 是否切换到 unix\_socket 认证：`n`（保持用密码登录，方便后续用 `mariadb -u root -p`）
- Remove anonymous users? → `Y`（删除匿名账号）
- Disallow root login remotely? → `Y`（禁止 root 远程登录，只在本机使用）
- Remove test database and access to it? → `Y`（删除 test 库）
- Reload privilege tables now? → `Y`（立刻刷新权限）

跑完脚本之后，为 WordPress 创建一个专属库和专属账号：

```
mariadb -u root -p
```

输入数据库 root 密码进入之后，依次执行：

```
CREATE DATABASE wordpress DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'wpuser'@'localhost' IDENTIFIED BY ' 这里换成一个强密码 ';
GRANT ALL PRIVILEGES ON wordpress.* TO 'wpuser'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

这几行的含义分别是：

- 新建一个叫 `wordpress` 的库，使用 utf8mb4 编码（支持中文和 emoji）；
- 新建一个只允许本机访问的用户 `wpuser`，设一个强密码；
- 只在 `wordpress` 这个库里授予它全部权限，其他库一概无权访问；
- 刷新权限，让改动即时生效。

到这一步，数据库层已经为 WordPress 准备好了一个安全、独立的空间。

---

## 安装 PHP

WordPress 是 PHP 应用，所以还需要 PHP-FPM 和必要扩展：

```
apt install -y php-fpm php-mysql php-xml php-gd php-curl php-mbstring php-zip
```

安装完成后，用下面的命令确认 FPM 的 sock 文件：

```
ls /run/php/
```

通常能看到类似：

```
php8.4-fpm.sock
```

这就是稍后 Nginx 里要配置的 PHP 入口。

## 设置站点

然后我们要在服务器上规划两个不同的站点根目录：

- `blacknico.com` → `/var/www/html`（作为首页，后面放一个简洁 landing）；
- `blog.blacknico.com` → `/var/www/blog`（用来放 WordPress）。

建 blog 目录：

```
mkdir -p /var/www/blog
```

接下来修改 Nginx 的默认站点配置 `/etc/nginx/sites-available/default`，改成同时服务根域和 Blog 子域。

这时候 FinalShell 的作用来了，在它的文件界面按路径找到这个文件，右键打开，用下面的代码覆盖掉原文件：

![image](https://blog.blacknico.com/wp-content/uploads/2025/12/image-5-1024x463.jpg "AI 控制我搭建了这个网站！")

```
cat > /etc/nginx/sites-available/default << 'EOF'
# 根域名：blacknico.com（静态页面）server {
    listen 80 default_server;
    listen [::]:80 default_server;

    server_name blacknico.com [www.blacknico.com](https://www.blacknico.com);

    root /var/www/html;
    index index.html index.htm;
}

# 子域名：blog.blacknico.com（WordPress 博客）server {
    listen 80;
    listen [::]:80;

    server_name blog.blacknico.com;

    root /var/www/blog;
    index index.php index.html index.htm;

    location / {
        try_files $uri $uri/ /index.php?$args;
    }

    location ~ \.php$ {
        include snippets/fastcgi-php.conf;
        fastcgi_pass unix:/run/php/php8.4-fpm.sock;
    }

    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
        try_files $uri $uri/ @fallback;
        expires max;
        log_not_found off;
    }

    location @fallback {
        try_files $uri $uri/ /index.php?$args;
    }
}
EOF
```

（如果 `ls /run/php/` 显示的是 `php8.4-fpm.sock`，就把 `fastcgi_pass` 那一行改成实际文件名。）

改完之后检查并重载：

```
nginx -t
systemctl reload nginx
```

如果 `nginx -t` 没通过，`reload` 是不会成功的，浏览器看到的就仍然是旧配置。

---

## 安装 WordPress

Nginx 配好后，就可以部署 WordPress 了。

流程是：

```
cd /tmp
curl -O [https://wordpress.org/latest.tar.gz](https://wordpress.org/latest.tar.gz)
tar -xzf latest.tar.gz
cp -r wordpress/* /var/www/blog/
chown -R www-data:www-data /var/www/blog
```

然后进入 blog 根目录，配置 `wp-config.php`：

```
cd /var/www/blog
cp wp-config-sample.php wp-config.php
nano wp-config.php
```

在文件里找到数据库相关的几行，改成前面创建数据库时用到的参数：

```
define('DB_NAME', 'wordpress');
define('DB_USER', 'wpuser');
define('DB_PASSWORD', ' 你给 wpuser 设的那个密码 ');
define('DB_HOST', 'localhost');
```

保存退出后，在浏览器访问：

```
http://blog. 你的域名
```

如果看到 WordPress 安装向导页面，说明：

> DNS → Nginx → PHP-FPM → MariaDB 这条链路，已经全部打通。

按照向导设置站点标题、管理员账号密码，就可以正式登录后台 `http://blog. 你的域名 /wp-admin` 写作了。

---

## 安装 HTTPS 证书

接下来是浏览器安全感问题：把 `http://` 变成 `https://`，去掉“不安全”的标记。

Debian 上用 Let’s Encrypt 的 certbot 很方便，先安装：

```
apt update
apt install -y certbot python3-certbot-nginx
```

对博客子域申请证书并自动配置 Nginx：

```
certbot --nginx -d blog. 你的域名
```

按提示输入邮箱、同意协议，遇到“是否将所有 HTTP 请求重定向到 HTTPS”的问题时，我选择了自动重定向。完成后访问：

```
[https://blog.blacknico.com](https://blog.blacknico.com)
```

如果可以正常打开，并且浏览器出现小锁，说明 blog 的 HTTPS 已经成功。

然后轮到根域：

```
certbot --nginx -d 你的域名 -d www. 你的域名
```

在我的执行过程中，certbot 提示：

> 已经存在一张针对这两个域名的证书，且还未接近过期，要不要重新安装还是签新证书？

这时我选择的是：

> 选项 1：**Attempt to reinstall this existing certificate**（重新安装现有证书，而不是重新签）

这样不会浪费 Let’s Encrypt 的配额，又能自动把证书挂到当前的 Nginx 配置上。

完成后测试：

```
https:// 你的域名
https://www. 你的域名
```

都能正常打开，就说明根域也已经上了 HTTPS。

至此，整个站点体系的结构变成：

- `https://blacknico.com`：首页（静态）
- `https://blog.blacknico.com`：WordPress 博客（动态）

后面如果要再挂新的子域（比如 `lab.blacknico.com`），只要重复 DNS + Nginx + certbot 这一套，整个框架是可扩展的。

---

## 开防火墙

装一个简单的 ufw 就够用，输入代码：

```
apt update
apt install -y ufw
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw default deny incoming
ufw default allow outgoing
ufw enable
ufw status
```

保留的端口只有：

> 22（SSH）
> 80（HTTP，用来签证书、重定向）
> 443（HTTPS）

这样其他乱七八糟的端口默认就被挡了。

## 关掉 Root SSH 密码登陆，使用密钥登陆

可能是因为服务器的问题，改 /etc/ssh/sshd\_config 主文件没用，直接在 /etc/ssh/sshd\_config.d/ 放一个编号更大的文件，让它最后生效：

```
sudo nano /etc/ssh/sshd_config.d/99-root-login.conf
```

写入下面内容：

```
PermitRootLogin prohibit-password
PasswordAuthentication no
KbdInteractiveAuthentication no
X11Forwarding no
```

保存后，先做语法检查再 reload：

```
sudo sshd -t
sudo systemctl reload ssh
```

然后用“最终生效值”确认一次：

```
sudo sshd -T | egrep -i 'permitrootlogin|passwordauthentication|kbdinteractiveauthentication|x11forwarding'
```

你希望看到 permitrootlogin prohibit-password、passwordauthentication no、kbdinteractiveauthentication no。

这样再次登陆的时候安全性应该高了不少！

## 安装 failtoban 防爆破(关了密码登陆可能不需要了)

安装并启用

```
sudo apt update
sudo apt install -y fail2ban
sudo systemctl enable --now fail2ban
```

用 nano 直接编辑配置文件

```
sudo nano /etc/fail2ban/jail.d/sshd.local
```

把下面这段完整粘进去

```
[sshd]
enabled = true

# Debian 13 通常用 systemd journal 作为日志后端，更稳
backend = systemd

# 如果你改过 SSH 端口，把 22 改成你的端口，例如 2222
port = 22

# 封禁策略：10 分钟内失败 5 次就封 2 小时
findtime = 10m
maxretry = 5
bantime  = 2h

# 重要：把你自己的固定出口 IP 加进去，避免误封
# 多个 IP 用空格分隔
# 没有固定 IP 保留本机回环地址即可
ignoreip = 127.0.0.1/8
```

保存退出后生效

```
sudo systemctl restart fail2ban
sudo fail2ban-client status sshd
```

## 极简首页

在博客跑起来之后，我让 GPT 给 `blacknico.com` 先生成了一个  **极简版 landing page**，既能说明这里是个人主站，又能明显给出博客入口。

这个首页就是一个单文件 `index.html`，放在 `/var/www/html/index.html`，内容大致如下（只贴核心结构）：

```
cat > /var/www/html/index.html << 'EOF'

blacknico.com · online

# Welcome to Blacknico

这里是 Blacknico 的个人主站，一部分是长期建设的博客，一部分是以后会慢慢上线的小工具和实验项目。

Overview

你现在看到的是一个极简版本的首页。后续这里会逐步变成一个更完整的「导航页」……

Main Entry

博客目前托管在独立子域
blog.blacknico.com，用于长期沉淀文字和系统化内容。

进入博客 blog.blacknico.com

©  Blacknico. All rights reserved.

EOF
```

这只是一个临时版本，未来完全可以换成更加个性化的设计，但对于“先立一个门牌号”来说，这就已经足够。

![image](https://blog.blacknico.com/wp-content/uploads/2025/12/image-6-1024x680.jpg "AI 控制我搭建了这个网站！")

---

## 结束

就这样，我终于搭建好了自己的博客站！
感谢 AI，我明显能感觉到 GPT 比以前更聪明了。这种聪明并不是它的代码能力变强了，而是它恐怕已经把互联网上教程全都吃完了，现在的 GPT 给任何普通人当老师都足够。
而我们在 AI 的帮助下，可以轻易学会一项技能。

但，这样就真的结束了吗？

不！WordPress 的坑远比你想象的更多！
下一篇文章我会继续讲讲都遇到了哪些坑🕳，以及 AI 是如何帮我解决的。

<!-- content-case-notes -->

## 可以参考什么

参考它先承认标题的夸张，再交代为什么非做不可。技术步骤始终跟着当时的选择、花费和踩坑推进，因此长教程仍像一次真实经历，而不是说明书。

## 适用场景

适合把一个从零完成的长期项目写成兼具故事与操作细节的长文。服务商、价格和命令会变化，写新内容时重新核实。
