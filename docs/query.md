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

- index，作名词相当于关系型数据库的表；作动词相当于解析文档，创建索引
- search，搜索阶段
- store，在ES中有时特指store字段，另存一份；有时是指普通的存储。

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
      "_source": {
      	"excludes": {
      		"*vector"
      	}
      },
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

对存在检索关键词的结果字段添加特殊标签。es支持三种Highlighter。

- Unified highlighter，默认的，底层使用Lucene Unified Highlighter，切句分词后BM25评分。
- Plain highlighter，使用Standard Luncene Highlighter，通过关键字的重要性及关键字的位置信息，尝试尽量的体现查询的匹配逻辑。Plain Highlighter需要针对具体的查询和命中文档的每个字段进行实时的计算，其会在内存中创建一个小型的index，然后通过查询计划重新执行一遍查询，从而获得高亮需要使用底层的匹配信息，所以其比较适合小型的字段。
- Fast vector highlighter，使用Lucene Fast Vector highlighter，需要设置term_vector为with_position_offsets，会占用更多存储空间，适合多字段、大字段的高亮。不支持span查询。

既然需要高亮指定的句子短语，highlighter需要知道每个词的起始字符位置，有以下几种方式。

- 索引时分析文本的结果。如果mapping中index_options设置为offsets，unfied highlighter使用这些信息完成高亮而不用再次使用分析器分析文本。它会在预先分析的结果上再次运行查询并从索引中匹配字符偏移。对于大字段来说，不需要重新分析文本是很有意义的，同时相比于term_vector占用更小的磁盘空间。

- Term vector。如果term_vector参数设置为with_positions_offsets，unified highlighter会自动使用这些信息高亮字段，因为可以直接访问到每个文档的词典，所以能提高大字段(1MB以上)和muti-term查询比如prefix或者wildcard的高亮速度。Fast vector highlighter只能使用term vector。

