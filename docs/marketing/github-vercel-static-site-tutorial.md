---
title: 不用买服务器！GitHub + Vercel 把静态网站上线，绑定域名全流程教程
description: 手把手教你把 HTML、CSS、JavaScript 静态网站提交到 GitHub，再用 Vercel 自动部署并绑定自定义域名，含截图、DNS 配置和域名购买建议。
keywords: GitHub部署静态网站、Vercel部署教程、静态网站上线、GitHub上传网页、Vercel绑定域名、DNS配置、个人网站搭建、免费部署网站、freellm.top、免费AI资源
---

# 不用买服务器！GitHub + Vercel 把静态网站上线，绑定域名全流程教程

> 从一个 `index.html` 开始，跟着做一遍，你就能拥有一个可以被别人访问的正式网站。

很多人第一次做网站，卡的不是 HTML，而是“写完以后怎么让别人访问”。其实，一个只由 HTML、CSS、JavaScript 和图片组成的静态网站，不需要先购买服务器，也不需要配置复杂的后端，就可以通过 GitHub 和 Vercel 快速上线。

本文也会用 [freellm.top](https://freellm.top/) 作为真实案例，展示一个 AI 资源导航站如何持续更新、自动发布和绑定自己的域名。

这篇教程用最简单的路径演示完整流程：

> 本地静态文件 → GitHub 仓库 → Vercel 自动部署 → 自定义域名

如果你搜索的是“GitHub 怎么部署网站”“Vercel 怎么绑定域名”“静态网页怎么免费上线”，这篇文章可以从头到尾照着操作。

## 先说清楚：Vercel 免费方案可以用吗？

可以部署静态网站，但要看你的使用场景。

Vercel 的 Hobby 方案面向个人、非商业用途；个人学习项目、作品集、实验站点通常适合从这里开始。如果网站已经用于商业运营、企业业务、付费产品、广告变现或客户项目，应先阅读当前计划条款，并考虑 Pro 或其他合适方案。不要只因为“部署按钮是免费的”，就默认所有用途都免费。

另外，网站内容仍需遵守 Vercel 的可接受使用政策：不要用于诈骗、钓鱼、侵权、垃圾信息、恶意爬取、代理/VPN、热链媒体等用途。AI 资源导航、个人主页、文档站、开源项目展示这类正常静态内容，一般属于常见的网站使用场景，但最终还是以你自己的实际内容和当前政策为准。

参考：[Vercel Hobby Plan](https://vercel.com/docs/plans/hobby)、[Vercel Terms of Service](https://vercel.com/legal/terms)、[Acceptable Use Policy](https://vercel.com/legal/acceptable-use-policy)。

## 一、准备一个最小静态网站

先新建一个文件夹，例如 `my-static-site`，里面放一个 `index.html`：

```html
<!doctype html>
<html lang="zh-CN">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>我的第一个静态网站</title>
    <style>
      body {
        max-width: 760px;
        margin: 0 auto;
        padding: 72px 24px;
        font-family: system-ui, sans-serif;
        line-height: 1.7;
      }
      a { color: #315cf5; }
    </style>
  </head>
  <body>
    <h1>你好，Vercel</h1>
    <p>这是一个由 GitHub 自动部署的静态网站。</p>
    <p><a href="https://freellm.top/">顺便看看 FreeLLM</a></p>
  </body>
</html>
```

如果还有样式、脚本和图片，可以整理成这样：

```text
my-static-site/
├─ index.html
├─ style.css
├─ script.js
└─ images/
```

关键点只有一个：网站首页通常需要叫 `index.html`，并且放在部署根目录，或者放在你稍后配置的输出目录中。

## 二、在 GitHub 创建仓库

1. 登录 [GitHub](https://github.com/)，点击右上角的 `+`，选择 `New repository`。
2. 填写仓库名，例如 `my-static-site`。
3. 选择 `Public` 或 `Private`。个人演示项目可以公开；如果仓库里有不应公开的内容，就选择私有。
4. 如果你准备直接上传已有文件，可以先不要勾选 README、`.gitignore` 和 License，避免后续出现不必要的合并冲突。
5. 点击 `Create repository`。

![GitHub 新建仓库入口截图](https://docs.github.com/assets/cb-29762/images/help/repository/repo-create-global-nav-update.png)

图 1：从 GitHub 右上角菜单进入新建仓库。图片来自 [GitHub 官方文档](https://docs.github.com/en/repositories/creating-and-managing-repositories/creating-a-new-repository)。

![GitHub 创建仓库表单截图](https://docs.github.com/assets/cb-89988/images/help/repository/create-repository-name.png)

图 2：填写仓库名称和可见性。GitHub 官方文档也提醒，仓库名只能使用字母、数字、`.`、`-` 和 `_` 等字符。

## 三、把静态文件提交到 GitHub

创建仓库后，选择 `Add file` → `Upload files`，把 `index.html`、CSS、JS 和图片拖进去。

上传后，在页面底部填写一次提交说明，例如：

```text
Initial static site
```

然后点击 `Commit changes`。

提交完成后，确认仓库根目录能看到 `index.html`。如果 `index.html` 被放进了多一层的文件夹，Vercel 可能会找不到首页；这种情况下，要么把文件移动到仓库根目录，要么在 Vercel 中填写正确的 Root Directory。

如果你更习惯命令行，也可以这样提交：

```bash
git init
git add .
git commit -m "Initial static site"
git branch -M main
git remote add origin https://github.com/你的用户名/my-static-site.git
git push -u origin main
```

注意：不要把 API Key、密码、私钥和 `.env` 文件提交到公开仓库。静态网站里的前端 JavaScript 会被访问者看到，任何写在前端的密钥都不是真正的秘密。

## 四、在 Vercel 导入 GitHub 项目

1. 打开 [Vercel Dashboard](https://vercel.com/dashboard)，使用 GitHub 登录。
2. 点击 `Add New` → `Project`。
3. 在 Git 仓库列表中找到刚才的 `my-static-site`，点击 `Import`。
4. 项目名称可以保持默认，也可以改成自己喜欢的名字。
5. 对于只有 HTML、CSS、JS 的项目，设置如下：

   - **Framework Preset**：选择 `Other`
   - **Build Command**：留空；如果页面出现 Override 开关，打开后留空
   - **Output Directory**：使用仓库根目录，或填写实际静态文件目录
   - **Install Command**：没有 `package.json` 时通常不需要填写

6. 点击 `Deploy`。

Vercel 会生成一个 `vercel.app` 结尾的临时域名。打开它，如果能看到你的首页，就说明第一次部署成功了。

Vercel 的 Git 集成有一个很实用的特点：连接仓库后，新的 commit 或 Pull Request 可以自动触发新的部署，并为改动生成预览地址。静态项目不需要每次手动上传压缩包。

官方参考：[Vercel for GitHub](https://vercel.com/docs/git/vercel-for-github)、[Configuring a Build](https://vercel.com/docs/builds/configure-a-build)。

## 五、以后如何更新网站？

以后只需要改文件并提交到连接的分支即可：

```bash
git add .
git commit -m "Update homepage"
git push
```

Vercel 会自动开始构建和部署。推荐的工作习惯是：

- `main` 分支对应正式站点；
- 新功能先放在单独分支；
- 先查看 Vercel Preview Deployment；
- 确认手机端、链接和图片都正常，再合并到 `main`。

如果网页没有更新，先检查三件事：是否推送到了正确分支、Vercel 项目是否连接了正确仓库、Build 和 Output Directory 是否填写正确。

## 六、绑定自己的域名

有了 `xxx.vercel.app` 以后，你可以绑定自己的域名，例如 `example.com` 或 `www.example.com`。

### 1. 在 Vercel 添加域名

进入项目 → `Settings` → `Domains`，输入你的域名并点击添加。

以根域名为例：

```text
example.com
```

如果还想使用 `www`，也把下面这个一起添加：

```text
www.example.com
```

建议最后确定一个主地址，例如统一使用 `https://example.com`，再把 `www.example.com` 重定向到它，避免搜索引擎把两个地址当成两个页面。

### 2. 在域名服务商配置 DNS

Vercel 会显示该域名需要的记录。常见配置是：

| 域名 | 类型 | 主机记录 | 目标值 |
|---|---|---|---|
| 根域名 | A | `@` | `76.76.21.21` |
| `www` 子域名 | CNAME | `www` | `cname.vercel-dns-0.com` |

这两个是 Vercel 文档中的通用示例值；你的项目可能会显示专属值，请优先使用 Vercel 域名页面或 `vercel domains inspect` 给出的记录。

如果用命令行，可以这样查看：

```bash
vercel domains inspect example.com
```

DNS 修改后通常需要等待一段时间。验证成功后，Vercel 会自动申请 HTTPS/SSL 证书。官方步骤见 [Setting up a custom domain](https://vercel.com/docs/domains/set-up-custom-domain)。

## 七、域名去哪里买？

域名注册商可以按自己的地区、支付方式和后缀需求选择：

| 渠道 | 适合谁 | 购买前重点看什么 |
|---|---|---|
| [Cloudflare Registrar](https://www.cloudflare.com/products/registrar/) | 重视 DNS、CDN 和安全功能的人 | 先确认目标后缀是否支持，比较续费价 |
| [Namecheap](https://www.namecheap.com/domains/) | 想要国际化界面和较多后缀选择的人 | 首年优惠与第二年续费价可能不同 |
| [Porkbun](https://porkbun.com/) | 喜欢简单界面、想比较不同后缀的人 | 看隐私保护、转入价格和续费价格 |
| 阿里云万网 / 腾讯云 DNSPod | 更习惯国内支付和中文控制台的人 | 实名、备案、DNS 和境内访问要求 |

买域名时不要只看“首年几块钱”，至少检查：

1. 第二年续费多少钱；
2. 是否包含 WHOIS 隐私保护；
3. 是否支持完整 DNS 记录管理；
4. 是否方便转出；
5. 目标后缀是否有额外注册或合规要求。

`.top`、`.com`、`.net` 等后缀的价格会随注册商和促销变化，结算前一定以当时显示的续费价格为准。

## 八、用真实案例看看：freellm.top 是什么？

如果你正在找免费的 AI 工具、模型或 API，推荐收藏 [freellm.top](https://freellm.top/)。

它不是简单罗列一堆链接，而是把不同类型的“免费”拆开整理：

- 永久免费或长期免费额度；
- 限时试用和首购优惠；
- 免费 API 和 OpenAI 兼容接口；
- 免费 AI IDE；
- 开源模型权重与本地下载；
- 学生优惠、地区限制、使用期限和官方来源。

![FreeLLM 首页截图](https://freellm.top/freellm-01-hero.png)

图 3：FreeLLM 首页，按“模型、API、IDE 与限时试用”组织入口。

![FreeLLM 分类筛选截图](https://freellm.top/freellm-02-categories.png)

图 4：可以按大模型、免费 IDE、图像视频、API 服务、开源模型等分类筛选。

![FreeLLM 资源目录截图](https://freellm.top/freellm-04-catalog-offers.png)

图 5：每条资源尽量同时展示免费方式、额度、有效期、地区和官方来源。

打开网站后，可以从搜索框开始，也可以直接进入这些入口：

- [全部模型](https://freellm.top/models/)
- [免费额度](https://freellm.top/category/free-quota/)
- [免费 IDE](https://freellm.top/category/free-ide/)
- [API 服务](https://freellm.top/category/api/)
- [开源权重](https://freellm.top/category/open-weights/)
- [免费 OpenAI API 替代方案](https://freellm.top/guides/free-openai-api-alternatives/)

使用时还要注意：免费额度可能有地区、速率、实名、绑卡、新用户或有效期限制；开源权重免费，也不代表 GPU、存储和流量免费。最稳妥的做法，是通过 FreeLLM 找到入口后，再点回官方价格页确认当前条件。

## 九、完整检查清单

上线前可以按下面这张清单快速检查：

- [ ] GitHub 根目录有 `index.html`
- [ ] 仓库里没有 API Key、密码或私钥
- [ ] Vercel 项目连接了正确的 GitHub 仓库
- [ ] 静态项目使用 `Other`，没有误填不存在的构建命令
- [ ] Preview 地址能正常打开
- [ ] 手机端布局没有横向溢出
- [ ] 图片、CSS、JS 路径大小写正确
- [ ] 自定义域名的 DNS 记录已按 Vercel 要求配置
- [ ] 根域名与 `www` 已确定主次关系
- [ ] HTTPS 证书已签发
- [ ] 如果是商业用途，已确认 Vercel 计划和条款适用

## 结语

部署静态网站最省心的组合，通常就是 GitHub 负责保存代码和记录版本，Vercel 负责自动构建、预览和发布，域名注册商负责域名与 DNS。

先用一个简单的 `index.html` 跑通完整链路，再逐步加入样式、交互和内容。等你准备好以后，也可以把网站做成自己的工具导航、作品集、博客或 AI 资源目录。

如果你想快速了解现在有哪些值得尝试的免费 AI，直接访问：[freellm.top](https://freellm.top/)。

---

> 文中平台界面、计划限制、免费额度和域名价格都会变化；发布前建议重新打开官方页面核对一次。
