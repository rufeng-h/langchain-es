## 相关概念

- index，索引，文档的集合，相当于关系型数据库的表（Table），包含表结构（mapping）和表配置（setting）两个选项。
- mapping，表结构，每个字段的数据类型相关配置。
- doc，文档，每个文档（Document）相当于关系型数据库中的行（Row），文档的字段（Field）相当于数据库中的列（Column）。
- Inverted index，倒排索引，先对文档进行分词，词条记录对应文档信息，查询时通过词条定位到文档。
- analyzer，分词器，将文本拆分成词条，对于英文，可直接按照空格拆分，默认情况下中文会按每个字拆分，支持中文分词需要安装插件。es中分词器的组合包含三个部分
    - character filters，字符过滤器，在分词之前对文本进行处理，例如删除停用词，替换字符等。
    - tokenizer，将文本切分成词条（term）。
    - tokenizer filters，进一步处理分词结果，例如大小写转换，同义词替换等。

## filter和query

filter不贡献评分，查询目标是判定是或者否，还可以使用缓存，效率更高。

query计算评分，查询目标是判定相关性，效率比filter低。

### index、search和store

### store、_source和doc_values

关于三者各自的作用可以查看我的另一篇文章。

我们可以将es对数据的存储查询过程分为三个阶段，索引index，查询search，取回fetch。

index阶段，es解析源文档，按照mapping配置、字段配置对字段进行索引，将整个源文档存储（如果没有禁用_source），将指定的字段进行store,另外存储一份（如果store设置为true），对指定字段建立doc_values存储（如果doc_values可用）。

search阶段，解析query dsl，通过通过索引或者doc_values对字段进行检索和过滤，找到符合条件的文档id，**对于需要聚合计算的，取出文档并进行计算？**

fetch阶段，按需返回指定的字段，指定_source，fields，或者docvalue_fields，这三个对应三个不同的存储位置，三者存在的作用也不同。

### fields、_source、stored_fields、docvalue_fields

这四个都是获取自己想要的字段，通常情况下，es推荐的是使用fields。

fields和_source filter差不多，但是fields会从\_source取出相应的字段数据并按照mapping设置进行一些格式处理、运行时字段计算等。

stored_fields是取出被store的字段，通常不建议使用。

docvalue_fields是取出建立了doc_values的字段，部分类型不支持。



## 检索特性

### [collapse字段折叠](https://blog.csdn.net/ZYC88888/article/details/83023143)

按照特定的字段分组，每组均返回结果，例如搜索手机，每个品牌都想看看，按品牌字段折叠，返回每个品牌的可排序、过滤的数据。

```text
GET /book/_search
{
  "size": 5,
  "_source": false,
  "query": {
    "match": {
      "info": "化学"
    }
  },
  "collapse": {
    "field": "publish",
    "inner_hits": {
      "name": "test",
      "size": 2,
      "from": 2
    }
  }
}
```

### [filter过滤](https://juejin.cn/post/7073820135873576997)

有两种使用filter的方式

- 使用带filter的bool查询，filter会在检索和聚合之前生效。

- 直接使用post_filter查询，对检索无影响，在聚合之后生效，可以使用[rescore](https://www.elastic.co/guide/en/elasticsearch/reference/8.11/filter-search-results.html#rescore)提高检索的相关性。

  rescore在所有分片上对query和post_filter的top-k个结果进行算分，可以调整top-k，原score权重，rescore权重，原score和rescore的计算方式（加减乘除平均）。

### [highlight高亮]()

对存在检索关键词的结果字段添加特殊标签。

- [async异步搜索](https://blog.csdn.net/UbuntuTouch/article/details/107868114)，检索大量数据，可查看检索的运行状态。

- [near real-time近实时搜索](https://doc.yonyoucloud.com/doc/mastering-elasticsearch/chapter-3/34_README.html)，添加或更新文档不修改旧的索引文件，写新文件到缓存，延迟刷盘。

- pagination分页，普通分页，深度分页scroll，search after。

  ### [inner hits不同阶段文档命中](https://www.jianshu.com/p/0d6488a8072b)

  搜索嵌套对象或Join检索、字段折叠等情况下，可以查出具体每个阶段的文档。

  例如字段折叠，inner_hits可以查询出折叠每个分组下具体有哪些文档。

  支持name、sort、from、size参数。

- selected field返回需要的字段，使用_source filter、fileds、docvalue_fields、stored_fields返回需要的文档字段。

- across clusters分布式检索，支持多种检索API的分布式搜索。

- multiple indices多索引检索，支持同时从一次从多个索引检索数据。

- shard routing分片路由，自适应分片路由以减少搜索响应时间，可自定义检索哪个节点。

- 自定义检索模板search templates，可复用的检索模板，根据不同变量生成不同query dsl。

- 同义词检索search with synonyms，定义同义词集、过滤器和分词器，提高检索准确度。

- 排序sort results，支持多字段，数组字段、嵌套字段排序，对于数组的排序，可以选择数组的最大值、最小值、平均值等作为排序依据。

- [最邻近搜索knn search](https://www.elastic.co/guide/en/elasticsearch/reference/current/knn-search.html)，检索最邻近的向量，常用于相关性排名、搜索建议、图像视频检索。

- [语义检索semantic search](https://www.elastic.co/guide/en/elasticsearch/reference/current/semantic-search.html)，按语义和意图检索，而不是词汇检索，基于NLP和向量检索，支持上传模型，在存储和检索时自动编码，支持混合检索。

  所有的检索特性可以查看[官方文档](https://www.elastic.co/guide/en/elasticsearch/reference/current/search-your-data.html)

## 查询

- match，最常用，分词，全文检索。

- match_phrase，与match类似，**但是索引分词和查询分词结果必须相同，包括分词得到的顺序**，可配置参数slop，允许词和词之间出现其他token的数量。

  本人在ik分词测试，需要将analyzer和search_quote_analyzer设置成一样的分词器，才能正确检索出结果。

  match_phrase容易受到停用的影响，不配置ik的停用词影响match搜索，配置之后影响match_phrase，本人使用ik的tokenizer自定义analyzer，但是
  **ik的tokenizer就完成了中文标点去除、停用词去除以及分词的功能**，无法配置其仅完成分词，需要修改源码。
