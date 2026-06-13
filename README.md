# 宠物医疗助手 AI 智能体 (Agent for Dog)

基于 **LangGraph** + **DeepSeek-V4-Pro** 构建的宠物医疗问答智能体，内嵌 **RAG（检索增强生成）** 与 **Web 搜索** 能力，通过 **Streamlit** 提供多会话前端界面。

---

## 目录结构

```
agent_for_dog/
├── main.py                  # Streamlit UI 入口
├── session_manager.py       # 多会话管理 & 持久化
├── agent/                   # 智能体核心
│   ├── RecAgent.py          # 主 Agent 类（LangGraph create_agent）
│   └── tools/
│       ├── agent_tools.py   # 三大工具函数：rag_summarize / get_weather / rag_webserch
│       ├── middleware.py     # 中间件：工具调用监控 & 前置日志
│       └── webserch.py      # 备用 Web 搜索（Bocha.cn，当前未接入）
├── model/                   # 模型工厂
│   ├── __init__.py          # 导出 chat_model / embedding_model / summ_model
│   └── model_factory.py     # BaseModelFactory / ChatModelIni / EmbeddingModeIni
├── rag/                     # RAG 检索增强生成
│   ├── ChromaService.py     # Chroma 向量数据库初始化 & 文档加载（含 MD5 去重）
│   ├── RagService.py        # RAG 检索 + 生成链
│   └── SummRag.py           # 网页内容摘要封装
├── utils/                   # 工具模块
│   ├── config_tool.py       # YAML 配置加载（rag / chroma / prompt / agent / public）
│   ├── file_tool.py         # 文件操作：MD5、PDF/TXT 加载
│   ├── logging_tool.py      # 双输出日志（控制台 + 文件）
│   ├── path_tool.py         # 项目根目录 & 绝对路径解析
│   └── prompt_tool.py       # Prompt 管理（占位）
├── config/                  # YAML 配置文件
│   ├── rag.yml              # LLM 模型配置（model / base_url / api_key）
│   ├── chroma.yml           # Chroma 配置（collection / chunk / k 值）
│   └── prompt.yml           # 系统提示词 & 各场景 Prompt 模板
├── doc/                     # 本地知识库文档（宠物医疗 PDF/TXT 源文件）
├── knowledge/               # Chroma 向量数据库持久化目录
├── history/                 # 会话历史 JSON 持久化目录
├── log/                     # 日志文件目录
└── README.md                # 本文件
```

---

## 各模块详解

### 1. `main.py` — Streamlit UI 入口

基于 **Streamlit** 构建的多会话聊天前端。

**关键方法：**

| 方法 | 作用 |
|------|------|
| `init_session_state()` | 初始化 `st.session_state`，创建 `SessionManager`、`RecAgent` 单例 |
| `render_sidebar()` | 渲染左侧边栏：新建会话、清除、切换/删除会话列表、统计信息 |
| `render_chat()` | 渲染聊天主体：标题、历史消息、输入框、**流式输出** |
| `save_message(role, content)` | 保存消息到当前会话并持久化到 JSON |
| `load_current_session_messages()` | 从文件加载当前会话的所有消息 |

**流式输出：** 调用 `agent.exe_stream(prompt, history[:-1])` 实现逐 token 流式显示。

---

### 2. `session_manager.py` — 多会话管理

将会话持久化到 `history/sessions.json`，支持页面刷新后恢复历史。

**关键类与方法：**

| 类 | 方法 | 作用 |
|----|------|------|
| `Session` | `__init__` | 初始化：session_id(UUID)、title、created_at、messages 列表 |
| `Session` | `add_message(role, content)` | 添加一条消息（含时间戳） |
| `Session` | `to_dict()` / `from_dict()` | 序列化 / 反序列化 |
| `SessionManager` | `__init__` | 从 `history/sessions.json` 加载已有会话 |
| `SessionManager` | `create_session(title)` | 创建新会话，返回 `Session` |
| `SessionManager` | `switch_session(session_id)` | 切换当前激活的会话 |
| `SessionManager` | `delete_session(session_id)` | 删除会话，自动切换到下一个 |
| `SessionManager` | `get_conversation_history(session_id)` | 获取 Agent 兼容格式（role/content 列表）的消息历史 |
| `SessionManager` | `add_message_to_current(role, content)` | 快捷添加消息到当前会话 |

