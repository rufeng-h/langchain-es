import json
import os.path
import re
from pathlib import Path

from sentence_transformers import SentenceTransformer

from schemas import Book

text = Path(os.path.join(os.path.dirname(__file__), 'bookdata.txt')).read_text(encoding='utf-8')
text = re.sub(r'([\u4e00-\u9fa5])"([\u4e00-\u9fa5，\d、？！：《》（）。]+)"', r'\1“\2”', text)
it = iter(text.splitlines())
ls = []
for _, item in zip(it, it):
    ls.append(Book(**json.loads(item)))

sentences_1 = ["样例数据-1", "样例数据-2"]
sentences_2 = ["样例数据-3", "样例数据-4"]
model = SentenceTransformer('BAAI/bge-large-zh-v1.5')
embeddings_1 = model.encode(sentences_1, normalize_embeddings=True)
embeddings_2 = model.encode(sentences_2, normalize_embeddings=True)
similarity = embeddings_1 @ embeddings_2.T
print(similarity)

