# TVBox 成人站接口合集（自托管版）

把分散在多个来源里的成人站 TVBox 接口，合并成**一份可直接上传 GitHub 的自托管配置**。
上传后，TVBox 的接口内容全部从你自己的仓库 `raw.githubusercontent.com` 拉取，不再依赖第三方服务器。

---

## 一、目录结构

```
tvbox-interfaces/
├── box.json            ← 主配置（自托管，相对路径 ./spiders/...）★ 上传这个
├── box-remote.json     ← 同 132 站，但用绝对 URL（不上传也能直接用）
├── spiders/            ← 4 个 csp 站引用的本地文件（共 5 个）
│   ├── hanime1_direct.py
│   ├── gm.jar
│   ├── 123av.user.js
│   ├── missav.user.js
│   └── hanime1.user.js
├── sources/            ← 原始来源配置（留档，供排查）
│   ├── 18cn.json
│   ├── R18.json
│   └── wtc1069-hanime1-missav-box.json
├── finalize.py         ← 合并/去重/校验脚本（可复现本配置）
└── README.md
```

## 二、站点统计（box.json）

| 类型 | 说明 | 数量 |
|---|---|---|
| type 1 | `api.php/provide/vod/` 采集接口（远端 API） | 72 |
| type 0 | 通用采集接口（远端 API） | 56 |
| type 3 | csp 爬虫（本地 `spiders/` 文件） | 4 |
| **合计** | | **132** |

4 个 csp 站及其本地文件（均已随包提供，上传后即可用）：

| 站 key | 引用的本地文件 |
|---|---|
| `hanime1_direct.py` | `./spiders/hanime1_direct.py` |
| `Hanime1` | `./spiders/gm.jar` + `./spiders/hanime1.user.js` |
| `MissAV` | `./spiders/gm.jar` + `./spiders/missav.user.js` |
| `123av` | `./spiders/gm.jar` + `./spiders/123av.user.js` |

> 顶层还保留了 `parses`（解析）、`flags`、`ijk`、`ads`、`lives`（1 个可正常工作的远端直播源）等 TVBox 常用设置，均自包含、无本地文件依赖。

## 三、合并与去重说明

- **来源**：`18cn.json`（46 站）、`R18.json`（101 站）、`wtc1069-hanime1-missav-box.json`（4 站）。
- **去重**：按 `key` 去重，合并后 134 站。
- **剔除 2 个 18cn csp 站**（`转点`、`csp_xBPQ_公子福利`）：
  - 二者都指向 123AV，而 `123av`（`123av.user.js`）站已完整覆盖 123AV，功能重复；
  - 且它们依赖 `./lib/apiv2542直转点.js`、`./lib/直转点.txt`、`./lib/xBPQ.jar` 三个文件，原 18cn 主机已无法访问（探测均 502/404），无法随包提供。
  - 剔除后 **132 站，全部 csp 引用都能在本仓库内解析，零悬空引用**。
- **剔除 1 个直播源**：`lives` 里引用 `./lib/RTV.txt` 的直播列表（文件同样拿不到），保留另一个可正常工作的远端直播代理。

## 四、上传到你的 GitHub

1. 新建一个仓库（如 `tvbox`），把本目录内容全部上传：
   ```
   box.json  box-remote.json  README.md  finalize.py
   spiders/  sources/
   ```
2. 打开仓库 → **Settings → General → 确认 Public**（TVBox 需能匿名访问 raw 文件）。
3. 你的接口地址就是：
   ```
   https://raw.githubusercontent.com/<你的用户名>/tvbox/main/box.json
   ```
   （分支名按实际改，默认 `main`。）
4. 把该地址填进 TVBox / 影视仓 的「配置地址」即可，接口内容从此只从你的仓库拉取。

## 五、TVBox 使用

- **自托管（推荐）**：用上面的 `box.json` raw 地址。csp 站走 `./spiders/` 相对路径，自动指向你仓库里的文件。
- **免上传直接用**：用 `box-remote.json`（csp 文件走 wtc1069 的 GitHub 绝对地址），无需上传，但依赖第三方服务器。

## 六、注意

- type 0 / type 1 是**远端采集 API**，本身无法本地化，接口可用性取决于对方服务器是否在线；失效多为对方关停，可在 `sources/` 里对照原始配置排查。
- 只有 type 3 的 csp 文件能自托管（已放入 `spiders/`）。
- 若日后找到 18cn 的 `./lib/` 三个文件，可补回 `转点`、`csp_xBPQ_公子福利` 两站（把文件放进 `spiders/` 并改相对路径即可）。
