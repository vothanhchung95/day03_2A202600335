import os
from dotenv import load_dotenv
from src.core.gemini_provider import GeminiProvider
from src.agent.agent import ReActAgent
from src.tools.tools import tools

# 1. Load enviroment variables
load_dotenv()

def main():
    # 2. Gemini Provider
    llm = GeminiProvider(
        model_name=os.getenv("DEFAULT_MODEL", "gemini-1.5-flash"),
        api_key=os.getenv("GEMINI_API_KEY")
    )

    # 3. Initialize Agent with tools
    agent = ReActAgent(llm=llm, tools=tools, max_steps=5)

    print("--- 🤖 English Learning Agent đã sẵn sàng! ---")
    print("(Gõ 'exit', 'quit' hoặc 'bye' để dừng cuộc trò chuyện)\n")

    # 4. Interactive Loop
    while True:
        try:
            # User input
            user_query = input("You: ").strip()

            # exit condition
            if user_query.lower() in ['exit', 'quit', 'bye']:
                print("Agent: Tạm biệt! Chúc bạn học tiếng Anh vui vẻ.")
                break

            if not user_query:
                continue

            print("\nAgent đang suy nghĩ...")
            
            # Run the agent with the user's query
            result = agent.run(user_query)
            
            print(f"\nAgent: {result}\n")
            print("-" * 30)

        except KeyboardInterrupt:
            print("\nAgent: Đã dừng chương trình.")
            break
        except Exception as e:
            print(f"\n❌ Có lỗi xảy ra: {e}")
            print("Hãy thử lại câu hỏi khác.\n")

if __name__ == "__main__":
    main()