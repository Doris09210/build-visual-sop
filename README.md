# build-visual-sop · 可视化操作手册

入口是 [SKILL.md](SKILL.md)。这是供 AI 助手读取并执行的工作流程，不是独立聊天产品。

## 下载与安装

下载本仓库的独立包 `build-visual-sop.zip`（若从 GitHub 下载整个仓库，先解压）。保持 `build-visual-sop/SKILL.md` 及其支持目录在同一文件夹。将该文件夹放入所用助手支持的技能目录；不要再套一层同名目录。

Codex 的个人技能目录通常为 `~/.codex/skills/`；Claude Code 通常为 `~/.claude/skills/`。以安装环境的实际配置为准。支持 ZIP 上传的产品可上传独立包；仅支持文本的产品可以读取 SKILL.md，但需要自行提供引用文件。

## 使用示例

> 使用 examples/manifest.json 生成离线 HTML 和 PDF；检查所有合成身份信息已遮挡，并报告实际验证结果。

## 依赖与失败降级

HTML：Python 3.10+、Pillow、可用的中文字体。PDF：另需 Node.js 18+、Playwright 和 Chromium 或本机 Chrome/Edge。

缺少能力时交付当前能完成的内容，并明确文件未生成、附件未保存或渲染未验证，不提供虚构结果。不能把模型能读懂流程等同于完整运行。

## 兼容与测试边界

Windows / Python 3.12.14 / Pillow 12.3.0：5 项脚本测试通过；合成示例生成、结构校验、桌面/390px 浏览、目录高亮、键盘大图操作通过；Node Playwright + 本机 Edge 导出 4 页 PDF并逐页查看。macOS/Linux 未实机测试。

GPT/ChatGPT、Claude、WorkBuddy、豆包等是否支持自动发现技能、执行脚本、读取附件和交付文件，取决于具体产品与权限；本包不声称这些平台均已实测。文本工作流可供阅读，但完整运行必须满足上述能力。

## 来源与许可

原始说明来自作者提供的 `doris-skills.zip`。经作者授权，本仓库采用 [MIT License](LICENSE)，Copyright (c) 2026 Doris09210。第三方依赖和字体仍适用各自许可证，不因本仓库 MIT 而改变。

脚本基础来自作者同名仓库提交 `e930ddbc20080227ab5617b642fe55bdd01235f0`；保留原参考文件与 agents 元数据。本版修复遮罩角部、输入检查、源文件覆盖保护、标注编号位置和键盘焦点，补充校验、回归测试、打印样式及 PDF 导出。依赖通过各自官方包管理器安装，不随包复制第三方库或字体。

## HTML：各系统安装和运行

先安装 Python 3.10+，在仓库根目录创建独立环境。Windows 用 `py -3`，macOS/Linux 用 `python3`：

```text
# Windows PowerShell（不用激活环境）
py -3 -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements.txt
.venv/Scripts/python.exe scripts/build_visual_sop.py examples/manifest.json --output output/SOP.html
.venv/Scripts/python.exe scripts/validate_visual_sop.py output/SOP.html --manifest examples/manifest.json
.venv/Scripts/python.exe scripts/test_visual_sop.py

# macOS / Linux
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python scripts/build_visual_sop.py examples/manifest.json --output output/SOP.html
.venv/bin/python scripts/validate_visual_sop.py output/SOP.html --manifest examples/manifest.json
.venv/bin/python scripts/test_visual_sop.py
```

Windows 默认搜索微软雅黑/黑体，macOS 搜索 PingFang/STHeiti，Linux 搜索 Noto Sans CJK；缺少时安装相应字体，或将 `SOP_FONT` 指向实际的中文 TTF/TTC 文件。PowerShell 用 `$env:SOP_FONT='字体完整路径'`，macOS/Linux 用 `export SOP_FONT='字体完整路径'`。未发现中文字体会停止并给出提示，不用缺字字体悄悄替换。

## PDF：可选依赖与命令

```text
npm install playwright
npx playwright install chromium
node scripts/export_pdf.cjs output/SOP.html output/SOP.pdf
```

若已有 Chrome/Edge，可跳过浏览器下载并提供第三个参数：

```text
node scripts/export_pdf.cjs output/SOP.html output/SOP.pdf "C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe"
```

macOS/Linux 同样可传本机浏览器的真实可执行路径。Linux Chromium 还需系统运行库，按 Playwright 官方安装提示配置，不假设具有管理员权限。临时目录不可写时，将 TMP/TEMP 指向当前有权限的工作目录。

首次安装依赖/浏览器需联网；离线机器应提前在受信任环境准备相应系统的依赖。安装完成后 HTML 构建、PDF 导出和 HTML 查看均无需网络。没有 Node/浏览器时仍可生成 HTML，也可由用户在浏览器“打印→另存为 PDF”，但应单独检查打印结果。

## 安全与验证边界

脚本只遮挡 manifest 指定的区域，不自动识别隐私。分享前检查图片以及标题、说明、标签中的敏感文字。校验器检查结构、锚点、内嵌图片和交互标记，不代替目视审查。`examples/` 中所有图片都是合成测试界面，可安全用于演示。
