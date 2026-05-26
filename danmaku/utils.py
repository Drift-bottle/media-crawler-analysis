import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

# ------设置图表字体------
def create_font(font_path):
    """
    为图表设置全局字体
    Args:
        font_path: 图表用的字体完整路径
    """
    # 把文件字体添加到 fontManager
    fm.fontManager.addfont(font_path)

    # 获取该字体的系统名称
    font_name = fm.FontProperties(fname=font_path).get_name()

    # 设置为全局默认
    plt.rcParams['font.sans-serif'] = [font_name, 'SimHei', 'DejaVu Sans']
    plt.rcParams['axes.unicode_minus'] = False