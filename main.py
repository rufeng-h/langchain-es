import json
import os.path
import re
from pathlib import Path
from typing import List

from pydantic import TypeAdapter
from configuration import Configuration

from schemas import Book

text = Path(os.path.join(os.path.dirname(__file__), 'bookdata.txt')).read_text(encoding='utf-8')
text = re.sub(r'([\u4e00-\u9fa5])"([\u4e00-\u9fa5，\d、？！：《》（）。]+)"', r'\1“\2”', text)
it = iter(text.splitlines())
ls = []
for _, item in zip(it, it):
    ls.append(Book(**json.loads(item)))

ta = TypeAdapter(List[Book])

Path(os.path.join(Configuration.BASE_DIR, 'book.json')).write_text(ta.dump_json(ls).decode(), encoding='utf-8')