---

### 3. `agent/RecAgent.py` — 核心 Agent 类

封装 **LangGraph** 的 `create_agent()`，是智能体的中枢。

```python
class RecAgent:
    def __init__(self):
        self.agent = create_agent(
            model=chat_model,                          # 来自 model_factory
            tools=[rag_summarize, get_weather, rag_webserch],  # 三大工具
            system_prompt=prompt_config['main_prompt'], # 系统提示词
            middleware=[monitor_tool, log_befort_mode]  # 中间件
        )

    def exe_stream(self, query, history=None):
        """流式执行：用 self.agent.stream(stream_mode="updates") 逐 token 产出内容"""
```

**核心流程：** 自动进入 **ReAct**（Reasoning + Acting）循环——模型根据当前状态决定思考、调用工具或输出回答。

---

### 4. `agent/tools/agent_tools.py` — Agent 工具集

定义注册给 Agent 的三个 LangChain 工具（使用 `@tool` 装饰器）：

| 工具函数 | 签注 | 作用 |
|----------|------|------|
| `rag_summarize(query: str) -> str` | 标注 RAG | 调 `RagService.rag_summarize()` → 向量检索 + LLM 总结 |
| `get_weather(location: str, date: str) -> str` | 标注天气 | Open-Meteo 地理编码 → 获取天气预报/历史 → 格式化输出 |
| `rag_webserch(querys: str) -> str` | 标注网页搜索 | SerpAPI(Google) 搜索 → Jina Reader 获取前 2 条内容 → 清洗后返回 |

**辅助函数：**

| 函数 | 作用 |
|------|------|
| `fetch_with_jina(url, max_chars=2000)` | 用 Jina Reader API 抓取网页正文，带超时和错误处理 |
| `clean_jina_content(content)` | 清洗 Jina 返回内容：去除 YAML 头、Markdown 链接标记等 |

---

### 5. `agent/tools/middleware.py` — 中间件

| 函数 | 装饰器 | 作用 |
|------|--------|------|
| `monitor_tool(request, handler)` | `@wrap_tool_call` | 工具调用前后日志记录：记录工具名、参数、结果、异常 |
| `log_befort_mode(state, runtime)` | `@before_model` | 模型调用前日志：记录即将发送给模型的消息数量 |

---

### 6. `model/model_factory.py` — 模型工厂

采用**工厂模式**统一创建 AI 模型实例。

| 类 | 继承 | 产出 |
|----|------|------|
| `BaseModelFactory` | `ABC` | 抽象基类，定义 `model()` 抽象方法 |
| `ChatModelIni` | `BaseModelFactory` | `ChatOpenAI`（deepseek-v4-pro，DashScope 接口） |
| `EmbeddingModeIni` | `BaseModelFactory` | `OpenAIEmbeddings`（text-embedding-v1） |

**模块级单例（模块加载时创建一次）：**
- `chat_model = ChatModelIni().model()` — 主对话模型
- `embedding_model = EmbeddingModeIni().model()` — 向量嵌入模型
- `summ_model = ChatModelIni().model()` — 摘要模型（复用 ChatModelIni）

---

### 7. `rag/ChromaService.py` — 向量数据库服务

管理 **Chroma** 向量数据库的初始化、文档切分、文档加载（MD5 去重）。

**关键方法：**

| 方法 | 作用 |
|------|------|
| `__init__()` | 创建 `knowledge/` 目录、`md5.txt`；初始化 Chroma 集合 + `RecursiveCharacterTextSplitter` |
| `get_retriever()` | 返回检索器，`search_kwargs={'k': 2}`，取最相似的 2 个文档块 |
| `load_document()` | 扫描 `doc/` 目录 → MD5 去重 → 加载 TXT/PDF → 切分 → 写入 Chroma → 记录 MD5 |

