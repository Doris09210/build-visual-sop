---
name: build-visual-sop
description: "把编号截图与文字步骤制作成隐私安全的可视化 SOP：不可逆像素遮挡、操作标注、内嵌图片、滚动目录、键盘大图查看和单文件离线 HTML；具备浏览器导出环境时生成 PDF。"
---

# 可视化操作手册

使用本包 `scripts/` 中的固定版本脚本，不在运行时下载 main 分支代码。HTML 生成需要 Python 3.10+、Pillow 和中文字体；安装及 PDF 的额外依赖见 [README.md](README.md)。没有执行环境时只能提供步骤整理与 manifest 草稿，不能声称生成或验证了文件。

## 流程

1. 清点、按编号逐张查看原图，与文字步骤对应；保留原图，不覆盖。
2. 读取 [manifest 结构](references/manifest-schema.md)，建立 UTF-8 JSON。坐标是原图像素 `[left, top, right, bottom]`，必须在界内。不要未经检查就猜点击位置。
3. 有联系人、聊天、账号或二维码时，读取 [隐私标准](references/privacy-redaction.md)。按照用户已明确允许保留的信息决定遮挡区域；其余敏感信息保守处理。公共品牌或理解操作所必需的非敏感 UI 不必机械遮挡。
4. 对每张图在原始分辨率上先做不透明像素遮挡，再加红色操作框、绿色完成框。遮挡区域必须完整包住敏感信息和边缘；不可依赖 CSS、透明遮罩、模糊或弱马赛克。脚本不自动检测隐私，manifest 中遗漏的区域不会自动隐藏。
5. 用本地脚本构建 HTML。只有处理后的光栅图片进入 HTML；原图、敏感 manifest 或中间目录不随最终手册默认分享。
6. 运行结构校验，再打开处理图和页面检查隐私、标注、步骤顺序、移动端布局、目录高亮、大图的 Enter/Tab/Escape 操作。校验器不等于隐私识别或视觉检查。
7. 需要 PDF 时按 README 的导出命令从已验证 HTML 生成，检查页数与逐页排版；环境缺失则交 HTML 并明确 PDF 尚未生成。

## 命令

在技能目录运行；Windows 可用 `py -3` 或 Python 完整路径替换 `python`，macOS/Linux 可用 `python3`。路径含空格时加引号。

```text
python scripts/build_visual_sop.py manifest.json --output output/SOP.html
python scripts/validate_visual_sop.py output/SOP.html --manifest manifest.json
python scripts/test_visual_sop.py
```

## 设计与检查

默认浅色、响应式、单文件 HTML；多份 SOP 一节一份，除非用户要求分开。按源图顺序、一图一步；重复使用截图时分别设置标注。标签不能遮住控件、其他标注或关键结果；脚本无法自动理解 UI，发现碰撞需调整标注内容/框，或在步骤文字里解释。

长页目录须随滚动高亮当前步骤，并设置 `aria-current="step"`；只滚动侧栏自身来保持当前项可见。大图使用模态对话框，关闭后恢复触发按钮焦点。所有图片内嵌，无外部字体或网络请求；首次安装依赖需要联网，依赖安装完成后构建和浏览可离线。

对每张敏感图全尺寸复核。搜索用户提供的敏感串是否误入标题、说明或 HTML（不要把敏感串写入测试日志）；解码内嵌图片检查像素遮挡。工具不能证明不存在未发现的隐私，因此报告实际审查范围。

交付真实 HTML/PDF 文件链接和节数、步骤数、内嵌图片数、manifest 遮挡数；区分“框数”与隐私覆盖是否经人工确认。不可把未生成的 PDF、未执行的渲染检查或草稿路径报告为成品。
