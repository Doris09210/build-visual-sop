# Manifest schema

Use UTF-8 JSON. Resolve every `source` path relative to the manifest file unless it is absolute.

```json
{
  "title": "企业微信基础设置",
  "subtitle": "完整图示操作指南",
  "theme": "light",
  "output_name": "完整SOP.html",
  "sections": [
    {
      "id": "sop1",
      "number": "SOP 01",
      "title": "允许别人找到我的企业身份",
      "subtitle": "打开联系人权限。",
      "outcome": "目标开关显示为开启状态。",
      "steps": [
        {
          "source": "screenshots/1.png",
          "title": "选择企业并进入设置",
          "instruction": "选中目标企业，点击设置。",
          "check": "目标企业右侧出现勾选。",
          "redactions": [
            {"box": [40, 100, 240, 220], "label": "个人信息已隐藏"}
          ],
          "actions": [
            {"number": 1, "label": "选择目标企业", "box": [20, 840, 490, 950]},
            {"number": 2, "label": "点击设置", "box": [20, 1130, 210, 1230]}
          ],
          "highlights": [
            {"box": [450, 850, 540, 940], "label": "已选中"}
          ]
        }
      ]
    }
  ]
}
```

## Coordinates

- Use `[left, top, right, bottom]` in source-image pixels.
- Inspect the original dimensions before writing boxes.
- Keep boxes inside the image bounds.
- Include enough padding for borders without covering adjacent controls.

## Field rules

- `title`, `sections`, `steps`, and each step's `source` and `title` are required.
- `id` must be unique and safe for an HTML fragment identifier.
- `number` is user-facing; use `SOP 01`, `SOP 02`, and so on.
- `instruction` describes what to do; `check` describes the visible success state.
- `redactions` are applied before `actions` and `highlights`.
- `actions.number` may restart within each SOP.
- `theme` currently supports `light`; treat it as the default.

## Multi-SOP guidance

- Keep all sections in one manifest to produce a merged document.
- Use one section per SOP and one screenshot per step unless a single screenshot clearly contains multiple sequential actions.
- When screenshots are reused, repeat the step with a distinct title and annotation set rather than linking to the same DOM card.