**配置（来自 `config/chroma.yml`）：**
- `chunk_size`: 200, `chunk_overlap`: 20
- `separators`: `["\n\n", "\n", "\t", ".", "!", "?", ""]`
- `k`: 2

---

### 8. `rag/RagService.py` — RAG 检索生成链

完整的 RAG 流水线：检索 → 增强 → 生成。

**关键方法：**

| 方法 | 作用 |
|------|------|
| `__init__()` | 获取 `chroma_ini.get_retriever()`；构建 LangChain chain: `PromptTemplate \| print_test \| chat_model \| StrOutputParser` |
| `rag_summarize(query, web_content="")` | 从 Chroma 检索相关文档 → 拼接 → （若有 Web 内容则用 `SummRag` 摘要） → 送入 LLM 链 → 返回最终回答 |

---

### 9. `rag/SummRag.py` — 网页内容摘要

轻量摘要封装，用于对 Web 搜索获取的内容做二次总结。

**关键方法：**

| 方法 | 作用 |
|------|------|
| `__init__(prompt)` | 构建 LangChain chain: `PromptTemplate \| print_test \| summ_model \| StrOutputParser` |
| `get_key_words(quer)` | 执行摘要链，传入 `{"input": quer}`，返回 LLM 输出（虽名 `get_key_words`，但功能是完整摘要） |

---

### 10. 工具模块 (`utils/`)

| 模块 | 关键函数 | 作用 |
|------|----------|------|
| `config_tool.py` | `load_rag_config()` / `load_chroma_config()` / `load_prompt_config()` 等 | 加载 `config/` 下各 YAML 配置文件 |
| `file_tool.py` | `get_file_md5_hex()` / `check_md5()` / `save_md5()` | 文件 MD5 计算、去重检查、保存 |
| `file_tool.py` | `load_pdf()` / `load_txt()` | 加载文档，返回 LangChain `Document` 对象（含丰富元数据） |
| `file_tool.py` | `get_file_list(dir)` | 按扩展名过滤获取文件列表 |
| `logging_tool.py` | `get_logger()` | 双输出日志：控制台（INFO）+ 文件（DEBUG，每日轮转） |
| `path_tool.py` | `get_projiect_root()` / `get_abs_path()` | 项目根路径检测与绝对路径拼接 |

---

## 完整数据流

