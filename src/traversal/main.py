import glob
import json
import os
from utils.swc import SWCReader


class BaselineCropHandler:
    def __init__(self, swc_nodes, box_size=256):
        self.swcNodes = swc_nodes
        self.boxSize = box_size
        pass

    def baselineCrop(self):
        bb_list = []

        for node in self.swcNodes:
            tempBox = {
                "pos": [node["x"], node["y"], node["z"]],
                "size": [self.boxSize, self.boxSize, self.boxSize]
            }
            bb_list.append(tempBox)

        return bb_list


if __name__ == '__main__':
    swcDirPath = os.path.join(os.getcwd(), "input")
    swcFilePathList = glob.glob(os.path.join(swcDirPath, "*"))

    for swcPath in swcFilePathList:
        SWC = SWCReader(swcPath)
        swcNodes = SWC.getSWCData()

        # crop
        # cropHandler = VoxelCropHandler(swc_nodes, voxel_size=64, box_max_size=512)
        cropHandler = BaselineCropHandler(swcNodes)
        # bb_list = cropHandler.voxelCrop()
        bb_list = cropHandler.baselineCrop()

        swcName = os.path.basename(swcPath)
        jsonFileName = swcName.split(".")[0] + ".json"
        saveFilePath = os.path.join(os.getcwd(), "output", jsonFileName)

        # 记录bb list信息
        with open(saveFilePath, 'w') as f:
            json.dump(bb_list, f, indent=2, sort_keys=True, ensure_ascii=False)

        print(swcName, " finished")
