# 抖音内容增长智能体

这是一个可迁移的本地智能体工作台。复制整个文件夹到任意电脑后，启动脚本会打开一个本地网页，用来抓取抖音主页作品、复盘内容、生成选题、优化标题封面文案，并输出 7 天发布规划。

## 启动方式

macOS / Linux:

```bash
./start_agent.sh
```

Windows 双击：

```text
start_agent.bat
```

Windows PowerShell:

```powershell
.\start_agent.ps1
```

启动后会自动打开管理页，默认地址是：

```text
http://127.0.0.1:8787/
```

## 跨系统能力

- macOS、Windows、Linux 都可以打开本地工作台。
- 通用能力是“输入抖音博主主页分享链接，抓取公开作品并分析”。
- macOS 额外支持读取已登录的抖音桌面 App 页面，适合抓取 App 中已经显示的主页作品。
- Windows / Linux 不调用 macOS 辅助功能脚本，会自动使用网页抓取链路。

## 使用流程

1. 打开工作台。
2. 进入“抖音数据抓取”。
3. 粘贴抖音 App 里复制的博主主页分享链接。
4. 点击“抓取这个博主”。
5. 回到“发布规划”，查看未来 7 天发布指导和涨粉/信任感操作清单。

## 文件说明

- `scripts/start_agent.py`：跨系统启动入口。
- `scripts/serve_workflow_app.py`：本地智能体服务。
- `scripts/build_workflow_app.py`：生成可视化工作台页面。
- `scripts/cleanup_media_cache.py`：清理临时视频缓存，打包前用于瘦身。
- `data/`：本地抓取数据与配置。
- `output/workflow_app/`：网页工作台。

## 打包前瘦身

智能体默认只长期保存作品文案、转写稿、分析结果和网页工作台。原始视频只作为临时中转文件，转写完成后会自动删除。

如果你要把整个智能体复制到另一台电脑，建议先运行：

macOS / Linux:

```bash
.venv/bin/python scripts/cleanup_media_cache.py
```

Windows:

```powershell
.\.venv\Scripts\python.exe scripts\cleanup_media_cache.py
```

这个命令会清理：

- `data/media/`
- `data/tmp_media/`
- 详情数据里的临时 `media_path`

不会删除：

- 作品文案
- 转写稿
- 复盘分析
- 发布规划
- 本地工作台页面

## 生成跨电脑轻量包

直接运行：

```bash
.venv/bin/python scripts/package_agent.py
```

Windows:

```powershell
.\.venv\Scripts\python.exe scripts\package_agent.py
```

生成的压缩包会放在：

```text
dist/
```

轻量包会自动排除：

- `.git/`
- `.venv/`
- `data/media/`
- `data/tmp_media/`
- `data/browser_profile/`
- 抖音接口缓存和原始视频缓存

这样复制到新电脑时体积更小。新电脑首次启动时，运行启动脚本会重新安装依赖。

## 注意

抖音网页端可能因为登录、风控、公开权限而不给完整作品列表。智能体现在有作者归属校验：抓不到目标作者作品时会失败保护，不会把推荐流或热门链接误写进作品库。
