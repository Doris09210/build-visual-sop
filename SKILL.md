---
name: build-visual-sop
description: Create polished, privacy-safe visual SOPs from numbered screenshots and written procedures. Use when Codex needs to turn app or website screenshots into annotated step-by-step SOP webpages or PDFs; mark click targets; irreversibly redact contacts, messages, avatars, QR codes, account details, or other sensitive content; combine multiple SOPs; embed images into one offline HTML file; or build a long SOP with a sticky directory that automatically highlights the currently viewed step.
---

# Build Visual SOP

Create a shareable visual SOP from screenshots while preserving UI fidelity and privacy.

## Required workflow

1. Inventory all screenshots with `rg --files`; preserve originals.
2. Inspect every screenshot in order and map it to the user's written procedure.
3. Create a step manifest. Read [references/manifest-schema.md](references/manifest-schema.md) before authoring it.
4. Audit privacy before annotation. Read [references/privacy-redaction.md](references/privacy-redaction.md) whenever screenshots contain people, contacts, chats, account data, QR codes, or unrelated organizations.
5. Apply irreversible raster redactions first; add action boxes and verification highlights second.
6. Build a light-theme, responsive, single-file HTML using `scripts/build_visual_sop.py`.
7. Validate with `scripts/validate_visual_sop.py` and visually inspect privacy-critical and representative steps.
8. Deliver the final HTML with a direct file link and report section, step, embedded-image, and redaction counts.

## Default output rules

- Produce one offline HTML file with every processed image embedded as a Base64 data URL.
- Use a unified cover, SOP section headers, completion outcomes, sticky directory, and large-image viewer.
- For multiple SOPs, merge them into one document unless the user requests separate files.
- Use a light visual theme unless the user specifies otherwise.
- Keep screenshot order aligned with the user's numbering.
- Preserve original screenshots; write processed artifacts to a separate output or temporary directory.
- Prefer deterministic PIL drawing for UI screenshots. Do not generatively redraw interfaces unless explicitly requested.

## Annotation language

- Red: required click, tap, input, confirmation, or selection.
- Green: completed state or expected result.
- Dark diagonal mask: privacy information removed.
- Number actions continuously within each SOP. Keep step titles concise and imperative.
- Place labels so they do not cover the target control or essential UI context.

## Privacy requirements

- Mask at native resolution before resizing or JPEG encoding.
- Use opaque fills or patterned masks; never rely on CSS blur, transparency, pixelation, or a removable overlay.
- Mask full contact lists, private chat threads, personal backgrounds, direct identifiers, credentials, QR codes, and unrelated organizations unless the user explicitly whitelists them.
- Preserve only the minimum context needed to understand the operation.
- Re-open every privacy-critical processed image before delivery.

## Directory current-position behavior

The long-page directory must track scrolling:

- Highlight the link for the step crossing roughly the upper third of the viewport.
- Set `aria-current="step"` on the active link.
- Highlight the active SOP group separately.
- Keep the active directory item visible by adjusting the sidebar's own scroll position; do not move the document scroll position.
- Update on initial load, scrolling, resizing, hash navigation, and near-page-bottom state.
- Use `.active` and `.section-active` CSS states with obvious contrast.

Do not ship a long SOP without this scroll-spy behavior.

## Running the bundled builder

```powershell
python scripts/build_visual_sop.py manifest.json --output output/SOP.html
python scripts/validate_visual_sop.py output/SOP.html --manifest manifest.json
```

If `python` is unavailable, locate and use the workspace's bundled Python runtime. Install Pillow only when absent and only with appropriate approval.

## Quality gate

Confirm all of the following:

- Every written procedure step appears once and in the right order.
- Every action box points to the intended control.
- Every sensitive region is irreversibly masked in the embedded raster image.
- All images use `data:` URLs and no external image path remains.
- Directory links resolve and current-position highlighting is present.
- Mobile layout remains readable and lightbox controls are keyboard accessible.
- Section count, step count, and embedded-image count match the manifest.

For a PDF request, create and validate the HTML first, then use the PDF workflow to render it. Keep the HTML as the editable source of truth.
