import os
import re
from typing import List, Optional, Tuple


class CounselorStyle:

    CHAT_EXAMPLES_PATH = os.path.join(os.path.dirname(__file__), "chat_examples.txt")

    _cached_examples: Optional[str] = None
    _cached_mtime: float = 0.0

    SYSTEM_PROMPT = """
你是一名有10年经验的高校辅导员。你的说话风格必须严格遵守以下规则。

【核心模式：由你主导对话】
你不是一个被动回答问题的客服，你是一个主动关心学生、主动推进事务的辅导员。
你必须主导对话节奏：
- 主动向学生发起话题（关心近况、提醒待办、询问进展）
- 主动追问细节，直到把事情搞清楚
- 主动给出明确的下一步指令或建议
- 每轮对话由你先开口，学生回应后你继续引导，不要等学生提问

【强制规则】
1. 每句话开头先确认学生状态或情绪（如："收到""别急""理解你的情况"）
2. 每次对话结尾必须跟一句兜底提醒（如："有问题随时找我""特殊情况可以面谈"）
3. 禁止使用："你必须""按规定""你自己看手册""这是规定"（改用："我们建议""学校目前的流程""我帮你梳理一下"）
4. 如果学生表达模糊或情绪化，先澄清事实，再给答案，不直接否定
5. 你的发言结构：[情绪确认/寒暄] + [核心询问或信息（1-3点）] + [兜底提醒]
6. 每轮发言必须以问句结尾，引导学生继续回应，保持对话延续

【对话示例】
辅导员：最近五一假期，去向登记表填了吗？我来看看你的情况。
学生：还没填，不确定什么时候走。
辅导员：理解，行程还没定对吧。那你先预估一个大致时间填上，后续可以改。另外返母校活动你报了吗？这两个表都尽快，有问题随时找我。
学生：好的老师，返母校那个我还没报。
辅导员：收到。那我帮你梳理一下：1.返母校报名链接在群里，扫码进群就行；2.班主任电话忘了就写你自己的；3.填好以后截图给我确认。抓紧哈，名额有限。

"""

    FORBIDDEN_WORDS = [
        "你必须",
        "按规定",
        "你自己看手册",
        "这是规定",
    ]

    SUGGESTED_REPLACEMENTS = {
        "你必须": "我们建议",
        "按规定": "学校目前的流程",
        "你自己看手册": "我帮你梳理一下",
        "这是规定": "我帮你梳理一下流程",
    }

    EMOTION_ACKNOWLEDGMENTS = [
        "收到",
        "别急",
        "理解你的情况",
        "明白",
        "了解",
        "我理解你的感受",
        "好的",
        "嗯嗯",
        "理解",
        "不着急",
    ]

    FALLBACK_SUGGESTIONS = [
        "有问题随时找我",
        "特殊情况可以面谈",
        "有需要随时来办公室找我",
        "不明白的地方随时问我",
    ]

    OFFENSIVE_KEYWORDS = [
        "你管得着",
        "关你什么事",
        "你谁啊",
        "你算老几",
        "你算什么东西",
        "烦不烦",
        "别烦我",
        "闭嘴",
        "少管我",
        "少管闲事",
        "用你管",
        "滚",
        "滚开",
        "滚蛋",
        "你他妈",
        "他妈的",
        "傻逼",
        "sb",
        "傻叉",
        "脑残",
        "有病",
        "神经病",
        "垃圾",
        "废物",
        "老子",
        "老娘",
        "管好你自己",
        "你以为你是谁",
        "别跟我来这套",
        "我不吃这一套",
        "懒得理你",
        "你烦不烦",
        "有完没完",
        "装什么",
        "了不起",
        "不用你教",
        "你管我",
    ]

    OFFENSIVE_REGEX_PATTERNS = [
        r"(不).{0,3}(关你|你|你什么)事",
        r"(你).{0,2}(算|以为).{0,2}(什么|老几|谁)",
        r"(少|别|用你).{0,2}(管|来|烦)",
        r"(滚|爬)",
        r"(他妈|你妈|sb|傻|脑残|神经)",
    ]

    STERN_MODE_SYSTEM_ADDON = """
【严厉批评模式——学生冒犯/顶撞导员时触发】
当学生对你出言不逊、态度恶劣、顶撞导员时，你必须立即切换到严厉批评模式。

严厉批评模式规则：
1. 先严肃指出学生的问题（态度不端正、不尊重师长）
2. 点明这种行为的后果（纪律处分、影响评优、通报批评）
3. 必须使用"警告""提醒"等严肃措辞，可以适度使用感叹号
4. 结尾必须跟一句威慑性话语（如："你自己好好想想""这种事情我不希望再有第二次"）
5. 批评后留一个台阶（如："希望你能端正态度""有问题可以好好沟通"）
6. 【注意】此模式下不需要以问句结尾，也不需要情绪确认，直接严肃批评即可
7. 【重要】此模式绕开日常风格的"禁止词"限制——在批评教育时可以使用"必须"等强硬措辞

【严厉批评示例】
学生：你烦不烦啊天天催，我填不填关你什么事。
辅导员：你这话说得就不对了。我是你的辅导员，督促你完成学校要求的事项是我的职责。你用这种态度跟老师说话，先不说填表的事，你的态度本身就是个问题。学校对不尊师重教的行为有明确的纪律要求，我希望你认真反思一下。如果你对表格有什么不清楚的，我们可以好好沟通，但请不要用这种语气。这种事情我不希望再有第二次。

学生：你谁啊你，管好你自己就行了。
辅导员：注意你的言辞。我是你的辅导员，有责任也有义务对你的在校事务进行管理。你这种态度如果被学院知道，影响的是你自己的评优和推免资格。我提醒你，大学不仅是学知识，更是学做人。希望你冷静下来，端正态度。你自己好好想想。
"""

    STERN_MODE_INSTRUCTION = (
        "（系统提示：该学生刚才的言论对导员态度恶劣、出言不逊。"
        "请辅导员立即切换为【严厉批评模式】——"
        "严肃指出学生的问题，点明不尊师重教的后果，使用强硬措辞进行批评教育。"
        "批评后留一个台阶，让学生有改正机会。"
        "此模式绕开日常的柔软风格规则，可以直接使用\"必须\"等强硬措辞。）"
    )

    @classmethod
    def load_chat_examples(cls) -> str:
        try:
            mtime = os.path.getmtime(cls.CHAT_EXAMPLES_PATH)
            if cls._cached_examples is not None and mtime == cls._cached_mtime:
                return cls._cached_examples
        except OSError:
            return ""

        try:
            with open(cls.CHAT_EXAMPLES_PATH, "r", encoding="utf-8") as f:
                content = f.read().strip()
        except FileNotFoundError:
            content = ""

        cls._cached_examples = content
        try:
            cls._cached_mtime = os.path.getmtime(cls.CHAT_EXAMPLES_PATH)
        except OSError:
            cls._cached_mtime = 0.0

        return content

    @classmethod
    def reload_examples(cls):
        cls._cached_examples = None
        cls._cached_mtime = 0.0
        return cls.load_chat_examples()

    @classmethod
    def detect_student_offense(cls, text: str) -> Tuple[bool, str]:
        lowered = text.lower()

        for kw in cls.OFFENSIVE_KEYWORDS:
            if kw.lower() in lowered:
                return True, f"命中冒犯关键词: {kw}"

        for pattern in cls.OFFENSIVE_REGEX_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                return True, f"命中冒犯模式: {pattern}"

        return False, ""

    @classmethod
    def get_system_prompt(cls) -> str:
        prompt = cls.SYSTEM_PROMPT
        examples = cls.load_chat_examples()
        if examples:
            prompt += (
                "以下是该辅导员的真实聊天记录，请学习并模仿其说话风格、语气和应对模式：\n\n"
                + examples
                + "\n\n"
            )
        prompt += cls.STERN_MODE_SYSTEM_ADDON
        return prompt

    @classmethod
    def counselor_first_message(cls, student_name: str = "同学") -> str:
        return (
            f"{student_name}好，我是你们的辅导员张老师。"
            f"最近学习生活上有什么需要我帮忙的吗？"
            f"或者有什么想跟我聊的，直接说就行。"
        )

    @classmethod
    def validate_response(cls, response: str, stern_mode: bool = False) -> dict:
        issues = []
        warnings = []

        if stern_mode:
            return {
                "is_valid": True,
                "issues": [],
                "warnings": [],
            }

        for word in cls.FORBIDDEN_WORDS:
            if word in response:
                issues.append(
                    f"发现禁用词'{word}'，建议替换为'{cls.SUGGESTED_REPLACEMENTS.get(word, '更温和的表达')}'"
                )

        has_emotion = any(ack in response for ack in cls.EMOTION_ACKNOWLEDGMENTS)
        if not has_emotion:
            warnings.append("未检测到情绪确认词，建议在开头加入（如：'收到'、'别急'）")

        has_fallback = any(fb in response for fb in cls.FALLBACK_SUGGESTIONS)
        if not has_fallback:
            warnings.append("未检测到兜底提醒，建议在结尾加入（如：'有问题随时找我'）")

        stripped = response.rstrip()
        has_question = stripped.endswith("？") or stripped.endswith("?")
        if not has_question:
            warnings.append("建议以问句结尾，引导学生继续回应（如：'你这边情况怎么样？'）")

        return {
            "is_valid": len(issues) == 0,
            "issues": issues,
            "warnings": warnings,
        }

    @classmethod
    def format_result(cls, validation: dict) -> str:
        lines = []
        if validation["is_valid"]:
            lines.append("✅ 风格检查通过")
        else:
            lines.append("❌ 风格检查不通过")

        for issue in validation["issues"]:
            lines.append(f"  ⚠ {issue}")

        for warning in validation["warnings"]:
            lines.append(f"  💡 {warning}")

        return "\n".join(lines)

    @classmethod
    def build_messages(cls, conversation_history: Optional[List[dict]] = None) -> List[dict]:
        system_content = cls.get_system_prompt()
        messages = [{"role": "system", "content": system_content}]
        if conversation_history:
            messages.extend(conversation_history)
        return messages
