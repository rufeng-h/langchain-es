"""
@time    : 2023/12/11 16:25
@author  : chunf
"""
import hashlib
import json
from pathlib import Path
from typing import List
from sentence_transformers import SentenceTransformer

from elasticsearch import Elasticsearch
from pydantic import TypeAdapter

from schemas import Book

es_client = Elasticsearch("http://localhost:9200")

index_name = 'book'

model = SentenceTransformer('D:/models/bge-large-zh-v1.5')

if es_client.indices.exists(index=index_name):
    es_client.indices.delete(index=index_name)

settings = {
    "analysis": {
        "analyzer": {
            "ik_smart_no_stop": {
                "type": "custom",
                "tokenizer": "ik_smart",
                "filter": [],
            },
            "ik_max_word_no_stop": {
                "type": "custom",
                "filter": [],
                "tokenizer": "ik_max_word",
            },

        },
        "normalizer": {
            "punctuation_normalizer": {
                "type": "custom",
                "char_filter": "punctuation_char_filter"
            }
        },
        "char_filter": {
            "punctuation_char_filter": {
                "type": "pattern_replace",
                "pattern": "[。？！，、；：“”‘（ ）《》〈〉【】『』「 」﹃﹄ 〔〕.—～﹏￥?!]",
                "replacement": "",
            },
            # "punctuation_char_filter": {
            #     "type": "mapping",
            #     "mappings": [
            #         "： =>",
            #     ]
            # }
        },
        # 未使用
        "filter": {
            "punctuation_stop": {
                # "stopwords_path":"",
                "type": "stop",
                "stopwords": ['。', '？', '！', '，', '、', '；', '：', '“', '”', '‘', '（ ', '）', '《', '》', '〈', '〉',
                              '【', '】', '『', '』', '「 ', '」', '﹃', '﹄ ', '〔', '〕', '.', '—', '～', '﹏', '￥',
                              # 英文
                              '?', '!', ]
            }
        }
    }
}

mappings = {
    "_source": {
        "excludes": ["*vector"]
    },
    "properties": {
        "name": {
            "type": "text",
            "analyzer": "ik_max_word",
            "search_quote_analyzer": "ik_smart_no_stop",
            "search_analyzer": "ik_smart",
            "copy_to": "all",
            "fields": {
                "keyword": {
                    "type": "keyword",
                    # "normalizer": "punctuation_normalizer"
                }
            }
        },
        "meta": {
            "doc_values": False,
            "norms": False,
            "type": "keyword",
            "normalizer": "punctuation_normalizer"
        },
        "publish": {
            "type": "keyword",
            "doc_values": False,
            "norms": False,
            "normalizer": "punctuation_normalizer",
            "copy_to": "meta",
        },
        "type": {
            "type": "keyword",
            "normalizer": "punctuation_normalizer",
            "doc_values": False,
            "norms": False,
            "copy_to": "meta",
        },
        "author": {
            "norms": False,
            "type": "text",
            "analyzer": "ik_max_word",
            "search_quote_analyzer": "ik_smart_no_stop",
            "search_analyzer": "ik_smart",
            "copy_to": "all",
        },
        "info": {
            "type": "text",
            "copy_to": "all",
            "analyzer": "ik_max_word",
            "search_analyzer": "ik_smart",
            "search_quote_analyzer": "ik_smart_no_stop"
        },
        "all": {
            "norms": False,
            "type": "text",
            "analyzer": "ik_max_word",
            "search_analyzer": "ik_smart",
            "search_quote_analyzer": "ik_smart_no_stop"
        },
        "info_vector": {
            "type": "dense_vector",
            "dims": 1024,
            "index": True,
            "similarity": "dot_product"
        }
    }
}

es_client.indices.create(index=index_name, mappings=mappings, settings=settings)

books = json.loads(Path('./book.json').read_text(encoding='utf-8'))
books: List[Book] = TypeAdapter(List[Book]).validate_python(books)

operations = []

for book in books:
    operations.append({"create": {"_index": index_name, "_id": hashlib.md5(book.name.encode()).hexdigest()}})
    doc = book.model_dump()
    doc['info_vector'] = model.encode(book.info, normalize_embeddings=True)
    operations.append(doc)

es_client.bulk(index=index_name, operations=operations)
