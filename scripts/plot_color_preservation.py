"""Readable old/new preview panels from the recorded same-frame evaluation."""
import argparse,json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from semantic_debug_viewer import configure_fonts

def plot(root):
    configure_fonts()
    for case in ('blue_pipe','yellow_box','red_box'):
        folder=root/case
        fig,axes=plt.subplots(1,3,figsize=(15,4.2))
        for ax,m,title in zip(axes,['none','white_balance','range_preserve'],['原始水下图','旧白平衡：存在偏色风险','新预览：距离恢复＋保色提亮']):
            ax.imshow(plt.imread(folder/(m+'.png')));ax.set_title(title);ax.axis('off')
        fig.suptitle(case+'：显示画面对比，推荐配置的识别仍使用原图',fontsize=13)
        fig.tight_layout();fig.savefig(folder/'before_after.png',dpi=170);plt.close(fig)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('directory',type=Path);a=p.parse_args();plot(a.directory)
