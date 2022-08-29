import copy
import os
import random

from utils.swc import SWCReader
from crop import CropHandler, VoxelCropHandler
import json
import glob
import matplotlib.pyplot as plt
import numpy as np


def CropAndCombineTest():
    # 读取所有的swc
    swc_path = os.path.join(os.getcwd(), "R1741/*.swc")
    print("---swc path---", swc_path)

    swc_list = glob.glob(swc_path)
    print(len(swc_list))

    swc_cnt = len(swc_list)

    # io 优化参数
    segment_io_optimize_rate = []
    voxel_io_optimize_rate = []

    # block 默认以64 x 64 x 64为最小单位
    # block 优化参数
    segment_block_optimize_rate = []
    voxel_block_optimize_rate = []

    # 平均信息密度
    cnt = 0
    for swc in swc_list:
        SWC = SWCReader(swc)

        # baseline计算 256单位的包围盒
        swc_nodes_cnt = len(SWC.getSWCData())
        base_io = swc_nodes_cnt * 64
        base_box_cnt = swc_nodes_cnt

        # segment crop
        swc_segments = SWC.getSWCSegments()
        segmentCropHandler = CropHandler(swc_segments)
        bb_list = segmentCropHandler.segmentCropWithFixedBB([256, 256, 256])

        segment_io = 0
        segment_box_cnt = 0

        for sbbList in bb_list:
            for bb in sbbList:
                segment_io += (bb["size"][0] / 64) * (bb["size"][1] / 64) * (bb["size"][2] / 64)
                segment_box_cnt += 1

        segment_io_optimize_rate.append(int(round(1 / (segment_io / base_io))))
        segment_block_optimize_rate.append(int(round(1 / (segment_box_cnt / base_box_cnt))))

        # voxel crop
        voxelCropHandler = VoxelCropHandler(SWC.getSWCData(), voxel_size=64, box_max_size=512)
        # bb_list = cropHandler.voxelCrop()
        bb_list2 = voxelCropHandler.voxelCropAndCombine()

        voxel_io = 0
        voxel_box_cnt = 0

        for bb in bb_list2:
            voxel_io += (bb["size"][0] / 64) * (bb["size"][1] / 64) * (bb["size"][2] / 64)
            voxel_box_cnt += 1

        voxel_io_optimize_rate.append(int(round(1 / (voxel_io / base_io))))
        voxel_block_optimize_rate.append(int(round(1 / (voxel_box_cnt / base_box_cnt))))

        print("swc:", cnt, "--finished")
        cnt += 1


    # 计算均值和标准差
    mean_segment_io_optimize_rate = np.mean(segment_io_optimize_rate)
    mean_voxel_io_optimize_rate = np.mean(voxel_io_optimize_rate)
    mean_segment_block_optimize_rate = np.mean(segment_block_optimize_rate)
    mean_voxel_block_optimize_rate = np.mean(voxel_block_optimize_rate)

    std_segment_io_optimize_rate = np.std(segment_io_optimize_rate, ddof=1)
    std_voxel_io_optimize_rate = np.std(voxel_io_optimize_rate, ddof=1)
    std_segment_block_optimize_rate = np.std(segment_block_optimize_rate, ddof=1)
    std_voxel_block_optimize_rate = np.std(voxel_block_optimize_rate, ddof=1)

    print(mean_segment_io_optimize_rate, mean_voxel_io_optimize_rate, mean_segment_block_optimize_rate, mean_voxel_block_optimize_rate)

    print(std_segment_io_optimize_rate, std_voxel_io_optimize_rate, std_segment_block_optimize_rate, std_voxel_block_optimize_rate)

    # io优化
    # x_data = ["baseline", "SegmentCrop", "VoxelCrop"]
    # y_data = []

    # block优化
    """plot figure mean"""
    io_opt_list = [mean_segment_io_optimize_rate, mean_voxel_io_optimize_rate]
    block_opt_list = [mean_segment_block_optimize_rate, mean_voxel_block_optimize_rate]

    # x轴坐标, size=5, 返回[0, 1, 2, 3, 4]
    x = np.arange(2)
    print(x)

    # 有a/b/c三种类型的数据，n设置为3
    total_width, n = 0.8, 2
    # 每种类型的柱状图宽度
    width = total_width / n

    # 画柱状图
    plt.bar(x - width / 2, io_opt_list, width=width, label="io_optimize")
    plt.bar(x + width / 2, block_opt_list, width=width, label="block_optimize")

    # x_labels = ["baseline", "SegmentCrop", "VoxelCrop"]
    x_labels = ["SegmentCrop", "VoxelCrop"]
    # 用第1组...替换横坐标x的值
    plt.xticks(x, x_labels)

    plt.title("Optimization effect using Segment Corp and Voxel Crop")

    # 显示图例
    plt.legend()
    # 显示柱状图
    plt.show()

    """plot figure std"""
    io_std_list = [std_segment_io_optimize_rate, std_voxel_io_optimize_rate]
    block_std_list = [std_segment_block_optimize_rate, std_voxel_block_optimize_rate]

    # x轴坐标, size=5, 返回[0, 1, 2, 3, 4]
    x = np.arange(2)
    print(x)

    # 有a/b/c三种类型的数据，n设置为3
    total_width, n = 0.8, 2
    # 每种类型的柱状图宽度
    width = total_width / n

    # 重新设置x轴的坐标
    # x = x - total_width / 2
    # print(x)

    # 画柱状图
    plt.bar(x - width / 2, io_std_list, width=width, label="std_io_optimize")
    plt.bar(x + width / 2, block_std_list, width=width, label="std_block_optimize")

    # x_labels = ["baseline", "SegmentCrop", "VoxelCrop"]
    x_labels = ["SegmentCrop", "VoxelCrop"]
    # 用第1组...替换横坐标x的值
    plt.xticks(x, x_labels)

    plt.title("Standard Deviation of Optimization effect")

    # 显示图例
    plt.legend()
    # 显示柱状图
    plt.show()


def ProofReadingTest():
    pass


if __name__ == '__main__':
    CropAndCombineTest()
    pass
