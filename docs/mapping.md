## 映射

- 动态映射。无须显示指定文档字段数据类型，直接添加数据即可，es会自动推断数据类型，一般在测试时使用，生产过程避免使用字段推断。

- 显式映射。创建索引时显式指定字段和数据类型。

  索引创建后不能修改字段名（可以添加alias），不能修改数据类型，可以添加新的字段

- 运行时字段。在查询时确定数据类型，由于不会提前索引数据，可以节省存储空间以及提供更灵活的映射操作，但是在部分搜索API中的表现不同，并且由于运行时确定字段，性能上存在一定损失。

### 元数据字段

可以理解为es为每个文档添加的实际存在的字段。

- \_doc_count，桶聚合会返回文档个数doc_count字段，通常情况下这个文档数是正确的，但是对于提前聚合的数据类型，如histogram，aggregate_metric_double等，一个字段可能代表了多个文档，此时聚合时不是加1，而是加文档的\_doc_count值，默认情况下，_doc_count值为1。

- \_filed_names，曾用于记录一个文档中包含非null值的字段，exists查询的时候直接查这个字段即可。

  现在仅用于记录一个文档中doc_values和norms都设置为false的字段，当二者中有任意一个字段可用时，exists查询不会使用\_field_names。

  doc_values被禁用这个字段很可能不用于排序聚合。

  norms被禁用这个字段很可能不用于检索评分。

- \_ignored，记录超出ignore_above或者字段格式不对但ignore_malformed开启的字段。可用于term，terms，exists检索。

- \_id，索引时赋值或者es自动生成，该字段不能进行配置，可用于`term`, `terms`, `match`, `query_string`。最大不能超过512字节。

- \_index，存储索引名，当进行多索引查询时有用。\_index是个虚拟字段，不会真正存到Lucene中，所以不支持`regexp`和`fuzzy` 查询。

- \_meta，自定义的，不被es使用的额外数据信息。比如存储索引的版本、作者、描述信息等。

- \_routing，影响分片的计算，默认的\_routing值是文档id，可以为每个文档指定routing值，也可以在检索时指定routing值。默认的分片路由计算是以下公式

  > ```python
  > routing_factor = index.num_routing_shards / index.num_primary_shards
  > shard_num = (hash(_routing) % index.num_routing_shards) / routing_factor
  > ```

-  \_source，存储原始文档，可以禁用，可以筛选字段。

- \_tier，检索时首选想要的数据等级，例如data_hot，data_warm，data_cold。

### mapping配置

- analyzer，分词器，仅用于text字段，如果不显式指定search_analyzer，将同时应用于索引阶段和检索阶段。

- search_quote_analyzer，phrase查询，不删除停止词。

- coere，数据类型自动转换，比如字符串转整数，浮点数截断为字符串，设置为false，数据类型与字段值类型必须强制符合。可以对字段单独设置，也可以对索引设置。

- copy_to，当需要对多个字段进行检索时（组合条件为或）,可以使用bool查询，但更建议使用copy_to组合字段，既简单又高效。需要注意以下几点
  1. copy过去的是字段值，而不是分词后的term。
  2. copy_to的字段不会包含在_source中，可以理解为仅用于搜索的组合字段。
  3. 同一字段可以copy到多个组合字段中，数组表示即可。
  4. 在目标组合字段未指定类型的情况下，如果dynamic为true，使用自动类型推断；如果dynamic为false，copy_to无效；如果dynamic为strict，则会抛出错误。
  5. copy_to不支持值为对象的数据类型，比如date_range。
  6. copy到组合数据类型的多个字段最好是同一数据类型，保证搜索行为的一致性，copy_to会忽略原字段的数据类型，对组合的所有字段进行同一种数据类型的检索。

- doc_values，倒排索引通过term找doc，完成全文检索功能，而对于文档的排序、聚合等操作需要通过doc找terms。Doc values是一种在索引时建立的磁盘数据结构，列式存储，用于提高排序、聚合的效率，**几乎支持所有的数据类型，除text和annotated_text，这两种类型也不支持聚合操作**。

  数值类型、日期类型、布尔类型、ip类型和geo_point类型、keyword类型即使不被索引，通过doc_values也可以被查询，这里的不被索引是指字段的index设置为false。doc_values的查询会显著慢于索引，但节省空间。doc_values适用于查询较少，聚合统计较多的字段，如果一个字段完全不需要排序统计，可以将doc_values设置为false。