- Plain highlighter，当其他highlighter不能用时会使用这个，对于大文本会很耗时间和内存。

  Highlighter是怎么工作的？对于一个查询，highlighter需要找到最佳的文本片段并且高亮目标词句，这里所指的片段是指一个词、多个词或者词句，这必须解决以下三个问题。

  - 如何将文本切片？

    Plain highlighter基于给定的分析器分词，然后遍历每一个词并添加到片段中，当片段将要超过最大fragment_size时，创建新的片段。如果分词不恰当，比如标点符号被单独分出或词以标点符号开头，可能会导致某个片段以标点符号开始。

    Unified或者FVH highlighter使用Java的BreakIterator进行切片，在允许的片段大小下，尽量保证词句的完整性。

    相关的配置选项`fragment_size`, `fragmenter`, `type`, `boundary_chars`, `boundary_max_scan`, `boundary_scanner`, `boundary_scanner_locale`。

  - 如何找到最佳的片段？

    三者都是在给定的查询上对片段进行评分，但是评分计算方式不同。

    Plaing highlighter会在内存中为分词结果重新创建一个索引并执行Lunene的查询并计算得分。片段中每出现一个查询的term，片段的得分加1（boost决定，默认是1）,每个片段的每个term只会被计算一次。

    FVH既不需要对文本进行分析，也不需要重新执行查询，而是term_vector的结果，进行切片，按照和Plain highlighter类似的方式计算片段得分，不同的是每个片段的term可以被计算多次。

    Unified highlighter可以使用term_vector或者index_options配置的term_offsets，如果这两者不可用，将会使用Plain highlighter的方式在内存中建立索引并再次进行查询。Unified highlighter使用BM25算法j评分。

  - 如何高亮片段中的词句？

    [How to highlight the query terms in a fragment?](https://www.elastic.co/guide/en/elasticsearch/reference/8.11/highlighting.html#_how_to_highlight_the_query_terms_in_a_fragment)

### [async异步搜索](https://blog.csdn.net/UbuntuTouch/article/details/107868114)

支持异步查询，可使用 [get async search](https://www.elastic.co/guide/en/elasticsearch/reference/8.11/async-search.html#get-async-search)查看检索的运行状态。

### [near real-time近实时搜索](https://doc.yonyoucloud.com/doc/mastering-elasticsearch/chapter-3/34_README.html)

添加或更新文档不修改旧的索引文件，写新文件到缓存，延迟刷盘，可通过API强制更新索引。

### pagination分页

普通分页，深度分页scroll，search after。

### [inner hits不同阶段文档命中](https://www.jianshu.com/p/0d6488a8072b)

搜索嵌套对象或Join检索、字段折叠等情况下，可以查出具体每个阶段的文档。

例如字段折叠，inner_hits可以查询出折叠每个分组下具体有哪些文档。

支持name、sort、from、size参数。

### selected field返回需要的字段

使用_source filter、fileds、docvalue_fields、stored_fields返回需要的文档字段。

### across clusters分布式检索

支持多种检索API的分布式搜索。

### multiple indices多索引检索

支持同时从一次从多个索引检索数据。

### shard routing分片路由

ES将索引分片并可以重复保存在多个节点上，可以提高容错和检索能力。默认情况下ES自动根据负载情况、响应时间选择合适的节点查询。在查询中可以配置preference优先去哪个节点查询，可以配置routing指定分片查询，可以配置每个节点同时并发检索的分片数。

### 自定义检索模板search templates

复用的检索模板，根据不同变量生成不同query dsl，Mustache语法。

### 同义词检索search with synonyms

定义同义词集，在索引和检索阶段可以被文本分析器中的tokenfilter使用，提高检索准确度。ES中提供了三种方法配置同义词

- 使用[synonyms APIs](https://www.elastic.co/guide/en/elasticsearch/reference/current/synonyms-apis.html)，可以动态灵活的定义和修改同义词集。使用这种方法修改同义词集后文本分析器会被自动重新加载，使用这种方法同义词替换只能用在搜索阶段。
- 使用文件方式，在每个节点上（相对于ES配置目录）放置同义词文件，在每个节点上更新文件后，需要手动调用[reload search analyzers API](https://www.elastic.co/guide/en/elasticsearch/reference/current/indices-reload-analyzers.html)
- 直接在tokenfiler定义时指定，不推荐。

以下是同义词文件示例

```text
# 左边的词在tokenfilter会被替换为右边的词
i-pod, i pod => ipod
sea biscuit, sea biscit => seabiscuit

# 取决于同义词的expand配置
ipod, i-pod, i pod
foozball , foosball
universe , cosmos
lol, laughing out loud

# expand为true的情况（默认），左边任意一个词会被替换为右边三个词
ipod, i-pod, i pod => ipod, i-pod, i pod
# expand为false，相当于左边任意三个词替换为右边一个词
ipod, i-pod, i pod => ipod

# 以下两行配置
foo => foo bar
foo => baz
# 相当于下面一行配置
foo => foo bar, baz
```

何时使用同义词替换

- 索引阶段，也就是说分词之后tokenfilter进行同义词替换，然后建立索引，如果同义词更新，需要重建索引。

- 搜索阶段，同义词替换只发生在搜索阶段，同义词库文件变化不需要重建索引。

  通过配置analyzer和search_analyzer指定何时使用同义词替换。

### 排序sort results

支持多字段，数组字段、嵌套字段排序，对于数组的排序，可以选择数组的最大值、最小值、平均值等作为排序依据。对一个字段指定排序后，不再计算评分，除非指定track_score。

- [最邻近搜索knn search](https://www.elastic.co/guide/en/elasticsearch/reference/current/knn-search.html)，检索最邻近的向量，常用于相关性排名、搜索建议、图像视频检索。

- [语义检索semantic search](https://www.elastic.co/guide/en/elasticsearch/reference/current/semantic-search.html)，按语义和意图检索，而不是词汇检索，基于NLP和向量检索，支持上传模型，在存储和检索时自动编码，支持混合检索。

  所有的检索特性可以查看[官方文档](https://www.elastic.co/guide/en/elasticsearch/reference/current/search-your-data.html)

## 查询

### query和filter

query用于回答相似度是多少的问题，计算评分。

filter用于回答是或否的问题，不计算评分，可使用缓存，效率更高

### 组合查询

#### Boolean

#### Boosting

- match，最常用，分词，全文检索。

- match_phrase，与match类似，**但是索引分词和查询分词结果必须相同，包括分词得到的顺序**，可配置参数slop，允许词和词之间出现其他token的数量。

  本人在ik分词测试，需要将analyzer和search_quote_analyzer设置成一样的分词器，才能正确检索出结果。

  match_phrase容易受到停用的影响，不配置ik的停用词影响match搜索，配置之后影响match_phrase，本人使用ik的tokenizer自定义analyzer，但是
  **ik的tokenizer就完成了中文标点去除、停用词去除以及分词的功能**，无法配置其仅完成分词，需要修改源码。
