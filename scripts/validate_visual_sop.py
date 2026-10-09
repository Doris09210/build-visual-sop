from __future__ import annotations
import argparse
import base64
import io
import json
from html.parser import HTMLParser
from pathlib import Path
from PIL import Image

class Inspector(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids=[]; self.links=[]; self.images=[]; self.resources=[]
        self.cards=0; self.sections=0
    def handle_starttag(self, tag, attrs):
        a=dict(attrs)
        if 'id' in a: self.ids.append(a['id'])
        classes=a.get('class','').split()
        self.cards += 'step-card' in classes
        self.sections += 'sop-head' in classes
        if tag=='a': self.links.append(a.get('href',''))
        if tag=='img' and a.get('id')!='lightboxImg': self.images.append(a.get('src',''))
        if tag in ('script','iframe','link','video','audio','source'):
            self.resources.extend(a[k] for k in ('src','href') if a.get(k))

def validate(path, manifest=None):
    text=Path(path).read_text(encoding='utf-8')
    p=Inspector(); p.feed(text); failures=[]
    if not p.cards: failures.append('No steps')
    if len(p.ids)!=len(set(p.ids)): failures.append('Duplicate HTML ids')
    if any(h.startswith('#') and h[1:] not in p.ids for h in p.links): failures.append('Broken anchor')
    if p.resources: failures.append('External or linked resources present')
    for src in p.images:
        if not src.startswith(('data:image/jpeg;base64,','data:image/png;base64,')):
            failures.append('Non-embedded image'); continue
        try:
            data=base64.b64decode(src.split(',',1)[1],validate=True)
            with Image.open(io.BytesIO(data)) as im: im.verify()
        except Exception: failures.append('Invalid embedded image')
    if len(p.images)!=p.cards: failures.append('Image/step count mismatch')
    for marker in ('aria-current','section-active','setActive','side.scrollTop','showModal','returnFocus'):
        if marker not in text: failures.append('Missing interaction marker: '+marker)
    redactions=None
    if manifest:
        m=json.loads(Path(manifest).read_text(encoding='utf-8-sig'))
        steps=[s for section in m['sections'] for s in section['steps']]
        if p.sections!=len(m['sections']) or p.cards!=len(steps): failures.append('Manifest counts mismatch')
        redactions=sum(len(s.get('redactions',[])) for s in steps)
    return dict(sections=p.sections,steps=p.cards,embedded_images=len(p.images),manifest_redactions=redactions,valid=not failures,failures=failures,scope='Structural checks only; manually review privacy, appearance and interaction.')

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('html',type=Path); ap.add_argument('--manifest',type=Path); a=ap.parse_args()
    result=validate(a.html,a.manifest); print(json.dumps(result,ensure_ascii=False,indent=2))
    raise SystemExit(0 if result['valid'] else 1)
if __name__=='__main__': main()
