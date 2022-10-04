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

dataPathDict = {
    # "step1": "/home/ynhang/swc_resample/step1/R1741/out/*.swc",
    "step5": "/home/ynhang/swc_resample/step5/R1741/out/*.swc"
}


def SampleStepSensitiveTest(datasetDict):
    # 读取所有的swc

    for step, path in datasetDict.items():
        swc_list = glob.glob(path)
        """需要考虑的参数 IO Block Time"""
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
            voxelCropHandler = VoxelCropHandler(SWC.getSWCData(), voxel_size=64, box_max_size=256)
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
        saveFileName = "./results/sensitive_" + str(step) + ".csv"
        save.to_csv(saveFileName, index=False, header=True)


def MethodsCompare(datasetDict):
    for step, path in datasetDict.items():
        swc_list = glob.glob(path)
        """需要考虑的参数 IO Block Time"""

        # baselineResultList = []

        segmentResultList = []
        voxelResultList = []

        # 平均信息密度
        # cnt = 0
        for swc in swc_list:

            SWC = SWCReader(swc)

            # baseline计算 256单位的包围盒
            swc_nodes_cnt = len(SWC.getSWCData())

            # 以64为单位 (256 / 64) 三次幂
            base_io = swc_nodes_cnt * 64
            base_box_cnt = swc_nodes_cnt

            """segment crop"""
            startTime = time.process_time()
            swc_segments = SWC.getSWCSegments()
            segmentCropHandler = CropHandler(swc_segments)
            bb_list = segmentCropHandler.segmentCropWithFixedBB([256, 256, 256])
            endTime = time.process_time()

            segment_io = 0
            segment_box_cnt = 0

            for sbbList in bb_list:
                for bb in sbbList:
                    segment_io += (bb["size"][0] / 64) * (bb["size"][1] / 64) * (bb["size"][2] / 64)
                    segment_box_cnt += 1

            fileName = os.path.basename(swc)
            io_optimize_rate = int(round(1 / (segment_io / base_io)))
            block_optimize_rate = int(round(1 / (segment_box_cnt / base_box_cnt)))
            time_consume = endTime - startTime
            segmentResultList.append([fileName, io_optimize_rate, block_optimize_rate, time_consume])

            """voxel crop"""
            startTime = time.process_time()
            # voxel crop
            voxelCropHandler = VoxelCropHandler(SWC.getSWCData(), voxel_size=64, box_max_size=256)
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

            fileName = os.path.basename(swc)
            io_optimize_rate = int(round(1 / (voxel_io / base_io)))
            block_optimize_rate = int(round(1 / (voxel_box_cnt / base_box_cnt)))
            time_consume = endTime - startTime
            voxelResultList.append([fileName, io_optimize_rate, block_optimize_rate, time_consume])

            # print("swc:", cnt, "--finished")
            # cnt += 1

        save = pd.DataFrame(np.array(segmentResultList), columns=["file_name", "io", "block", "time"])
        saveFileName = "./results/Q4_segment" + str(step) + ".csv"
        save.to_csv(saveFileName, index=False, header=True)

        save = pd.DataFrame(np.array(voxelResultList), columns=["file_name", "io", "block", "time"])
        saveFileName = "./results/Q4_voxel" + str(step) + ".csv"
        save.to_csv(saveFileName, index=False, header=True)

    pass


if __name__ == '__main__':
    # SampleStepSensitiveTest(dataPathDict)
    MethodsCompare(datasetDict=dataPathDict)
