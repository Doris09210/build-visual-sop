from pathlib import Path
import base64, copy, hashlib, io, json, tempfile, unittest
from PIL import Image, ImageDraw
import build_visual_sop as b
from validate_visual_sop import validate

class VisualSOPTests(unittest.TestCase):
    def test_redaction_removes_every_pixel_including_corners(self):
        a=Image.new('RGB',(200,200),'red'); c=Image.new('RGB',(200,200),'blue')
        b.redact(a,(20,20,180,180),''); b.redact(c,(20,20,180,180),'')
        self.assertEqual(a.crop((20,20,181,181)).tobytes(),c.crop((20,20,181,181)).tobytes())
    def test_embedded_output_independent_of_secret(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); step={'source':'source.png','redactions':[{'box':[30,30,170,170],'label':''}]}
            results=[]
            for color in ('red','blue'):
                image=Image.new('RGB',(300,300),'white'); ImageDraw.Draw(image).rectangle((30,30,170,170),fill=color); image.save(root/'source.png')
                before=hashlib.sha256((root/'source.png').read_bytes()).hexdigest()
                results.append(b.process(step,root,920,88)[0])
                self.assertEqual(before,hashlib.sha256((root/'source.png').read_bytes()).hexdigest())
            self.assertEqual(*results)
    def test_reject_invalid_boxes(self):
        im=Image.new('RGB',(100,100))
        for box in ([-1,0,20,20],[0,0,101,20],[0,0,0,20],[0.5,0,20,20]):
            with self.assertRaises(ValueError): b.box(box,im)
    def test_html_escape_counts_and_broken_image(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); Image.new('RGB',(300,300),'white').save(root/'source.png')
            m={'title':'<script>alert(1)</script>','sections':[{'id':'lightbox','title':'Example','steps':[{'source':'source.png','title':'A & B'}]}]}
            content,stats=b.build(m,root,920,88); target=root/'out.html'; target.write_text(content,encoding='utf-8')
            self.assertNotIn('<script>alert(1)',content); self.assertEqual(stats['steps'],1); self.assertTrue(validate(target)['valid'])
            target.write_text(content.replace('data:image/jpeg;base64,','https://example.invalid/'),encoding='utf-8')
            self.assertFalse(validate(target)['valid'])
    def test_empty_and_duplicate_sections_fail(self):
        for m in ({'title':'X','sections':[]},{'title':'X','sections':[{'id':'a'},{'id':'a'}]}):
            with self.assertRaises(ValueError): b.build(m,Path('.'),920,88)
if __name__=='__main__': unittest.main()
