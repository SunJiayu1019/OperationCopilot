# Milestone 2 Prompt 设计

Prompt 均由代码中的 `PromptRegistry` 统一管理，版本号固定为 `v1`，模型调用不在路由中拼接散落字符串。

## 视觉分析 Prompt

要求 MiniMind-V 只根据图像可见信息输出 JSON，字段包括：`product_name`、`category`、`colors`、`materials`、`scene`、`selling_points`、`visible_text`、`risks`、`page_layout`、`visual_style`。不确定的信息必须标记为 `unknown`，不能把猜测写成商品事实。商品主图、详情页截图和竞品素材各自带不同观察重点。如果 MiniMind-V 返回自然语言描述，Qwen 使用单独的结构化 Prompt 提取同一字段集；结果同时保留原始 `raw_description`。

## 商品总结 Prompt

要求 Qwen 根据视觉结果和检索证据，总结商品事实、目标人群、可验证卖点和不可直接宣称的功效，并为每条结论保留 evidence source。

## 小红书文案 Prompt

要求生成三版：生活方式、场景种草、信息清晰；使用轻量口语和真实体验，不使用绝对化词、无证据功效承诺或平台违规表达；输出标题、正文和标签数组。

## 内容审核 Prompt

要求逐句检查绝对化用语、无证据性能承诺、与商品资料不一致、可能引发误解和不符合品牌语气五类风险，并输出原文片段、风险等级、理由、建议。

