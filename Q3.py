import os
import time

from utils.swc import SWCReader
from crop import CropHandler, VoxelCropHandler
import json
import glob
import numpy as np
import pandas as pd

"""-------------Q3 - （1）Voxel Crop时的Voxel大小选择---------------"""

datasetPath = os.path.join(os.getcwd(), "swc")
voxelSize = 64
maxBlockSize = 256


def DifferentVoxelSizeTest(dataset_path, voxel_size, max_block_size):
    # 读取所有的swc
    swc_list = glob.glob(dataset_path)

    """需要考虑的参数 IO Block Time"""
    # # io 优化参数
    # voxel_io_optimize_rate = []
    #
    # # 时间优化参数
    # time_consume = []
    #
    # # block 默认以64 x 64 x 64为最小单位
    # voxel_block_optimize_rate = []

    # 列分别为：文件名、io、image block、time consume
    resultList = []

    # 平均信息密度
    # cnt = 0
    for swc in swc_list:

        SWC = SWCReader(swc)

        # baseline计算 256单位的包围盒
        swc_nodes_cnt = len(SWC.getSWCData())

        # 以64为单位 (256 / 64) 三次幂
        base_io = swc_nodes_cnt * 64
        base_box_cnt = swc_nodes_cnt

        startTime = time.process_time()
        # voxel crop
        voxelCropHandler = VoxelCropHandler(SWC.getSWCData(), voxel_size=voxel_size, box_max_size=max_block_size)
        # bb_list = cropHandler.voxelCrop()
        bb_list = voxelCropHandler.voxelCropAndCombine()
        endTime = time.process_time()
        # 记录程序执行时间
        # time_consume.append((endTime - startTime))

        voxel_io = 0
        voxel_box_cnt = 0

        for bb in bb_list:
            voxel_io += (bb["size"][0] / 64) * (bb["size"][1] / 64) * (bb["size"][2] / 64)
            voxel_box_cnt += 1

        # voxel_io_optimize_rate.append(int(round(1 / (voxel_io / base_io))))
        # voxel_block_optimize_rate.append(int(round(1 / (voxel_box_cnt / base_box_cnt))))

        fileName = os.path.basename(swc)
        io_optimize_rate = int(round(1 / (voxel_io / base_io)))
        block_optimize_rate = int(round(1 / (voxel_box_cnt / base_box_cnt)))
        time_consume = endTime - startTime
        resultList.append([fileName, io_optimize_rate, block_optimize_rate, time_consume])

        # print("swc:", cnt, "--finished")
        # cnt += 1

    save = pd.DataFrame(np.array(resultList), columns=["file_name", "io", "block", "time"])
    saveFileName = str(voxel_size) + "_" + str(max_block_size) + ".csv"
    save.to_csv(saveFileName, index=False, header=True)


if __name__ == '__main__':
    DifferentVoxelSizeTest(datasetPath, voxelSize, maxBlockSize)