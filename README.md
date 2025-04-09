# AI Novel Writer - 智能小说创作助手

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Leveraging AI to help structure, build worlds, and generate content for your next novel.

## 项目概述

本项目旨在为小说作者提供一个集思绪整理、世界观构建、大纲编排和 AI 辅助内容生成于一体的创作工具。它遵循**结构化数据优先**的原则，用户首先定义小说的核心要素（项目、人物、设定、章节、场景目标），然后利用这些结构化信息，通过**检索增强生成 (Retrieval-Augmented Generation, RAG)** 技术驱动大型语言模型（如 OpenAI GPT 系列）生成具体的场景叙事内容。

## 核心功能

*   **项目管理:** 创建和管理多个小说项目，包含基本信息和全局梗概。
*   **世界构建:**
    *   **角色管理:** 创建、编辑、查看角色信息（背景、目标、性格等），自动生成并存储用于 RAG 的文本嵌入 (Embeddings)。
    *   **设定管理:** 定义小说的关键设定元素（地点、物品、概念等），同样生成并存储 Embeddings。
    *   **关系管理:** 定义角色之间的关系及其描述，生成并存储 Embeddings。
*   **故事结构:**
    *   **章节编排:** 创建、编辑、排序章节，定义章节概要（可选生成 Embedding）。
    *   **场景规划:** 在章节内或作为独立单元创建场景，定义场景核心目标 (Goal)，自动生成并存储 Goal Embedding 用于 RAG。
*   **AI 内容生成:**
    *   **RAG 驱动:** 基于场景目标 (Goal)，自动检索项目相关的角色、设定、关系以及过往场景概要等上下文信息。
    *   **智能续写:** 将场景目标和检索到的上下文信息组合成 Prompt，调用 LLM 生成场景的初稿内容。
    *   **状态管理:** 跟踪场景状态（计划中 Planned, 草稿 Drafted, 完成 Completed 等）。
*   **内容编辑:** 提供编辑器（可能基于富文本）查看和修改 AI 生成的内容或手动编写。

## 技术栈

*   **后端:**
    *   框架: Python, FastAPI
    *   ORM: SQLAlchemy
    *   数据库迁移: Alembic
    *   异步任务: (可能需要，例如 Celery，用于长时间运行的生成任务 - 当前未明确)
*   **数据库:**
    *   PostgreSQL
    *   PGVector: 用于高效存储和相似性搜索 Embeddings
*   **前端:**
    *   框架: Vue.js (Vue 3)
    *   状态管理: Pinia
    *   UI 库: Element Plus (根据前端结构推断)
    *   HTTP 客户端: Axios
    *   路由: Vue Router
    *   富文本编辑: TipTap (根据前端结构推断)
    *   构建工具: Vite
*   **AI & LLM:**
    *   OpenAI API: 用于文本生成和获取 Embeddings
*   **容器化:**
    *   Docker & Docker Compose: 用于轻松部署和管理 PostgreSQL + PGVector 数据库服务

## 架构简述

应用采用前后端分离架构。

1.  **前端 (Vue):** 用户通过界面进行交互，管理项目数据、定义故事结构、触发内容生成。
2.  **后端 (FastAPI):** 提供 RESTful API 供前端调用。处理业务逻辑，包括：
    *   所有资源的 CRUD 操作。
    *   在创建/更新关键文本信息（角色描述、设定细节、场景目标等）时，调用 OpenAI API 生成 Embeddings 并存储到 PGVector 字段。
    *   处理 `/scenes/{scene_id}/generate_rag` 请求：
        *   获取场景 Goal Embedding。
        *   使用 Goal Embedding 在 PGVector 中检索相关上下文（角色、设定、关系、过往场景等）的 Embeddings。
        *   获取对应的文本数据。
        *   格式化上下文信息并结合场景目标构建 Prompt。
        *   调用 OpenAI API 获取生成内容。
        *   将生成内容、可选的摘要及摘要 Embedding 存回数据库，更新场景状态。
3.  **数据库 (PostgreSQL + PGVector):** 持久化存储所有项目数据和 Embeddings。

## 环境准备

在开始之前，请确保你的系统已安装以下软件：

*   Git
*   Python 3.9+
*   Node.js 18+ (推荐使用 pnpm 或 npm)
*   Docker
*   Docker Compose

## 安装与配置

1.  **克隆仓库:**
    ```bash
    git clone https://github.com/glwlg/novel_writer_ai.git
    cd novel-writer-ai
    ```

