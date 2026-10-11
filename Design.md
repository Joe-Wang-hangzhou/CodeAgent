# 架构与设计文档

## 项目目标
搭建一个简单的代码助手 Agent，掌握 Agent 开发的基础能力（LLM调用、Prompt设计、工具集成等）。

## 选题方向
本项目选择了 **代码审查与解释 Agent**，提供代码质量分析、错误排查和重构建议。

## 技术选型
- **编程语言**：Python
- **LLM 服务商**：支持 OpenAI 协议的所有大模型（默认预设阿里云百炼/通义千问 `qwen-max`）。
- **Agent 框架**：不使用 LangChain / AutoGen 等重型框架，而是基于**原生的 OpenAI API (Function Calling)** 手工编写了标准的 Agent Loop，以便更透彻地展现其底层逻辑。

## Agent 架构设计
本项目基于 **ReAct (Reasoning and Acting)** 思想实现了基础的 Agent 循环。

### 1. 核心循环 (Core Loop)
- **输入 (Input)**：接收用户的自然语言指令。
- **推理 (Reasoning)**：将系统提示词、对话历史和可用工具描述发送给大模型，模型根据上下文决定直接回复还是调用工具。
- **工具调用 (Tool Call)**：如果模型决定调用工具，代码会解析函数名和参数，在本地执行对应函数，并将执行结果拼接回对话上下文中。
- **重新推理 / 输出 (Output)**：将工具执行结果发给大模型进行下一轮推理，直到模型给出最终的人类可读文本回复。

### 2. 错误处理与重试
- 工具调用过程中使用了 `try-except` 包裹，任何本地文件读取或目录访问异常都会作为 JSON 字符串返回给大模型。
- 模型接收到错误信息后，可以进行自我纠正或向用户报告错误。

### 3. 工具集成 (Tools Integration)
我们定义了 `TOOLS_DEFINITION` JSON Schema，并在 `AVAILABLE_TOOLS` 中将名称映射到实际的 Python 函数：
- `list_directory`: 调用 `os.listdir()` 了解项目结构。
- `read_file`: 读取文件文本并返回，赋予 Agent 获取外部（本地）环境信息的能力。
