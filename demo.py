"""离线教学用模型响应夹具。它不调用大模型，不代表真实模型质量。"""
import json
from pathlib import Path
from types import SimpleNamespace


ANALYSIS = {
    "summary": "示例模块提供列表求和与文本读取，直接运行时打印求和结果 6。",
    "functions": [
        {"name": "calculate_sum", "parameters": "arr：支持 len 和下标访问的数值序列",
         "returns": "元素累加结果；空序列返回 0",
         "description": "按下标遍历并累加；未做元素类型校验。"},
        {"name": "read_file", "parameters": "path：文件路径",
         "returns": "文件文本字符串",
         "description": "以 r 模式打开并读取全文，使用系统默认编码，异常向调用方传播。"},
    ],
    "usage": "python examples/sample_code.py；直接运行打印 6。导入模块也会打印 6。",
    "issues": [
        "read_file 未显式关闭文件，建议改为 with open(...) 管理文件生命周期。",
        "读取文件时未指定编码，也未捕获文件不存在等异常，调用方需处理异常。",
        "calculate_sum 可使用内置 sum 简化；当前输入必须支持长度和下标访问。",
        "顶层 print 缺少 __main__ 保护，导入模块也会产生输出。",
    ],
}

DRAFT = """# sample_code.py 使用文档

## 功能说明

该模块包含数值序列求和和文本文件读取两个函数。直接运行模块会输出示例求和结果 `6`。

## 函数接口

| 函数 | 参数 | 返回值 | 行为 |
| --- | --- | --- | --- |
| `calculate_sum(arr)` | 支持 `len()` 和下标访问的数值序列 | 元素累加结果，空序列为 `0` | 按下标循环累加，不检查元素类型 |
| `read_file(path)` | 文件路径 | 文件全文字符串 | 使用系统默认编码，以 `r` 模式读取；读取异常向调用方传播 |

## 使用方法

在项目根目录执行：

```bash
python examples/sample_code.py
```

输出：

```text
6
```

在 Python 中调用：

```python
from examples.sample_code import calculate_sum, read_file

total = calculate_sum([1, 2, 3])  # 6
text = read_file("examples/sample_code.py")
```

注意：模块末尾有顶层 `print`，导入模块时也会输出一次 `6`。

## 已知问题

- `read_file` 未显式关闭文件，建议使用 `with open(...)`；当前代码尚未实现该改进。
- 未指定读取编码，文件编码与系统默认编码不一致时可能解码失败。
- 文件不存在或没有读取权限时会抛出异常，由调用方处理。
- 求和函数可用内置 `sum` 简化；当前实现要求输入支持长度和下标访问。
- 示例输出没有放在 `if __name__ == "__main__":` 下，导入模块会产生输出。
"""


def make_response(content=None, tool_calls=None):
    """提供与 SDK 消息相同的最小接口，走真实 Agent Loop。"""
    data = {"role": "assistant", "content": content}
    if tool_calls:
        data["tool_calls"] = tool_calls
    message = SimpleNamespace(
        content=content,
        tool_calls=[SimpleNamespace(id=c["id"], function=SimpleNamespace(**c["function"]))
                    for c in tool_calls] if tool_calls else None,
        model_dump=lambda **_: data,
    )
    return SimpleNamespace(choices=[SimpleNamespace(message=message)])


class DemoClient:
    def __init__(self, *, revision=False, reject_always=False):
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self.create))
        self.revision = revision
        self.reject_always = reject_always
        self.review_count = 0

    def create(self, *, messages, **kwargs):
        prompt = messages[0]["content"]
        payload = json.loads(messages[1]["content"])
        if "代码分析 Agent" in prompt:
            if messages[-1]["role"] != "tool":
                return make_response(tool_calls=[{
                    "id": "read_source_1", "type": "function",
                    "function": {"name": "read_file",
                                 "arguments": json.dumps({"filepath": payload["source"]})},
                }])
            actual = json.loads(messages[-1]["content"])
            expected = (Path(__file__).parent / "examples" / "sample_code.py").read_text(encoding="utf-8")
            if actual.get("status") != "success" or actual.get("content") != expected:
                raise ValueError("离线演示仅适用于随附的 sample_code.py，请使用 live 模式分析其他代码")
            return make_response(json.dumps(ANALYSIS, ensure_ascii=False))
        if "文档生成 Agent" in prompt:
            draft = DRAFT
            if (self.revision or self.reject_always) and not payload.get("review"):
                draft = draft[:draft.index("## 已知问题")]
            return make_response(draft)
        if "文档审校 Agent" in prompt:
            self.review_count += 1
            rejected = self.reject_always or "## 已知问题" not in payload["draft"]
            return make_response(json.dumps({
                "approved": not rejected,
                "issues": ["缺少已知问题章节，需要补充资源关闭、编码和导入副作用说明。"] if rejected else [],
            }, ensure_ascii=False))
        raise ValueError("未知的演示 Agent")
