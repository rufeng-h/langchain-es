# Text-Analysis

文本处理是在index和search阶段对文本数据的处理，包括去除无效字符、分词、替换等操作。

## 分析器

一个完整的分析器Analyzer由三种组件组成，代表了es文本处理的三个阶段。

1. 字符过滤器Character filter

   文本处理的第一阶段，进行前置处理，可以对字符进行添加、去除、替换等操作。一个分析器可以包含零个或多个字符过滤器。es默认提供了三个字符过滤器。

   - HTML strip，去除html标签
   - Mapping，字符替换，例如将罗马数字替换为阿拉伯数字，替换的映射表支持文件路径和写在json串的形式。
   - Pattern replace，正则表达式替换。

2. 分词器Tokenizer

   第二阶段分词，并且需要以下几点要求

   - 分词每个词后的顺序、位置需要保证。
   - 分词每个词在源文本中的起始位置。
   - 得到的词标记类型，比如数字、字母等。

   es提供了一系列分词器，但都不支持中文。一个分析器有且只能有一个分词器。

3. 词过滤器Token filter

   第三阶段，对得到的词进行过滤，比如去掉一些无意义的词，添加替换同义词等。一个分析器可以包含零个或者多个词过滤器。

## Normalizer

`Normalizer`相当于没有`Tokenizer`的`Analyzer`，或者说不进行任何操作，直接返回的tokenizer（es内置的keyword tokenizer）。仅仅处理文本而不进行分词，某些情况下这对于keyword检索有用，例如检索某些带标点符号或者特殊字符的书名，不分词但需要处理特殊字符（用于不会输入特殊字符），可以用到normalizer。

```
{
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
        }
}
```

## 一些问题

### 默认分析器

如果没有配置分词器，默认使用`stadard analyzer`，由一个`standard tokenizer`和`lower case token filter`、`stop token filter`组成。

**默认的标准分词器会将所有中英文标点去掉并基于Unicode文本分割算法进行分词。**

**ik的两个分词器也会去掉所有标点符号并将文本转化为小写。**

```json
POST /_analyze
{
  "char_filter": [],
  "tokenizer": "standard",
  "filter": [],
  "text": "，你,好！。!！HELLO"
}
# 你，好，HELLO

POST /_analyze
{
  "char_filter": [],
  "tokenizer": "keyword",
  "filter": [],
  "text": "，你,好！。!！HELLO"
}
# ，你,好！。!！HELLO
# keyword不做任何操作直接返回

POST /_analyze
{
  "char_filter": [{
                "type": "pattern_replace",
                "pattern": "[。？！，,、；：“”‘（ ）《》〈〉【】『』「 」﹃﹄ 〔〕.—～﹏￥?!]",
                "replacement": ""
            }],
  "tokenizer": "keyword",
  "filter": [],
  "text": "，你,好！，!！HELLO"
}
# 你好HELLO
# 正则表达式替换，去除了所有的标点符号

POST /_analyze
{
  "char_filter": [],
  "tokenizer": "ik_smart",
  "filter": ["uppercase"],
  "text": "HELLO!?>》"
}
# HELLO
```

