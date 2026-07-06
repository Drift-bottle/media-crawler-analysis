import matplotlib.pyplot as plt
import emoji
import re
from wordcloud import WordCloud
from collections import Counter
from models import StaticDanmakuSingleP
import json
import ijson
import os
import logging
from typing import List, Any


def json_data_is_not_empty(filepath, logger):
    """
    判断文件是否成功存入数据
    Args:
        filepath: 文件路径
        logger: Logger
    """
    if not os.path.isfile(filepath) or os.path.getsize(filepath) == 0:
        return False
    with open(filepath, 'r', encoding='utf-8') as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError as e:
            logger.error(f"❌加载文件出问题 | {type(e).__name__}: {e}, 可能不是合法的 JSON")
            return False
    # 检查'无数据'形态
    if data is None:
        return False
    elif isinstance(data, (dict, list, str)):
        if isinstance(data, str) and len(data.strip()) > 0:
            return True
        elif len(data) > 0:
            return True
        else:
            return False
    # 其他类型(数字、布尔值等)通常视为"有数据"
    return True


class SaveData:
    """保存解析后的数据"""
    def __init__(self, data: List[Any], filepath: str, logger=None):
        self.data = data # 解析后的数据
        self._filepath = filepath # 储存弹幕数据的完整路径
        self.logger = logger or logging.getLogger(__name__) # 设置logger

    def save_to_json(self) -> None:
        """将数据储存到json文件中"""
        if len(self.data) == 0:
            err = "❌没有储存到数据"
            self.logger.error(err)
            raise Exception(err)
        danmaku_dict = [danmaku.to_dict() if hasattr(danmaku, 'to_dict') else danmaku for danmaku in self.data]
        with open(self._filepath, 'w', encoding='utf-8') as f:
            json.dump(danmaku_dict, f, ensure_ascii=False, indent=4)
        if json_data_is_not_empty(self._filepath, logger=self.logger):
            self.logger.info(f"✅数据已储存到{self._filepath}")
        else:
            err = f"❌数据未储存到{self._filepath}"
            self.logger.error(err)
            raise Exception(err)


