from dataclasses import dataclass, asdict
from collections import Counter

@dataclass
class StaticDanmakuSingleCid:
    """DanmakuStatic类中使用, 用于储存每个分 P 或每个 Ep 的所有弹幕的 Counter对象)"""
    title: str
    cid_counter: Counter

    def to_dict(self):
        return asdict(self)