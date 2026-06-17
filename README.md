# 🐾 宠物医疗助手

[![Python Version](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/)
[![LangChain](https://img.shields.io/badge/LangChain-1.3.4-ff69b4)](https://www.langchain.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.58.0-ff4b4b)](https://streamlit.io/)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue)](https://www.docker.com/)
[![License](https://img.shields.io/badge/License-MIT-green)](https://opensource.org/licenses/MIT)

> 专业的宠物医疗咨询助手，基于 LangChain 技术和 RAG（检索增强生成）系统，为宠物主人提供智能化的医疗咨询服务。

---

## ✨ 核心特性

- **🧠 智能对话**：基于 LangGraph 的 ReAct（Reasoning + Acting）循环，自主思考并调用工具
- **📚 本地知识库**：基于 Chroma 向量数据库的 RAG 检索，支持 PDF/TXT 文档上传与 MD5 去重
- **🌐 联网搜索**：集成 SerpAPI（Google）搜索，直连抓取网页正文（requests + lxml）
- **🌦️ 天气查询**：通过 Open-Meteo API 获取历史与未来天气预报
- **💬 多会话管理**：Streamlit 前端支持多会话切换、持久化与历史恢复
- **🚀 流式输出**：实时 token 流式输出，提升用户体验
- **📊 知识库管理**：独立的向量库浏览与知识库管理页面
- **🐳 Docker 支持**：一键容器化部署，简化运维流程
- **🔧 模块化设计**：工厂模式管理模型、配置驱动、中间件监控工具调用

---

## 🏗️ 技术架构

### 核心组件

| 组件 | 技术栈 | 说明 |
|------|--------|------|
| **Agent 引擎** | LangGraph + DeepSeek-V4-Pro | ReAct 循环，自主调用工具 |
| **向量数据库** | Chroma + OpenAIEmbeddings | 文档检索与相似度匹配 |
| **前端界面** | Streamlit 多页面 | 主界面 + 知识库管理 + 向量库浏览 |
| **模型服务** | DashScope（阿里云） | LLM 与 Embedding 模型 |
| **Web 搜索** | SerpAPI + requests/lxml | 联网搜索与内容提取 |
| **天气服务** | Open-Meteo API | 地理编码与天气预报 |

### 系统架构图

```
┌──────────────────────────────────────────────────────────────────────┐
│                        用户 (Streamlit UI)                           │
│                主界面.py → render_chat() → 输入问题                   │
│              pages/ → 知识库管理.py → 向量库浏览.py                   │
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
                    工具执行分支（由 Agent 自主选择调用）
```

---

## 🚀 快速开始

### 环境要求

- Python 3.11+
- 阿里云 DashScope API Key（用于 DeepSeek-V4-Pro）
- SerpAPI Key（用于 Google 搜索）
- 可选：本地宠物医疗文档（PDF/TXT）

### 安装方式

#### 方式一：一键启动脚本（推荐）

**Windows：**
```bash
# 双击运行 start.bat 或在终端执行
start.bat
```

**Linux / Mac：**
```bash
# 添加执行权限并运行
chmod +x start.sh
./start.sh
```

启动脚本会自动完成：
- 检测 Python 环境
- 创建并激活虚拟环境
- 安装所有依赖
- 创建必要的目录结构
- 启动 Streamlit 应用

#### 方式二：手动安装

1. **克隆仓库**
   ```bash
   git clone https://github.com/Chow529/pet-medical-assistant.git
   cd pet-medical-assistant
   ```

2. **创建虚拟环境并安装依赖**
   ```bash
   python -m venv .venv
   # Windows
   .venv\Scripts\activate
   # Linux/Mac
   source .venv/bin/activate
   
   pip install -r requirements.txt
   ```

3. **配置 API 密钥（系统环境变量）**
   
   所有 API 密钥通过**系统环境变量**配置，无需 `.env` 文件。请在操作系统中设置以下环境变量：

   **Windows（PowerShell）：**
   ```powershell
   [System.Environment]::SetEnvironmentVariable('SERPAPI_API_KEY', 'your_serpapi_key_here', 'User')
   [System.Environment]::SetEnvironmentVariable('mode_key', 'sk-your-dashscope-api-key-here', 'User')
   ```

   **Windows（CMD）：**
   ```cmd
   setx SERPAPI_API_KEY "your_serpapi_key_here"
   setx mode_key "sk-your-dashscope-api-key-here"
   ```

   **Linux / Mac：**
   ```bash
   echo 'export SERPAPI_API_KEY="your_serpapi_key_here"' >> ~/.bashrc
   echo 'export mode_key="sk-your-dashscope-api-key-here"' >> ~/.bashrc
   source ~/.bashrc
   ```

   | 环境变量 | 说明 | 是否必填 |
   |----------|------|----------|
   | `SERPAPI_API_KEY` | SerpAPI（Google 搜索）密钥 | 必填 |
   | `mode_key` | 阿里云 DashScope API Key（DeepSeek-V4-Pro） | 必填 |

   > ⚠️ 注意：设置完成后**重启终端**使环境变量生效。

4. **加载本地知识库（可选）**
   - 创建 `doc/` 目录并放入宠物医疗相关 PDF/TXT 文档
   - 执行文档加载：
     ```bash
     python -c "from rag.ChromaService import chroma_ini; chroma_ini.load_document()"
     ```
   - 支持 MD5 去重，重复文档不会被重复加载

5. **启动应用**
   ```bash
   streamlit run 主界面.py
   ```
   - 访问 `http://localhost:8501`
   - 在左侧边栏创建新会话，开始提问

#### 方式三：Docker 部署

适合生产环境或需要快速部署的场景。

1. **构建并运行容器**
   ```bash
   # 使用 docker-compose（推荐）
   docker-compose up -d
   
   # 或直接构建
   docker build -t pet-medical-assistant .
   docker run -d -p 8501:8501 \
     -e SERPAPI_API_KEY="your_key" \
     -e mode_key="your_key" \
     -v ./knowledge:/app/knowledge \
     -v ./config:/app/config \
     pet-medical-assistant
   ```

2. **访问应用**
   - 打开浏览器访问 `http://localhost:8501`

3. **停止容器**
   ```bash
   docker-compose down
   ```

---

## 📖 使用指南

### 基本操作

1. **新建会话**：点击左侧边栏"新对话"按钮
2. **切换会话**：在历史对话列表中选择不同会话
3. **清空对话**：点击"清空"按钮清除当前会话消息
4. **删除会话**：点击会话旁边的 ❌ 按钮删除整个会话
5. **输入问题**：在底部输入框提问，支持以下类型：
   - 🏥 宠物医疗咨询："狗狗呕吐怎么办？"
   - 🌤️ 天气查询："北京明天天气如何？"
   - 🔍 联网搜索："最新的宠物疫苗技术有哪些？"
6. **流式输出**：AI 回答会逐词显示，提升交互体验

### 知识库管理页面

访问方式：在 Streamlit 多页面应用中切换到"知识库管理"页面。

功能：
- 📤 上传文档：支持 PDF/TXT 格式
- 📋 查看已加载文档列表
- 🗑️ 删除指定文档
- 🔄 重新加载知识库
- 📊 统计信息展示

### 向量库浏览页面

访问方式：在 Streamlit 多页面应用中切换到"向量库浏览"页面。

功能：
- 🔍 搜索向量：输入关键词查询相似文档
- 📄 查看文档内容片段
- 📈 相似度评分展示

### 会话持久化

- 所有会话历史自动保存到 `history/sessions.json`
- 页面刷新或重启后会话完全恢复
- 每个会话包含唯一 ID、标题、创建时间与消息列表

---

## ⚙️ 配置说明

### 配置文件概览

| 配置文件 | 作用 | 关键字段 |
|----------|------|----------|
| `config/rag.yml` | LLM 模型与 Embedding 模型配置 | `chatmodel_name`, `embeddingmodel_name`, `base_url` |
| `config/chroma.yml` | 向量数据库参数 | `collection_name`, `chunk_size`, `chunk_overlap`, `k` |
| `config/prompt.yml` | 系统提示词与场景 Prompt | `main_prompt`, `rag_summarize_prompt`, `report_prompt_1` |
| 系统环境变量 | API Key | `SERPAPI_API_KEY`, `mode_key` |

### 模型配置（`rag.yml`）

```yaml
chatmodel_name: deepseek-v4-pro       # 对话模型名称
embeddingmodel_name: text-embedding-v1 # 嵌入模型名称
base_url: https://dashscope.aliyuncs.com/compatible-mode/v1
```

### 向量数据库配置（`chroma.yml`）

```yaml
collection_name: chowdb               # 集合名称
knowledge_dir: knowledge              # 向量库持久化目录
knowledge_doc: doc                    # 源文档目录

chunk_size: 200                       # 文本切分大小
chunk_overlap: 40                     # 切分重叠
separators: ["###\n", "\n\n", "\n", "。", "！", "？", "；", "，", ". ", " ", ""]
k: 2                                  # 检索返回最相似文档数
allow_type: [".pdf", ".txt"]          # 支持文件类型
```

### 系统提示词（`prompt.yml`）

- `main_prompt`：定义 Agent 角色、思考流程、工具使用约束
- `rag_summarize_prompt`：RAG 总结模板
- `report_prompt_1`：网页内容摘要模板

---

## 📁 项目结构

```
pet-medical-assistant/
├── 主界面.py                # Streamlit 主界面入口（聊天对话）
├── session_manager.py       # 多会话管理 & 持久化
├── pages/                   # Streamlit 多页面目录
│   ├── 知识库管理.py         # 知识库上传、管理页面
│   └── 向量库浏览.py         # 向量库检索、浏览页面
├── agent/                   # 智能体核心
│   ├── RecAgent.py          # 主 Agent 类（LangGraph create_agent）
│   └── tools/
│       ├── agent_tools.py   # 三大工具函数：rag_summarize / get_weather / rag_webserch
│       ├── middleware.py    # 中间件：工具调用监控 & 前置日志
│       └── webserch.py      # 备用 Web 搜索（Bocha.cn，当前未接入）
├── model/                   # 模型工厂
│   ├── __init__.py          # 导出 chat_model / embedding_model / summ_model
│   └ model_factory.py       # BaseModelFactory / ChatModelIni / EmbeddingModeIni
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
│   ├── rag.yml              # LLM 模型配置（model / base_url）
│   ├── chroma.yml           # Chroma 配置（collection / chunk / k 值）
│   └── prompt.yml           # 系统提示词 & 各场景 Prompt 模板
├── doc/                     # 本地知识库文档（宠物医疗 PDF/TXT 源文件）
├── knowledge/               # Chroma 向量数据库持久化目录
├── history/                 # 会话历史 JSON 持久化目录
├── log/                     # 日志文件目录
├── requirements.txt         # 完整 Python 依赖清单
├── pyproject.toml           # 项目配置（PEP 517）
├── Dockerfile               # Docker 构建镜像
├── docker-compose.yml       # Docker Compose 配置
├── start.bat                # Windows 一键启动脚本
├── start.sh                 # Linux/Mac 一键启动脚本
├── .gitignore               # Git 忽略文件配置
└── README.md                # 本文件
```

### 核心模块详解

#### 1. `主界面.py` — Streamlit 主界面
- 多会话聊天界面
- `init_session_state()`：初始化会话状态与单例
- `render_sidebar()`：渲染侧边栏（会话管理）
- `render_chat()`：渲染聊天主体与流式输出
- `save_message()`：消息持久化到 JSON

#### 2. `pages/知识库管理.py` — 知识库管理页面
- 文档上传（PDF/TXT）
- 已加载文档列表查看
- 单文档删除
- 知识库重新加载
- 统计信息展示

#### 3. `pages/向量库浏览.py` — 向量库浏览页面
- 关键词检索向量库
- 相似文档内容预览
- 相似度评分展示

#### 4. `session_manager.py` — 多会话管理
- `Session`：会话数据类（ID、标题、消息列表）
- `SessionManager`：会话 CRUD、持久化加载、历史格式转换

#### 5. `agent/RecAgent.py` — 核心 Agent 类
- 封装 LangGraph `create_agent()`
- `exe_stream()`：流式执行，逐 token 输出
- 注册三大工具 + 两个中间件

#### 6. `agent/tools/agent_tools.py` — 工具集
- `@tool` 装饰器注册的三大工具：
  1. `rag_summarize(query)`：RAG 检索本地知识库
  2. `get_weather(location, date)`：天气查询（Open-Meteo）
  3. `rag_webserch(querys)`：Web 搜索（SerpAPI + requests/lxml）

#### 7. `rag/ChromaService.py` — 向量数据库服务
- Chroma 初始化与持久化
- MD5 去重文档加载
- `get_retriever()`：返回 top-2 相似文档检索器

#### 8. `rag/RagService.py` — RAG 检索生成链
- 完整 RAG 流水线：检索 → 增强 → 生成
- `rag_summarize(query, web_content="")`：结合本地文档与 Web 内容生成回答

---

## 🔄 完整数据流

1. **用户输入** → Streamlit 前端获取问题
2. **Agent 启动** → `RecAgent.exe_stream(query, history)` → LangGraph ReAct 循环启动
3. **工具调用决策** → Agent 根据问题类型自主选择工具：
   - 🏥 宠物医疗 → `rag_summarize()` → Chroma 检索 → LLM 生成回答
   - 🌤️ 天气查询 → `get_weather()` → Open-Meteo API → 格式化输出
   - 🔍 语义不匹配 → `rag_webserch()` → SerpAPI 搜索 → 直连抓取网页 → 提取正文
4. **结果整合** → Agent 综合工具返回结果，生成自然语言回答
5. **流式输出** → 逐 token 显示在 Streamlit 界面
6. **持久化** → `save_message()` 写入 `history/sessions.json`

---

## 🛠️ 开发与扩展

### 添加新工具

1. 在 `agent/tools/agent_tools.py` 中使用 `@tool` 装饰器定义新函数
2. 在 `RecAgent.py` 的 `create_agent()` 的 `tools` 列表中添加
3. 在 `prompt.yml` 的 `main_prompt` 中描述工具用途与约束

### 自定义知识库

- 支持 PDF/TXT 文档
- 放入 `doc/` 目录，通过知识库管理页面或代码加载
- 修改 `config/chroma.yml` 中的 `chunk_size`、`chunk_overlap` 优化检索效果

### 日志与监控

- 日志输出：控制台（INFO）+ 文件（DEBUG，每日轮转）
- 工具调用监控：`monitor_tool` 中间件记录入参、结果、异常
- 模型调用前日志：`log_befort_mode` 记录消息数量

---

## 📝 待改进 / 已知问题

- [x] **Web 搜索超时** — ✅ 已修复，移除 Jina Reader，改用 requests + lxml 直连
- [x] **API Key 硬编码** — ✅ 已迁移到系统环境变量
- [x] **缺少 requirements.txt** — ✅ 已补充完整依赖清单
- [x] **缺少 Docker 支持** — ✅ 已添加 Dockerfile 与 docker-compose.yml
- [x] **缺少一键启动脚本** — ✅ 已添加 start.bat / start.sh
- [x] **缺少 .gitignore** — ✅ 已添加完整的忽略规则
- [ ] **Streamlit 流式输出卡顿** — 某些场景下流式输出可能卡顿，待优化
- [ ] **错误处理增强** — 部分 API 调用错误处理可更完善

---

## 🤝 贡献指南

1. Fork 本仓库
2. 创建功能分支：`git checkout -b feature/your-feature`
3. 提交更改：`git commit -m 'Add some feature'`
4. 推送分支：`git push origin feature/your-feature`
5. 提交 Pull Request

### 开发规范
- 遵循 PEP 8 代码风格
- 添加适当的类型注解
- 更新相关文档与配置文件
- 确保现有功能不受影响

---

## 📄 许可证

本项目采用 MIT 许可证，详见 [LICENSE](LICENSE) 文件。

---

## 🙏 致谢

- [LangGraph](https://langchain-ai.github.io/langgraph/)：强大的 Agent 框架
- [LangChain](https://www.langchain.com/)：LLM 应用开发框架
- [DashScope](https://dashscope.aliyuncs.com/)：阿里云模型服务平台
- [Chroma](https://www.trychroma.com/)：轻量级向量数据库
- [Streamlit](https://streamlit.io/)：快速构建数据应用
- [Open-Meteo](https://open-meteo.com/)：免费的天气 API
- [SerpAPI](https://serpapi.com/)：Google 搜索 API

---

## 📞 支持与反馈

如有问题或建议，请提交 Issue 或通过邮件联系。

---

**Happy coding with your pet! 🐶🐱**