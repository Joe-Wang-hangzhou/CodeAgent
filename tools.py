import os
import json

def list_directory(path: str = ".") -> str:
    """列出指定目录下的文件和文件夹"""
    try:
        files = os.listdir(path)
        return json.dumps({"status": "success", "files": files}, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)}, ensure_ascii=False)

def read_file(filepath: str) -> str:
    """读取指定代码文件的内容"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        return json.dumps({"status": "success", "content": content}, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)}, ensure_ascii=False)

# 工具定义描述，用于传递给大模型
TOOLS_DEFINITION = [
    {
        "type": "function",
        "function": {
            "name": "list_directory",
            "description": "列出指定目录下的文件和文件夹",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "要查看的目录路径，默认为当前目录 '.'"
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "读取指定代码文件的内容，用于进行代码审查或解释",
            "parameters": {
                "type": "object",
                "properties": {
                    "filepath": {
                        "type": "string",
                        "description": "要读取的文件相对或绝对路径"
                    }
                },
                "required": ["filepath"]
            }
        }
    }
]

# 工具函数映射表
AVAILABLE_TOOLS = {
    "list_directory": list_directory,
    "read_file": read_file
}
