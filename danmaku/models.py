from dataclasses import dataclass, asdict
from collections import Counter

@dataclass
class DanmakuSingleP:
    """DanmakuCrawler类中使用, 用于储存每个分 P 所有分段的所有弹幕的列表"""
    title: str
    danmaku_p_list: list

    def to_dict(self):
        return asdict(self)

@dataclass
class StaticDanmakuSingleP:
    """DanmakuStatic类中使用, 用于储存每个分 P 所有分段的所有弹幕的 Counter对象)"""
    title: str
    p_counter: Counter

    def to_dict(self):
        return asdict(self)