```
┌──────────────────────────────────────────────────────────────────────┐
│                        用户 (Streamlit UI)                           │
│               main.py → render_chat() → 输入问题                      │
└──────────────────────────┬───────────────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────────────┐
│                    RecAgent.exe_stream(query, history)               │
│                                                                      │
│  LangGraph ReAct Loop:                                               │
│  ┌────────────────────────────────────────────┐                     │
│  │  ① 模型接收：[系统提示词 + 历史 + 用户输入]   │                     │
│  │  ② 模型决定：思考 → 输出回答 或 调用工具      │                     │
│  │  ③ 若调用工具 → 执行 → 结果回传 → 回到 ②     │                     │
│  └────────────────────────────────────────────┘                     │
│                                                                      │
│  tools 注册列表：                                                     │
│   ┌─────────────────────────────┐                                   │
│   │ rag_summarize(query)        │  ← 优先查本地知识库                │
│   │ get_weather(loc, date)      │  ← 查天气                         │
│   │ rag_webserch(querys)        │  ← 联网搜索                       │
│   └─────────────────────────────┘                                   │
│                                                                      │
│  middleware 中间件：                                                  │
│   ├── monitor_tool    → 记录每次工具调用的入参、结果、异常              │
│   └── log_befort_mode → 记录模型调用前的消息数量                       │
└──────────────────────────┬───────────────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────────────┐
│  工具执行分支（由 Agent 自主选择调用）                                    │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌── rag_summarize(query) ────────────────────────────────────────┐  │
│  │  ① RagService.rag_summarize(query)                             │  │
│  │  ② chroma_ini.get_retriever().invoke(query)                    │  │
│  │     → 从 Chroma 向量库检索 top-2 相关文档块                      │  │
│  │  ③ 若有 web_content：                                          │  │
│  │     → SummRag.get_key_words(web_content) → 摘要                 │  │
│  │  ④ 送入 LangChain Chain：                                       │  │
│  │     PromptTemplate | chat_model | StrOutputParser               │  │
│  │     → 结合 query + doc + web 生成最终回答                        │  │
│  │  ⑤ 返回答案字符串                                                │  │
│  └─────────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  ┌── get_weather(location, date) ─────────────────────────────────┐  │
│  │  ① Open-Meteo Geocoding API → 获取城市坐标 (lat, lon)           │  │
│  │  ② 判断日期：未来 → Open-Meteo Forecast API                    │  │
│  │              过去 → Open-Meteo Archive API                     │  │
│  │  ③ 解析温度 + WMO 天气码 → 格式化输出                           │  │
│  └─────────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  ┌── rag_webserch(querys) ────────────────────────────────────────┐  │
│  │  ① 按逗号拆分关键词                                             │  │
│  │  ② SerpAPI (Google) 搜索 → 取前 5 条结果                        │  │
│  │  ③ Jina Reader → 抓取前 2 条链接正文（fetch_with_jina）                │  │
│  │  ④ clean_jina_content() → 清洗内容                                │  │
│  │  ⑤ 返回格式化文本                                                  │  │
│  └─────────────────────────────────────────────────────────────────┘  │
│                                                                      │
└──────────────────────────┬───────────────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────────────┐
│                    最终回答流式输出到前端                              │
│              render_chat() → st.chat_message() → 展示给用户            │
│              同时 save_message() → 持久化到会话 JSON                    │
└──────────────────────────────────────────────────────────────────────┘
```

### 流程文字描述

1. **用户输入** → Streamlit 前端获取问题
2. **Agent 启动** → `RecAgent.exe_stream(query, history)` → LangGraph ReAct 循环启动
3. **RAG 查本地知识库** → Agent 调用 `rag_summarize(query)`：
   - Chroma 向量库检索相关文档 → LLM 结合文档生成回答
4. **语义不匹配时** → Agent 调用 `rag_webserch(querys)`：
   - SerpAPI 搜索 → Jina Reader 获取网页 → 摘要后返回给 Agent
5. **Agent 综合总结** → 将工具返回结果整合为自然语言回答
6. **流式输出** → 逐 token 显示在 Streamlit 界面
7. **持久化** → `save_message()` 写入 `history/sessions.json`

---

## 启动方式

```bash
# 1. 安装依赖（建议使用虚拟环境）
pip install -r requirements.txt

# 2. 配置 config/rag.yml 中的 API Key
#    - model: deepseek-v4-pro
#    - base_url: https://dashscope.aliyuncs.com/compatible-mode/v1
#    - api_key: 你的阿里云 DashScope API Key

# 3. 加载本地知识库（首次运行需要）
#    python -c "from rag.ChromaService import chroma_ini; chroma_ini.load_document()"

# 4. 启动 Streamlit
streamlit run main.py
```

---

## 配置说明

| 配置文件 | 作用 | 关键字段 |
|----------|------|----------|
| `config/rag.yml` | LLM 模型 & Embedding 模型配置 | `chat_model_name`, `embedding_model_name`, `base_url`, `api_key` |
| `config/chroma.yml` | 向量数据库参数 | `collection_name`, `chunk_size`, `chunk_overlap`, `k` |
| `config/prompt.yml` | 系统提示词 & RAG/摘要 Prompt | `main_prompt`, `rag_summarize_prompt`, `report_prompt_1` |
| `config/agent.yml` | Agent 配置（预留） | 空 |
| `config/public_config.yml` | 公共配置（预留） | 空 |

---

## 待改进 / 已知问题

- [ ] Web 搜索（`rag_webserch`）超时问题需要优化
- [ ] API Key 硬编码在代码和配置文件中，建议使用环境变量