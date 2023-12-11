import os
from pathlib import Path

stopword_path = 'stopword'
s = set()
for f in os.listdir(stopword_path):
    filepath = os.path.join(stopword_path, f)
    s.update(set(Path(filepath).read_text(encoding='utf-8').splitlines()))

Path(os.path.join(stopword_path, 'ext_stopword.dic')).write_text('\n'.join(s), encoding='utf-8')
