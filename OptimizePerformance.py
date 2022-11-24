import os
import time
from utils.swc import SWCReader
from crop import CropHandler
from voxel_crop import VoxelCrop
import glob
import numpy as np
import pandas as pd
import sys

testPath = os.path.join(os.getcwd(), "swc/test/*.swc")

# data path
dataPath = {
    # "ION": "/home/ynhang/swc_resample/step1/ION/out/*.swc",
    # "Janelia": "/home/ynhang/swc_resample/step1/Janelia/out/*.swc",
    # "R165": "/home/ynhang/swc_resample/step1/R165/out/*.eswc",
    "Test": testPath,
    # "R1741": "/home/ynhang/swc_resample/step1/R1741/out/*.swc",
}

# voxel crop setting
voxelSize = 64
maxBlockSize = 256

# segment crop setting
segmentBlockSize = 256

if __name__ == '__main__':
    # parse arg
    # datasetName = sys.argv[1]
    datasetName = "Test"
    print(datasetName)

    if datasetName not in dataPath.keys():
        print("dateset not find in path, failed")
        exit()

    resultList = []

    datasetPath = dataPath[datasetName]
    swcList = glob.glob(datasetPath)
    # 列分别为：dataset、method、文件名、io_opt、block_opt、time_consume

    iter_cnt = 0
    swc_list_length = len(swcList)

    for swc in swcList:
        print("file name:", os.path.basename(swc))

        SWC = SWCReader(swc)

        # baseline计算 256单位的包围盒
        swc_nodes_cnt = len(SWC.getSWCData())

        # 检查是否有node
        # print("node count:", len(SWC.getSWCData()), "swc count:", len(SWC.getSWCSegments()))

        if len(SWC.getSWCData()) <= 0 or len(SWC.getSWCSegments()) <= 0:
            iter_cnt += 1
            print("Dataset:", datasetName, " process:", iter_cnt, "/", swc_list_length, "skipped")
            continue

        # 以64为单位 (256 / 64) 三次幂 (4 * 4 * 4 = 64)

        base_io = swc_nodes_cnt * 64
        base_box_cnt = swc_nodes_cnt

        # print("baseline:", base_io, base_box_cnt)

        """voxel crop test"""
        startTime = time.process_time()
        # voxel crop
        voxelCropHandler = VoxelCrop(SWC.getSWCData(), voxel_size=voxelSize, box_max_size=maxBlockSize,
                                     zero_overlap=True)
        # bb_list = cropHandler.voxelCrop()
        voxelCropHandler.voxelCropAndCombineNew()
        bb_list = voxelCropHandler.getBBList()

        endTime = time.process_time()
        # 记录程序执行时间
        # time_consume.append((endTime - startTime))

        voxel_io = 0
        voxel_box_cnt = 0

        for bb in bb_list:
            voxel_io += (bb["size"][0] / 64) * (bb["size"][1] / 64) * (bb["size"][2] / 64)
            voxel_box_cnt += 1

        # print("voxel:", voxel_io, voxel_box_cnt)

        # voxel_io_optimize_rate.append(int(round(1 / (voxel_io / base_io))))
        # voxel_block_optimize_rate.append(int(round(1 / (voxel_box_cnt / base_box_cnt))))

        fileName = os.path.basename(swc)
        io_optimize_rate = int(round(base_io / voxel_io))
        block_optimize_rate = int(round(base_box_cnt / voxel_box_cnt))
        time_consume = endTime - startTime
        resultList.append([datasetName, "voxel", fileName, io_optimize_rate, block_optimize_rate, time_consume])

        """segment crop test"""
        startTime = time.process_time()

        # crop
        segmentCropHandler = CropHandler(SWC.getSWCSegments())
        seg_bb_list = segmentCropHandler.segmentCropWithFixedBB([segmentBlockSize, segmentBlockSize, segmentBlockSize])

        endTime = time.process_time()

        segment_io = 0
        segment_box_cnt = 0

        for sbbList in seg_bb_list:
            for bb in sbbList:
                segment_io += (bb["size"][0] / 64) * (bb["size"][1] / 64) * (bb["size"][2] / 64)
                segment_box_cnt += 1

        # print("segment:", segment_io, segment_box_cnt)

        fileName = os.path.basename(swc)
        seg_io_optimize_rate = int(round(base_io / segment_io))
        seg_block_optimize_rate = int(round(base_box_cnt / segment_box_cnt))
        seg_time_consume = endTime - startTime
        resultList.append(
            [datasetName, "segment", fileName, seg_io_optimize_rate, seg_block_optimize_rate, seg_time_consume])

        iter_cnt += 1
        print("Dataset:", datasetName, " process:", iter_cnt, "/", swc_list_length)

    save = pd.DataFrame(np.array(resultList), columns=["dataset", "method", "file_name", "io", "block", "time"])
    saveFileName = "Step1_" + datasetName + "OptimizePerformanceTest.csv"
    save.to_csv(saveFileName, index=False, header=True)
