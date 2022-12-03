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
