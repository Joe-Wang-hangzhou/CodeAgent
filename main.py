import argparse
import os
from pathlib import Path

from workflow import DocumentationWorkflow


ROOT = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser(description="Homework2：代码分析 → 文档生成 → 文档审校")
    parser.add_argument("source", nargs="?", default=str(ROOT / "examples" / "sample_code.py"))
    parser.add_argument("--demo", action="store_true", help="使用固定响应夹具离线演示，不调用真实模型")
    parser.add_argument("--demo-revision", action="store_true", help="离线演示一次审校退回与修订（隐含 --demo）")
    parser.add_argument("--output", default=str(ROOT / "outputs" / "latest"))
    args = parser.parse_args()
    demo_mode = args.demo or args.demo_revision
    client = None
    if demo_mode:
        from demo import DemoClient

        client = DemoClient(revision=args.demo_revision)
        print("离线演示模式：使用预设响应，不调用真实大模型；会实际读取源码并执行工作流。")
    else:
        try:
            from dotenv import load_dotenv
            load_dotenv(ROOT / ".env")
        except ImportError:
            parser.error("请先执行 python -m pip install -r requirements.txt，或使用 --demo")
        key = os.getenv("OPENAI_API_KEY", "")
        if not key or key == "your_qwen_api_key_here":
            parser.error("真实模型模式需要在 .env 设置 OPENAI_API_KEY；可先运行 python main.py --demo")
        print("真实模型模式：三个 Agent 将调用配置的兼容 OpenAI API。")
    try:
        workflow = DocumentationWorkflow(args.output, client=client, mode="demo" if demo_mode else "live")
        state = workflow.run(args.source)
    except Exception as exc:
        print(f"初始化失败：{exc}")
        return 1
    if state.status == "failed":
        print(f"运行失败：{state.error}\n状态与日志：{Path(args.output).resolve()}")
        return 1
    print(f"执行完成，返工次数：{state.revisions}")
    print(f"最终文档：{Path(args.output).resolve() / 'generated_document.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
