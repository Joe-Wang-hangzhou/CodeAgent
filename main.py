import os
from dotenv import load_dotenv
from agent import CodeAgent

def main():
    # 尝试加载 .env 文件
    load_dotenv()
    
    if not os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY") == "your_qwen_api_key_here":
        print("警告: 未检测到有效的 OPENAI_API_KEY！请在 .env 文件中设置。")
        print("请按 Ctrl+C 退出，或者输入您的问题测试报错。")

    print("=======================================")
    print("代码审查与解释 Agent 已启动 (使用千问模型)")
    print("=======================================")
    print("输入 'exit' 或 'quit' 退出")
    
    agent = CodeAgent()
    
    while True:
        try:
            user_input = input("\nUser> ")
            if user_input.lower() in ['exit', 'quit']:
                print("退出 Agent。")
                break
            if not user_input.strip():
                continue
                
            print("\nAgent 正在思考...")
            reply = agent.chat(user_input)
            print(f"\nAgent> {reply}")
        except KeyboardInterrupt:
            print("\n退出 Agent。")
            break

if __name__ == "__main__":
    main()
