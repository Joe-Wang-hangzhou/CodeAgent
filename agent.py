import os
import json
from openai import OpenAI
from tools import TOOLS_DEFINITION, AVAILABLE_TOOLS

class CodeAgent:
    def __init__(self, system_prompt="你是一个高级代码审查与解释助手。你可以使用工具读取本地文件，帮助用户审查代码质量、发现 Bug 并提供改进建议。"):
        self.client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
        )
        self.model = os.getenv("MODEL_NAME", "qwen-max")
        self.messages = [
            {"role": "system", "content": system_prompt}
        ]

    def chat(self, user_input: str):
        self.messages.append({"role": "user", "content": user_input})
        
        while True:
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=self.messages,
                    tools=TOOLS_DEFINITION,
                    tool_choice="auto"
                )
                
                response_message = response.choices[0].message
                self.messages.append(response_message)
                
                # 如果模型决定调用工具
                if response_message.tool_calls:
                    for tool_call in response_message.tool_calls:
                        function_name = tool_call.function.name
                        function_args = json.loads(tool_call.function.arguments)
                        
                        print(f"\n[Agent 正在调用工具: {function_name}({function_args})]")
                        
                        function_to_call = AVAILABLE_TOOLS.get(function_name)
                        if function_to_call:
                            function_response = function_to_call(**function_args)
                            
                            self.messages.append({
                                "tool_call_id": tool_call.id,
                                "role": "tool",
                                "name": function_name,
                                "content": function_response,
                            })
                        else:
                            self.messages.append({
                                "tool_call_id": tool_call.id,
                                "role": "tool",
                                "name": function_name,
                                "content": json.dumps({"error": "Tool not found"}),
                            })
                    # 将工具调用的结果再次发送给模型（进行下一轮推理）
                    continue 
                else:
                    # 没有工具调用，输出最终回复
                    return response_message.content
            except Exception as e:
                return f"Agent 运行出错: {str(e)}"
