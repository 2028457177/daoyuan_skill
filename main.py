import sys

from config import OPENAI_MODEL, OPENAI_BASE_URL
from counselor_style import CounselorStyle
from llm_client import LLMClient


BANNER = r"""
╔══════════════════════════════════════════════════╗
║          🎓  高校辅导员助手 (AI Counselor)        ║
║          v1.0  |  你的贴心学生事务顾问            ║
╚══════════════════════════════════════════════════╝
"""

HELP_TEXT = """
📋 可用命令:
  /help     - 显示此帮助信息
  /quit     - 退出程序
  /clear    - 清除对话历史，导员会重新发起话题
  /style    - 检查上一条导员回复是否符合辅导员风格
  /reload   - 重新加载 chat_examples.txt 聊天记录
  /model    - 查看当前连接信息
  /test     - 测试 API 连接是否正常
"""


def print_error(msg: str):
    print(f"\n  ❌ {msg}")


def print_info(msg: str):
    print(f"\n  ℹ️  {msg}")


def print_success(msg: str):
    print(f"\n  ✅ {msg}")


def validate_api():
    print_info("正在检查 API 配置...")
    if not OPENAI_MODEL or OPENAI_MODEL == "your-model-name":
        print_error("请在 .env 文件中设置 OPENAI_MODEL")
        sys.exit(1)


def main():
    print(BANNER)

    validate_api()

    try:
        llm = LLMClient()
    except ValueError as e:
        print_error(str(e))
        print_info("提示: 复制 .env.example 为 .env，然后填入你的 API Key。")
        sys.exit(1)

    connection = llm.check_connection()
    if connection["status"] == "error":
        print_error(connection["message"])
        proceed = input("\n  是否仍然继续? (y/n): ").strip().lower()
        if proceed != "y":
            print_info("已退出。请配置好 API 后重新运行。")
            sys.exit(0)
    else:
        print_success(connection["message"])

    print(HELP_TEXT)
    print("  💬 对话开始——辅导员会主动发起话题。\n")

    while True:
        display_counselor_message(llm)


def display_counselor_message(llm: LLMClient):
    if not llm.conversation_history:
        print_info("辅导员正在发起对话...")
        first_msg = llm.counselor_initiate()
    else:
        first_msg = None

    if first_msg and first_msg.startswith("调用大模型出错"):
        print_error(first_msg)
        return

    if first_msg:
        print(f"  🧑‍🏫 辅导员: {first_msg}\n")
        validate_and_show_warnings(first_msg)

    while True:
        try:
            user_input = input("  🧑 学生: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\n  再见！有问题随时来找我。👋\n")
            sys.exit(0)

        if not user_input:
            continue

        if user_input.startswith("/"):
            handled = handle_command(user_input, llm)
            if handled == "quit":
                print("\n  再见！有问题随时来找我。👋\n")
                sys.exit(0)
            continue

        print("\n  🧑‍🏫 辅导员: ", end="", flush=True)
        try:
            is_offense, _ = CounselorStyle.detect_student_offense(user_input)
            if is_offense:
                print("⚠ 严厉模式  ", end="", flush=True)

            full_text = ""
            for chunk in llm.chat_stream(user_input):
                print(chunk, end="", flush=True)
                full_text += chunk
            print("\n")

            if full_text.startswith("调用大模型出错"):
                continue

            validate_and_show_warnings(full_text, stern_mode=is_offense)
        except Exception as e:
            print(f"\n  ❌ 发生错误: {e}\n")


def validate_and_show_warnings(text: str, stern_mode: bool = False):
    validation = CounselorStyle.validate_response(text, stern_mode=stern_mode)
    if validation["warnings"]:
        for w in validation["warnings"]:
            print(f"  💡 {w}")


def handle_command(user_input: str, llm: LLMClient) -> str:
    command = user_input[1:].strip().lower()

    if command in ("quit", "exit", "q"):
        return "quit"
    elif command == "help":
        print(HELP_TEXT)
    elif command == "clear":
        llm.clear_history()
        print_success("对话历史已清除。辅导员将重新发起话题。")
    elif command == "model":
        connection = llm.check_connection()
        if connection["status"] == "ok":
            print_success(connection["message"])
        else:
            print_error(connection["message"])
    elif command == "test":
        print_info("正在测试连接...")
        connection = llm.check_connection()
        if connection["status"] == "ok":
            print_success(connection["message"])
        else:
            print_error(connection["message"])
    elif command == "reload":
        examples = CounselorStyle.reload_examples()
        if examples:
            print_success(f"已重新加载聊天记录 ({len(examples)} 字符)")
        else:
            print_info("chat_examples.txt 文件为空或不存在")
    elif command == "style":
        history = llm.conversation_history
        last_response = None
        for msg in reversed(history):
            if msg["role"] == "assistant":
                last_response = msg["content"]
                break
        if last_response is None:
            print_info("还没有对话记录。")
        else:
            validation = CounselorStyle.validate_response(last_response)
            print(CounselorStyle.format_result(validation))
            print(f"\n  📝 上一条导员回复:\n  ---\n  {last_response}\n  ---")
    else:
        print_error(f"未知命令: /{command}。输入 /help 查看可用命令。")

    return ""


if __name__ == "__main__":
    main()
