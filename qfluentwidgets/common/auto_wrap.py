"""自动换行相关工具模块"""

from enum import Enum, auto
from functools import lru_cache
from re import sub
from typing import List, Optional, Tuple
from unicodedata import east_asian_width


class CharType(Enum):
    """字符类型枚举"""

    SPACE = auto()
    ASIAN = auto()
    LATIN = auto()


class TextWrap:
    """文本自动换行工具类"""

    EAST_ASAIN_WIDTH_TABLE = {
        "F": 2,
        "H": 1,
        "W": 2,
        "A": 1,
        "N": 1,
        "Na": 1,
    }

    @classmethod
    @lru_cache(maxsize=128)
    def get_width(cls, char: str) -> int:
        """获取字符的显示宽度

        Args:
            char: 待计算的字符

        Returns:
            字符的显示宽度
        """
        return cls.EAST_ASAIN_WIDTH_TABLE.get(east_asian_width(char), 1)

    @classmethod
    @lru_cache(maxsize=32)
    def get_text_width(cls, text: str) -> int:
        """获取文本的显示宽度

        Args:
            text: 待计算的文本

        Returns:
            文本的显示宽度
        """
        return sum(cls.get_width(char) for char in text)

    @classmethod
    @lru_cache(maxsize=128)
    def get_char_type(cls, char: str) -> CharType:
        """获取字符的类型

        Args:
            char: 待判断的字符

        Returns:
            字符类型
        """

        if char.isspace():
            return CharType.SPACE

        if cls.get_width(char) == 1:
            return CharType.LATIN

        return CharType.ASIAN

    @classmethod
    def process_text_whitespace(cls, text: str) -> str:
        """处理文本中的空白字符

        将连续空白字符替换为单个空格，并去除首尾空格

        Args:
            text: 待处理的文本

        Returns:
            处理后的文本
        """
        return sub(pattern=r"\s+", repl=" ", string=text).strip()

    @classmethod
    @lru_cache(maxsize=32)
    def split_long_token(cls, token: str, width: int) -> List[str]:
        """将长 token 按指定宽度分割

        Args:
            token: 待分割的字符串
            width: 每个片段的最大宽度

        Returns:
            分割后的字符串片段列表
        """
        return [token[i : i + width] for i in range(0, len(token), width)]

    @classmethod
    def tokenizer(cls, text: str):
        """对文本进行分词

        根据字符类型将文本切分为 token

        Args:
            text: 待分词的文本

        Yields:
            分词后的 token
        """

        buffer = ""
        last_char_type: Optional[CharType] = None

        for char in text:
            char_type = cls.get_char_type(char)

            if buffer and (char_type != last_char_type or char_type != CharType.LATIN):
                yield buffer
                buffer = ""

            buffer += char
            last_char_type = char_type

        yield buffer

    @classmethod
    def wrap(cls, text: str, width: int, once: bool = True) -> Tuple[str, bool]:
        """根据宽度对文本进行自动换行

        Args:
            text: 待换行的文本
            width: 单行允许的最大宽度，中文字符按 2 个字符计算
            once: 是否只执行一次换行

        Returns:
            包含换行后的文本和是否发生换行的元组
        """

        width = int(width)
        lines = text.splitlines()
        is_wrapped = False
        wrapped_lines = []

        for line in lines:
            line = cls.process_text_whitespace(line)

            if cls.get_text_width(line) > width:
                wrapped_line, is_wrapped = cls._wrap_line(line, width, once)
                wrapped_lines.append(wrapped_line)

                if once:
                    wrapped_lines.append(text[len(wrapped_line) :].rstrip())
                    return "".join(wrapped_lines), is_wrapped

            else:
                wrapped_lines.append(line)

        return "\n".join(wrapped_lines), is_wrapped

    @classmethod
    def _wrap_line(cls, text: str, width: int, once: bool = True) -> Tuple[str, bool]:
        """对单行文本进行自动换行

        Args:
            text: 待换行的单行文本
            width: 单行允许的最大宽度
            once: 是否只执行一次换行

        Returns:
            包含换行后的文本和是否发生换行的元组
        """
        line_buffer = ""
        wrapped_lines = []
        current_width = 0

        for token in cls.tokenizer(text):
            token_width = cls.get_text_width(token)

            if token == " " and current_width == 0:
                continue

            if current_width + token_width <= width:
                line_buffer += token
                current_width += token_width

                if current_width == width:
                    wrapped_lines.append(line_buffer.rstrip())
                    line_buffer = ""
                    current_width = 0
            else:
                if current_width != 0:
                    wrapped_lines.append(line_buffer.rstrip())

                chunks = cls.split_long_token(token, width)

                for chunk in chunks[:-1]:
                    wrapped_lines.append(chunk.rstrip())

                line_buffer = chunks[-1]
                current_width = cls.get_text_width(chunks[-1])

        if current_width != 0:
            wrapped_lines.append(line_buffer.rstrip())

        if once:
            return "\n".join([wrapped_lines[0], " ".join(wrapped_lines[1:])]), True

        return "\n".join(wrapped_lines), True