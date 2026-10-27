"""复用 Homework1 的 Function Calling 循环，供不同职责的 Agent 使用。"""
import json
import os

from tools import AVAILABLE_TOOLS, TOOLS_DEFINITION


class CodeAgent:
    def __init__(self, system_prompt, *, client=None, use_tools=False, max_steps=8):
        if client is None:
            from openai import OpenAI

            client = OpenAI(
                api_key=os.getenv("OPENAI_API_KEY"),
                base_url=os.getenv(
                    "OPENAI_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1"
                ),
                timeout=60.0,
                max_retries=1,
            )
        self.client = client
        self.model = os.getenv("MODEL_NAME", "qwen-max")
        self.system_prompt = system_prompt
        self.use_tools = use_tools
        self.max_steps = max_steps
        self.messages = []

    def chat(self, user_input):
        # 每次节点执行使用独立上下文；节点间的数据由 WorkflowState 显式传递。
        self.messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_input},
        ]
        for _ in range(self.max_steps):
            kwargs = {"model": self.model, "messages": self.messages}
            if self.use_tools:
                kwargs.update(tools=TOOLS_DEFINITION, tool_choice="auto")
            response = self.client.chat.completions.create(**kwargs)
            message = response.choices[0].message
            self.messages.append(message.model_dump(exclude_none=True))
            if not message.tool_calls:
                if not message.content or not message.content.strip():
                    raise ValueError("Agent 返回了空内容")
                return message.content
            if not self.use_tools:
                raise ValueError("该 Agent 未开放工具")
            for call in message.tool_calls:
                try:
                    function = AVAILABLE_TOOLS[call.function.name]
                    arguments = json.loads(call.function.arguments)
                    result = function(**arguments)
                except (KeyError, TypeError, ValueError) as exc:
                    result = json.dumps({"status": "error", "message": str(exc)})
                self.messages.append(
                    {"tool_call_id": call.id, "role": "tool",
                     "name": call.function.name, "content": result}
                )
        raise RuntimeError(f"Agent 超过最大调用轮数 {self.max_steps}")