2.  **启动数据库:**
    项目使用 Docker Compose 管理 PostgreSQL 和 PGVector 服务。
    ```bash
    cd novel_writer_ai # 进入包含 docker-compose.yml 的目录
    docker-compose up -d
    ```
    这将会在后台启动一个 PostgreSQL 实例，并启用 PGVector 扩展。

3.  **配置后端:**
    *   导航到后端目录: `cd backend`
    *   创建并激活 Python 虚拟环境:
        ```bash
        python -m venv .venv
        # Windows
        # .\venv\Scripts\activate
        # macOS/Linux
        source .venv/bin/activate
        ```
    *   安装依赖:
        ```bash
        pip install -r requirements.txt
        ```
    *   配置环境变量:
        复制 `.env.example` 文件为 `.env`:
        ```bash
        cp .env.example .env
        ```
        编辑 `.env` 文件，填入必要的配置：
        *   `DATABASE_URL`: 确保与 `docker-compose.yml` 中 PostgreSQL 服务的用户名、密码、数据库名和端口匹配。默认通常是 `postgresql+psycopg2://user:password@localhost:5432/novelai` (请检查 `docker-compose.yml` 中的配置)。
        *   `OPENAI_API_KEY`: 你的 OpenAI API 密钥。
        *   （可能还有其他配置，根据 `app/core/config.py` 查看）
    *   运行数据库迁移:
        确保数据库服务正在运行，然后在 `backend` 目录下执行：
        ```bash
        alembic upgrade head
        ```
        这将根据 `app/models/` 中的定义创建或更新数据库表结构。

4.  **配置前端:**
    *   导航到前端目录: `cd ../frontend` (从 backend 目录返回上一级再进入 frontend)
    *   安装依赖:
        ```bash
        # 推荐使用 pnpm
        # npm install -g pnpm # 如果未安装 pnpm
        # pnpm install

        # 或者使用 npm
        npm install
        ```
    *   (可选) 配置前端环境变量: 如果前端需要知道 API 的基础 URL (例如，如果不是在开发模式下使用 Vite 的 proxy)，可能需要在 `frontend` 目录下创建 `.env` 文件并设置类似 `VITE_API_BASE_URL=http://localhost:8000` 的变量。通常 Vite 开发服务器的代理配置 (`vite.config.js`) 可以处理这个问题。

## 运行应用

1.  **确保数据库正在运行:**
    ```bash
    cd novel_writer_ai # 包含 docker-compose.yml 的目录
    docker-compose ps # 检查服务状态，应该是 'Up'
    # 如果未运行，执行 docker-compose up -d
    ```

2.  **启动后端 FastAPI 服务器:**
    *   打开一个新的终端。
    *   导航到后端目录并激活虚拟环境:
        ```bash
        cd novel_writer_ai/backend
        source .venv/bin/activate # macOS/Linux or .\venv\Scripts\activate on Windows
        ```
    *   启动 Uvicorn 开发服务器:
        ```bash
        uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
        ```
        后端 API 将运行在 `http://localhost:8000`。

3.  **启动前端 Vue 开发服务器:**
    *   打开一个新的终端。
    *   导航到前端目录:
        ```bash
        cd novel_writer_ai/frontend
        ```
    *   启动 Vite 开发服务器:
        ```bash
        # 使用 pnpm
        # pnpm run dev

        # 使用 npm
        npm run dev
        ```
        前端应用通常会运行在 `http://localhost:5173` (或其他 Vite 指定的端口)。

4.  **访问应用:**
    在浏览器中打开前端 URL (例如 `http://localhost:5173`) 即可开始使用。
    你可以通过访问后端 API 文档 (`http://localhost:8000/docs`) 来查看和测试 API 接口。

## 数据库迁移

当数据库模型 (`app/models/`) 发生变化时，需要使用 Alembic 生成和应用迁移脚本：

1.  **生成迁移脚本 (在修改模型后):**
    ```bash
    cd backend
    # 确保虚拟环境已激活
    alembic revision --autogenerate -m "描述你的模型更改"
    ```
    检查 `alembic/versions/` 目录下新生成的脚本文件，确保它符合预期。

2.  **应用迁移:**
    ```bash
    alembic upgrade head
    ```

## API 文档

后端 API 遵循 OpenAPI 规范。当后端服务器运行时，可以通过访问 `/docs` 路径 (例如 `http://localhost:8000/docs`) 查看自动生成的交互式 API 文档 (Swagger UI)。

## 贡献

欢迎提出问题 (Issues) 或提交合并请求 (Pull Requests)。