# ------词频统计类------
class DanmakuStatic:
    """进行词频统计和数据清洗"""
    def __init__(self, filepath, static_path, logger=None):
        self._filepath = filepath # 储存弹幕数据的完整路径
        self._static_path = static_path # 储存词频统计结果的完整路径
        self._counter_list = []  # 储存所有分 P 或 Ep 的 counter 对象
        self.logger = logger or logging.getLogger(__name__)  # 设置logger

    def load_stopwords(self, filename='stopwords.txt'):
        """加载停用词列表"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                stopwords = [stopword.strip() for stopword in f]
            return stopwords
        except FileNotFoundError:
            return set()

    def word_frequency(self, stopwords=None, min_len=2):
        """对弹幕列表进行分词并统计词频, 生成储存 counter 对象的列表"""
        with open(self._filepath, 'r', encoding='utf-8') as f:
            for item in ijson.items(f, 'item'):
                # 将所有弹幕合并为一个字符串
                title = item['title'] # 获取分 P 或 Ep 的标题
                danmaku_p_list = item['danmaku_p_list'] # 获取分 P 或 Ep 的弹幕列表

                danmaku_p_list_copy = []  # 储存每个分 P 或每个 Ep 的弹幕数据
                for danmaku_content in danmaku_p_list:
                    # 获取单个弹幕内容
                    content = danmaku_content

                    # 过滤 stopwords
                    if stopwords and content in stopwords:
                        continue

                    # 过滤纯数字/日期文本
                    if re.match(r'^[\d\s\-/:.年月日]+$', content):
                        continue

                    # 去除重复字符
                    i = 0
                    base_word = content[0]
                    for w in content:
                        if w == base_word:
                            i += 1
                            if i >= 2 and w == content[1]:
                                break
                    if i >= 2:
                        continue

                    # 清洗数据
                    w = emoji.replace_emoji(content, replace='')
                    w = re.sub(r"[！？。、；：“”‘’【】《》～（）…—!?',;:()\[\]{}<>~@#$%^&*+=|\\/]", '', w)
                    if not w or w in stopwords:
                        continue
                    if len(w) < min_len:
                        continue

                    danmaku_p_list_copy.append(w)

                # 创建储存每个分 P 或 Ep 的 Counter 对象
                p_counter = Counter(danmaku_p_list_copy)
                # 创建 StaticDanmakuSingleP 对象
                danmaku_p_dict_copy = StaticDanmakuSingleP(title=title, p_counter=p_counter)
                self._counter_list.append(danmaku_p_dict_copy)


    def save_frequency(self, top_num=20):
        """将词频统计结果保存到文件, 并按频率降序输出前 top_num 个"""
        all_word = [] # 储存所有分 P 或 Ep 词频统计结果
        with open(self._static_path, 'w', encoding='utf-8') as f:
            for counter_dict in self._counter_list:
                word_p_dict = {} # 储存单个分 P 或 Ep 的词频统计结果(带分P标题)
                word_p_p_dict = {} # 储存单个分 P 或 Ep 的词频统计结果

                # 直接获取标题和 Counter 对象
                title = counter_dict.title
                p_counter = counter_dict.p_counter

                for word, count in p_counter.most_common(top_num):
                    word_p_p_dict[word] = count
                word_p_dict[title] = word_p_p_dict
                all_word.append(word_p_dict)
            json.dump(all_word, f, ensure_ascii=False, indent=4)
        if json_data_is_not_empty(self._static_path, logger=self.logger):
            self.logger.info(f"✅数据已储存到{self._static_path}")
        else:
            err = f"❌数据未储存到{self._static_path}"
            self.logger.error(err)
            raise Exception(err)


# ------数据可视化类------
class Visualization:
    """数据可视化, 生成词云图和条形图的组合图形"""
    def __init__(self, static_path, doc_path, font_path, logger=None):
        self.static_path = static_path # 储存词频统计结果的完整路径
        self.doc_path = doc_path # 储存生成的条形图和词云图的文件夹路径
        self.font_path = font_path  # 图表用的字体
        self.logger = logger or logging.getLogger(__name__) # 设置logger

    def create_combined_chart(self, freq_dict: dict, title: str, main_path: str, num: int):
        """
        将词云图和条形图组合到一张16:9的画布上
        Args:
            freq_dict: 词云图和条形图所需的词频字典
            title: 图表和图片的标题
            main_path: 图片保存的主路径
            num: 图表的序号(从 1 开始)
        """
        # 创建画布, 设置16:9的比例(宽度16英寸，高度9英寸)
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 9))

        # ---- 左侧: 词云图 ----
        wc = WordCloud(
            font_path=self.font_path,  # 支持中文的字体文件路径
            background_color="white",
            width=800,  # 词云图的内部分辨率
            height=450,
            colormap="OrRd", # 橙红配色
            prefer_horizontal=0.9  # 优先横排文字, 方便阅读
        )
        wc.generate_from_frequencies(freq_dict)
        ax1.imshow(wc, interpolation='bilinear')
        ax1.axis('off')  # 隐藏坐标轴
        ax1.set_title(f'{title}', fontsize=16, fontweight='bold')

        # ---- 右侧: 条形图 ----
        # 获取词和词频
        words = [word for word in freq_dict.keys()]
        freqs = [freq for freq in freq_dict.values()]

        # 绘制水平条形图(y 轴为词, x 轴为词频)
        ax2.barh(words, freqs, color='#5B9BD5')  # 使用一种柔和的蓝色
        ax2.set_xlabel('出现次数', fontsize=14)
        ax2.set_title(f'{title} - 高频词汇 Top 20', fontsize=16, fontweight='bold')

        # 调整y轴标签的字体大小, 避免标签过长导致重叠
        ax2.tick_params(axis='y', labelsize=10)

        # 自动调整子图之间的间距, 防止标题和文字重叠
        plt.tight_layout()

        # 保存图片
        save_path = os.path.join(main_path, f'{num}_{title}.png')
        fig.savefig(save_path, dpi=150, bbox_inches='tight')
        plt.close(fig)  # 释放内存

        return save_path


    def save_combined_figure(self):
        """保存同时具有词云图和条形图的图片"""
        # 获取文件夹路径
        path = self.doc_path
        # 创建文件夹
        os.makedirs(path, exist_ok=True)

        with open(self.static_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

            for i, word_p_dict in enumerate(data):
                for title, word_p_p_dict in word_p_dict.items():
                    try:
                        # 生成并保存组合图片
                        save_path = self.create_combined_chart(word_p_p_dict, title, path, i + 1)

                        # 设置文件夹中应有的文件数
                        formal_num = i + 1

                        # 文件夹中实际文件数
                        real_num = len(os.listdir(path))

                        # 验证图片是否成功保存
                        if os.path.isfile(save_path) and os.path.getsize(save_path) > 0:
                            self.logger.info(f"✅第 {i + 1} 张图表已保存至{path}")
                        else:
                            self.logger.error(f"❌第 {i + 1} 张图表未保存至{path} | save_path: {save_path} | 应有文件数: {formal_num} | 实际文件数: {real_num}")
                    except Exception as e:
                        self.logger.error(f"❌ create_combined_chart | {type(e).__name__}: {e}")