- dynamic，控制es对新增字段的处理，有以下四个选项

  1. true，默认，添加到mapping。
  2. runtime，运行时字段，不被索引，查询时从_source计算加载。
  3. false，新字段不被索引不可查询，但会在_source中出现，不会出现在mapping中。
  4. strict，拒绝新字段，直接抛出异常。

- `eager_global_ordinals`，基于term的数据类型，比如keyword，整个字段就相当于一个term，通过字典序为term分配一个id，顺序存储的是这个id而不是实际的term，并可以通过id查找到term。顺序存储可以提高聚合的效率。

  每个索引段有自己的顺序映射结构，但是聚合操作是在整个分片进行的，所以需要es创建了一个分片级的全局顺序映射(global ordinals)维护分片和索引段之间的关系。

  全局序和[filed data cache](https://www.elastic.co/guide/en/elasticsearch/reference/8.11/modules-fielddata.html)共用堆内存，大量数据的聚合操作会占用大量内存。默认情况下，global ordinals在需要用到后才第一次加载，但是如果对于查询聚合速度有要求，可以将设置为eager，即非懒加载模式。当eager_global_ordinals设置为true，global ordinals永远会在索引可用之前被加载，增大建立索引、分片复制等操作的代价。

  gloabal ordinals为分片上所有的段提供了一个统一的映射，当有新的段到来时，global ordinals必须重建，因为需要保证有序。所以通常情况下global ordinals不会占用太大的内存，但如果一个分片太大或者字段中有大量唯一的term，加载global ordinals是一个昂贵的操作。

  以下操作会用到全局序。

  > - Certain bucket aggregations on `keyword`, `ip`, and `flattened` fields. This includes `terms` aggregations as mentioned above, as well as `composite`, `diversified_sampler`, and `significant_terms`.
  > - Bucket aggregations on `text` fields that require [`fielddata`](https://www.elastic.co/guide/en/elasticsearch/reference/8.11/text.html#fielddata-mapping-param) to be enabled.
  > - Operations on parent and child documents from a `join` field, including `has_child` queries and `parent` aggregations.

  一些情况下可以避免加载global ordinals

  - terms、sampler、significant_terms聚合操作支持`execution_hint`参数来控制对桶的聚集。默认是global_ordinals，可以设置为map，直接使用term而不考虑字典序。
  - 如果一个分片设置了[force-merged](https://www.elastic.co/guide/en/elasticsearch/reference/8.11/indices-forcemerge.html)合并为一个段，那么段级的ordinals就是global ordinals，不需要额外维护。当一个索引不会再被修改后，你可以强制合并为一个段，否则，修改会抛弃原来整个索引段并重建，代价很高。

- enabled，是否会被es解析，索引，只能用于object类型，这能配置在第一层。对于不需要被解析索引的数据，只需要es做存储的，可以配置该选项。

- format，时间格式化，es提供的时间格式化模板很多，也支持自定义。

- ignore_above，超过ignore_above长度的term或者term数组的每个term将不会被index或者store。

  在Lucene中一个term的最大字节数是32766，ignore_above对字符计数，如果使用UTF-8编码存储非ascii字符，假定每个字符占用四个字节，一个term最长是32766/4=8192个字符。

- ignore_malformed，忽略数据类型错误的字段，不抛异常，不对该字段index，正常处理其他字段，支持部分字段。可以通过exists、term等查询结果中的_ignore查看有多少个malformed文档。

- index，是否被索引，数值类型、日期类型、布尔类型、ip类型和geo_point类型、keyword类型即使不被索引，通过doc_values也可以被查询，其他类型index设置为false无法被查询，index和doc_values都设置为false所有数据类型都无法被查询。

- index_options，控制添加哪些额外信息到倒排索引，只有term-based字段可以设置该值，如text、keyword。有以下四个选项。

  1. docs，文档id被索引，可以解决文档是否存在term的查询。
  2. freqs，索引文档id和词频。
  3. positions，默认选项，文档id、词频和term的位置顺序，在match_phrase查询中很有用。
  4. offsets，除以上三个外，还有term的字符起始位置，可以提高[unified highlighter](https://www.elastic.co/guide/en/elasticsearch/reference/8.11/highlighting.html#unified-highlighter)的速度。

  这个选项如果设置为docs应该会影响文档评分？

- index_phrases，两个term的组合会被index称一个额外字段以提高phrase（不带slop）检索的效率。去除停用词会影响检索效果。默认值为false。

  es对中文分词需要插件支持，可能该选项不适合？

  两个term比较符合检索的习惯？

- index_prefixes，对term的前几个字符也进行index以加快prefix检索的效率。

  - min_chars，被index的prefix的最小长度，必须大于0，默认为2。
  - max_chars，被index的prefix的最大长度，必须小于20，默认为5。

- meta，可以添加数据的单位、计算方式等额外共享信息。

- fields，可以理解为字段的子字段，比如一个字段既可以作为text检索，也可以作为keyword排序聚合；一个text字段既使用ik_smart分词，也使用ik_max_word分词。子字段作为一个完全独立的字段存在，不会继承父字段的属性。

  可以为mapping字段添加子字段，但对历史数据无效，需要手动调用update_by_query API。

- normalizer，和analyzer类似，但是保证不会分词，即tokenize阶段只返回一个term的analyzer，对于一些keyword查询，转化小写，去除停用词但是不分词可以配置这个选项，相比于analyzer，不需要配置tokenizer。

- norms，存储用于计算评分的相关信息，但是占用的磁盘空间较多，如果在某个字段上不需要计算评分，比如仅用于过滤或者聚合的字段，应该禁用此属性。

- null_value，默认情况下空值是不可index和search的，可以将空值替换为null_value的值，例如NULL字符串或者-1以支持检索。

- position_increment_gap，当phrase检索多个值时，前一个值的最后一个term和后一个值的第一个term中间的slop数，默认值是100。具体可查看官网例子，比较明了。

- properties，文档字段描述，可以写在mapping第一层，也可以写在字段中。

- search_analyzer，检索时的分词器。

- similarity，相似度评分算法，默认是BM25。

- store，\_source中会把原文档存储一次，某些时候如果想要单独某个字段，需要从\_source中去除整个文档再对进行字段过滤，当存在很大的字段时，取出来是比较耗时的。如果不需要这个很大的字段，只需要部分其他字段时，可以考虑将其他字段设置store，es会将这些字段另外存储一份，查询时设置_source为false，从fields中取出这些字段，避免大字段的读取。

  由于不知道原始字段是单个值还是数组，store后的字段统一返回为数组。

- subobjects，默认情况下x.y.z会被解析为x对象下的y对象的z属性，如果不想要嵌套下去，在字段的第一层设置该属性为false，x.y.z会被解析为x对象的y.z属性。该设置可以对字段和整个mapping设置，配置后无法修改。

- term_vector，保存了analysis分词处理的信息。

  1. 分词的结果。
  2. 分词结果位置顺序信息。
  3. 每个词在原始字符串中的起止字符位置。
  4. 分词器额外输出的一些其他信息，二进制格式。

  有以下几个选项配置

  - no，不保存这些信息。
  - yes，仅保存分词结果。
  - with_positions，
  - with_offsets，
  - with_positions_offsets，
  - with_positions_payloads，
  - with_positions_offsets_payloads，

  with_positions_offsets可以提高vector hignlighter的速度，但是字段的索引大小会直接变为原来的2倍。[term vectors API](https://www.elastic.co/guide/en/elasticsearch/reference/8.11/docs-termvectors.html)可以查询这些存储的信息。

### 数据类型

- Aggregate metric，聚合统计，提前统计聚合的一些值，包含最大值、最小值、数量、和等。

- Alias，别名，为其它字段添加别名。

- Arrays，数组，es中没有专门的数组，任何字段都可以包含0个或者多个值，mapping中指定字段的类型为数组的元素类型，不存在array类型，添加文档时可以写成数组的形式，es可以自动识别。

  数组中所有值必须是同一数据类型，第一个元素的数据类型决定整个数组的数据类型，数组中的null值可以配置为忽略或者null_value类型。

- Binary，二进制，接受base64字符串，默认是不store并且无法检索的。

## 查询

- match，最常用，分词，全文检索。

- match_phrase，与match类似，**但是索引分词和查询分词结果必须相同，包括分词得到的顺序**，可配置参数slop，允许词和词之间出现其他token的数量。

  本人在ik分词测试，需要将analyzer和search_quote_analyzer设置成一样的分词器，才能正确检索出结果。

  match_phrase容易受到停用的影响，不配置ik的停用词影响match搜索，配置之后影响match_phrase，本人使用ik的tokenizer自定义analyzer，但是**ik的tokenizer就完成了中文标点去除、停用词去除以及分词的功能**，无法配置其仅完成分词，需要修改源码。
