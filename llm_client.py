from typing import List, Optional, Generator, Tuple
from openai import OpenAI

from config import OPENAI_API_KEY, OPENAI_BASE_URL, OPENAI_MODEL
from counselor_style import CounselorStyle


class LLMClient:
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
    ):
        self.api_key = api_key or OPENAI_API_KEY
        self.base_url = base_url or OPENAI_BASE_URL
        self.model = model or OPENAI_MODEL

        if not self.api_key:
            raise ValueError(
                "API Key 未配置。请在 .env 文件中设置 OPENAI_API_KEY，"
                "或通过环境变量设置。参考 .env.example 文件。"
            )

        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
        )

        self._conversation_history: List[dict] = []

    @property
    def conversation_history(self) -> List[dict]:
        return self._conversation_history

    def clear_history(self):
        self._conversation_history = []

    def _build_messages(self, user_input: str, stern_mode: bool = False) -> List[dict]:
        if stern_mode:
            user_content = f"{CounselorStyle.STERN_MODE_INSTRUCTION}\n\n{user_input}"
        else:
            user_content = user_input
        return CounselorStyle.build_messages(self._conversation_history) + [
            {"role": "user", "content": user_content}
        ]

    def _detect_and_wrap(self, user_input: str) -> Tuple[str, bool]:
        is_offense, reason = CounselorStyle.detect_student_offense(user_input)
        if is_offense:
            return (
                f"{CounselorStyle.STERN_MODE_INSTRUCTION}\n\n{user_input}",
                True,
            )
        return (user_input, False)

    def _build_initiate_messages(self) -> List[dict]:
        launch_instruction = {
            "role": "user",
            "content": (
                "（现在是对话开始，请以辅导员身份主动向学生发起第一轮对话。"
                "关心一下学生最近的情况，或者提醒一个近期事项。"
                "必须用你的真实风格说话，以问句结尾，引导学生回应。）"
            ),
        }
        return CounselorStyle.build_messages(self._conversation_history) + [launch_instruction]

    def counselor_initiate(self) -> str:
        try:
            messages = self._build_initiate_messages()
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=512,
            )
            content = response.choices[0].message.content or ""
            self._conversation_history.append({"role": "assistant", "content": content})
            return content
        except Exception as e:
            return f"调用大模型出错: {str(e)}"

    def chat(self, user_input: str) -> str:
        try:
            wrapped_input, is_stern = self._detect_and_wrap(user_input)
            messages = self._build_messages(wrapped_input, stern_mode=is_stern)

            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=1024,
            )

            content = response.choices[0].message.content or ""

            self._conversation_history.append({"role": "user", "content": user_input})
            self._conversation_history.append({"role": "assistant", "content": content})

            if len(self._conversation_history) > 20:
                self._conversation_history = self._conversation_history[-20:]

            return content

        except Exception as e:
            error_msg = f"调用大模型出错: {str(e)}"
            return error_msg

    def chat_stream(self, user_input: str) -> Generator[str, None, None]:
        try:
            wrapped_input, is_stern = self._detect_and_wrap(user_input)
            messages = self._build_messages(wrapped_input, stern_mode=is_stern)

            stream = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=1024,
                stream=True,
            )

            full_response = ""

            for chunk in stream:
                if chunk.choices[0].delta.content:
                    delta = chunk.choices[0].delta.content
                    full_response += delta
                    yield delta

            self._conversation_history.append({"role": "user", "content": user_input})
            self._conversation_history.append({"role": "assistant", "content": full_response})

            if len(self._conversation_history) > 20:
                self._conversation_history = self._conversation_history[-20:]

        except Exception as e:
            error_msg = f"\n调用大模型出错: {str(e)}"
            yield error_msg

    def check_connection(self) -> dict:
        try:
            self.client.models.list()
            return {
                "status": "ok",
                "message": f"连接成功！当前模型: {self.model}\nAPI 地址: {self.base_url}",
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"连接失败: {str(e)}\n请检查 .env 文件中的 API Key 和 Base URL 配置。",
            }
