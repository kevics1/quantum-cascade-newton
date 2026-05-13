# 全国行政区划知识图谱 (National Administrative Region Knowledge Graph)

本项目旨在基于标准的行政区划空间数据，构建一个覆盖全国四级（省、市、县、乡/镇/街道）的行政区划知识图谱。通过提取层级归属（`BELONGS_TO`）等关系，支持复杂的层级查询、路径分析和前端可视化展示。

## 📦 项目结构

- **`build_admin_kg.py`**: 核心构建脚本。连接 PostgreSQL 数据库提取数据，使用 NetworkX 构建图数据结构，并导出可视化文件。
- **`index.html`**: D3.js 前端可视化页面。通过力导向图展示知识图谱的节点和连线结构。
- **`admin_knowledge_graph.json`**: (自动生成) 供 D3.js 渲染使用的 Node-Link JSON 格式图数据。
- **`admin_knowledge_graph.graphml`**: (自动生成) 供 Gephi 等专业图可视化软件导入分析的 GraphML 格式数据。

## 🚀 快速开始

### 1. 准备数据库环境
确保本地运行 PostgreSQL 数据库（默认主机 `localhost`，端口 `5432`，用户名 `postgres`，数据库名 `Administrator`），并且其中包含行政区划的数据表：
- `province`（包含：`省级码`, `省`, `省类型` 等字段）
- `city`（包含：`地级码`, `地名`, `地级类`, `省级码` 等字段）
- `county`（包含：`县级码`, `地名`, `县级类`, `地级码` 等字段）
- `village`（包含：`area_code`, `name`, `layer` 等字段）

### 2. 安装依赖
Python 环境需要以下依赖项：
```bash
pip install networkx psycopg2-binary
```

### 3. 生成知识图谱
如果你的数据库密码不是默认的 `gis2023`，请通过环境变量 `PGPASSWORD` 设置。
```bash
# 生成 JSON 和 GraphML 图谱文件
python build_admin_kg.py
```
运行成功后，脚本将查询数据库并在本地生成包含约 4.6 万节点和 4.5 万条边的 `json` 及 `graphml` 文件。

### 4. 启动可视化
为避免浏览器的跨域安全限制 (CORS) 导致无法读取本地 JSON 文件，需要通过本地 HTTP 服务器启动前端页面：
```bash
# 启动本地测试服务器（默认端口 8000）
python -m http.server
```
然后在浏览器中访问: [http://localhost:8000/index.html](http://localhost:8000/index.html)

> **💡 性能提示**：由于 4 万多个节点同时进行前端力导向计算会导致浏览器崩溃，`index.html` 中的 D3 可视化做了**自动过滤**，目前仅渲染展示**省**和**市**两级节点（蓝色为省，橙色为市）。如果需要全量分析，建议使用专业的图分析软件打开 `admin_knowledge_graph.graphml`。

## 🛠️ 后续可扩展方向
- **Neo4j 深度集成**：本项目目前的输出为内存网络图结构及静态文件导出。对于更复杂的查询计算（如查询北京下属的所有节点树、查找沿革路径），建议将 `build_admin_kg.py` 改造为直连 Neo4j 图数据库，使用 Cypher 语法进行深度检索。
- **空间拓扑关系补全**：未来可接入 PostGIS 空间函数（如 `ST_Intersects`），补充相邻（`ADJACENT_TO`）等空间实体边关系。
