# Homework 1: 代码审查与解释 Agent

这是一个基于原生大模型 API（兼容 OpenAI 协议）构建的代码审查与解释助手。它展示了 Agent 的基本运行循环：`Input → Reasoning → Tool Call → Output`。
本项目默认配置使用了阿里云百炼（通义千问）接口。

## 核心功能
1. **代码审查**：通过调用本地工具读取代码文件，分析代码质量并给出改进建议。
2. **代码解释**：解释本地代码文件的逻辑。
3. **上下文记忆**：在单次会话中保持多轮对话的上下文。
4. **工具调用**：实现了 `read_file` 和 `list_directory` 工具。

## 快速开始

### 1. 安装依赖
确保已安装 Python 环境（推荐 Python 3.8+）。
```bash
pip install -r requirements.txt
```

### 2. 配置环境
复制 `.env.example` 为 `.env` 文件：
```bash
cp .env.example .env
```
在 `.env` 中填入你的通义千问（或兼容模型）API Key：
```env
OPENAI_API_KEY=你的API_KEY
OPENAI_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
MODEL_NAME=qwen-max
```

### 3. 运行 Agent
```bash
python main.py
```

### 4. 交互示例
启动后，你可以输入：
- "列出当前目录下的文件"
- "帮我审查一下 sample_code.py"
- "刚刚那个代码有什么可以优化的地方？"

