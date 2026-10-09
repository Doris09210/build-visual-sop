# Privacy redaction standard

## Decision order

1. Identify user-approved information that may remain visible.
2. Treat unapproved personal identifiers, private accounts, conversations, internal organizations and access credentials as private. Public branding or non-sensitive UI needed to explain the operation may remain visible.
3. Redact before resizing, compression, annotation, or Base64 embedding.
4. Re-open the processed image and verify that no original pixels remain visible.

## Always redact unless explicitly approved

- Personal names, faces, avatars, phone numbers, email addresses, IDs, account handles, and location details.
- Contact lists, search results containing people, group rosters, customer lists, and notification counts tied to private workspaces.
- Private messages, informal or inappropriate chat content, message previews, and conversation backgrounds.
- QR codes, barcodes, invite links, tokens, credentials, verification codes, and scannable identity artifacts.
- Unrelated enterprise names, internal team names, project names, departments, and confidential status text.
- Information after a user-specified cutoff, such as all messages after an enterprise card.

## Redaction method

- Draw an opaque dark rectangle over the entire sensitive area, including all four corners. Do not use rounded corners that retain source pixels.
- Add diagonal stripes and a neutral label such as `联系人列表已隐藏` when useful.
- Expand the box slightly beyond text or image edges to prevent halos.
- For a list, mask the whole data column rather than many narrow text fragments. Preserve action buttons only when they are necessary to explain the step.
- For a chat, preserve only approved bubbles or cards; mask the header identity, background, avatars, and all other conversation content.
- For QR codes, cover the entire quiet zone as well as the code.

## Prohibited methods

- CSS blur, opacity, overlay elements, hover masks, or anything removable in browser developer tools.
- Weak pixelation or blur that may be reconstructed or read by OCR.
- Cropping that leaves partial names, faces, phone-number suffixes, or message fragments.
- Embedding unredacted source images elsewhere in the final HTML.

## Final audit

- Inspect every contact-list and chat screenshot at full size.
- Confirm that the final HTML contains only processed images.
- Search the HTML for sensitive literal strings when the user named them.
- Count redactions from the manifest and report the result.

