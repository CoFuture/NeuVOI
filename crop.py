import copy


# 包围盒的基本操作
class AABBBox:
    def __init__(self, pmin, pmax, size_threshold=None):
        # bounding box的两个基本属性
        # pmin = [x_min, y_min, z_min]

        if size_threshold is None:
            self.sizeThreshold = [256, 256, 256]
        else:
            self.sizeThreshold = size_threshold

        self.pmin = pmin
        self.pmax = pmax

    # bbox中添加一个新点
    def addNode(self, node_pos):
        # 向AABB中添加一个节点
        x_min = min(node_pos[0], self.pmin[0])
        x_max = max(node_pos[0], self.pmax[0])
        if x_max - x_min > self.sizeThreshold[0]:
            return False

        y_min = min(node_pos[1], self.pmin[1])
        y_max = max(node_pos[1], self.pmax[1])
        if y_max - y_min > self.sizeThreshold[1]:
            return False

        z_min = min(node_pos[2], self.pmin[2])
        z_max = max(node_pos[2], self.pmax[2])
        if z_max - z_min > self.sizeThreshold[2]:
            return False

        # AABB符合要求 添加进去
        self.pmin = [x_min, y_min, z_min]
        self.pmax = [x_max, y_max, z_max]
        return True

    # 设置包围盒大小阈值
    def setSizeThreshold(self, size_threshold):
        self.sizeThreshold = size_threshold

    # 返回x_size, y_size, z_size
    def getSize(self):
        return self.pmax[0] - self.pmin[0], self.pmax[1] - self.pmin[1], self.pmax[2] - self.pmin[2]

    def getCenter(self):
        center = [(self.pmin[0] + self.pmax[0]) / 2, (self.pmin[1] + self.pmax[1]) / 2,
                  (self.pmin[2] + self.pmax[2]) / 2]
        return center


# segment crop
class CropHandler:
    def __init__(self, swc_segments):
        self.swcSegments = swc_segments

    def segmentCropWithFixedBB(self, bb_size=None):
        if bb_size is None:
            sizeThreshold = [256, 256, 256]
        else:
            sizeThreshold = bb_size

        # bounding box list
        bb_list = []

        # 遍历segments
        for seg in self.swcSegments:
            seg_bb_list = []
            # node in a AABB
            node_list = []

            # 包围盒对象
            box = None

            for node in seg:
                # 获取node pos
                node_pos = [node["x"], node["y"], node["z"]]

                if len(node_list) == 0:
                    # 保存node
                    node_list.append(node["idx"])
                    # 新建一个box
                    box = AABBBox(node_pos, node_pos, size_threshold=sizeThreshold)
                else:
                    # 计算 node 加入后的bb
                    if box.addNode(node_pos):
                        # 成功加入box
                        node_list.append(node["idx"])
                    else:
                        # 导出bb
                        bb_center = box.getCenter()
                        bb_info = {
                            "pos": bb_center,
                            "size": bb_size,
                            "nodes": copy.deepcopy(node_list)
                        }
                        seg_bb_list.append(bb_info)

                        # 初始化基础对象
                        node_list = [node["idx"]]
                        # aabb 基本信息
                        del box
                        box = AABBBox(node_pos, node_pos, size_threshold=sizeThreshold)

            # 最后一个bb的处理
            bb_center = box.getCenter()
            bb_info = {
                "pos": bb_center,
                "size": bb_size,
                "nodes": copy.deepcopy(node_list)
            }
            seg_bb_list.append(bb_info)

            # 添加到总体的list中
            bb_list.append(seg_bb_list)

        return bb_list


#
class VoxelCropHandler:
    def __init__(self, swc_nodes, voxel_size=64, box_max_size=256):
        self.swcNodes = swc_nodes

        # voxel grid相关参数
        self.voxelSize = voxel_size

        self.boxMaxSize = box_max_size

        # voxel划分信息
        self.dx = -1
        self.dy = -1
        self.dz = -1

    # 获取index邻域block的index
    def getAdjacentList(self, b_index):
        index_list = []

        if self.dx == -1 or self.dy == -1 or self.dz == -1:
            return index_list

        total_block = self.dx * self.dy * self.dz

        if 0 <= b_index - 1 < total_block:
            index_list.append(b_index - 1)

        if 0 <= b_index + 1 < total_block:
            index_list.append(b_index + 1)

        if 0 <= b_index - self.dx < total_block:
            index_list.append(b_index - self.dx)

        if 0 <= b_index + self.dx < total_block:
            index_list.append(b_index + self.dx)

        if 0 <= b_index - self.dx * self.dy < total_block:
            index_list.append(b_index - self.dx * self.dy)

        if 0 <= b_index + self.dx * self.dy < total_block:
            index_list.append(b_index + self.dx * self.dy)

        return index_list

    def isAdjacent(self, b_index1, b_index2):

        pass

    def voxelCrop(self, box_padding=5):
        # 计算AABB
        x_min = self.swcNodes[0]["x"]
        x_max = self.swcNodes[0]["x"]

        y_min = self.swcNodes[0]["y"]
        y_max = self.swcNodes[0]["y"]

        z_min = self.swcNodes[0]["z"]
        z_max = self.swcNodes[0]["z"]

        for node in self.swcNodes:
            x_min = min(node["x"], x_min)
            x_max = max(node["x"], x_max)

            y_min = min(node["y"], y_min)
            y_max = max(node["y"], y_max)

            z_min = min(node["z"], z_min)
            z_max = max(node["z"], z_max)

        # voxel grid 操作
        x_min = x_min - box_padding
        x_max = x_max + box_padding

        y_min = y_min - box_padding
        y_max = y_max + box_padding

        z_min = z_min - box_padding
        z_max = z_max + box_padding

        dx = (x_max - x_min) // self.voxelSize + 1
        dy = (y_max - y_min) // self.voxelSize + 1
        dz = (z_max - z_min) // self.voxelSize + 1

        voxel_grid = {}
        for node in self.swcNodes:
            # 计算index
            hx = (node["x"] - x_min) // self.voxelSize
            hy = (node["y"] - y_min) // self.voxelSize
            hz = (node["z"] - z_min) // self.voxelSize

            grid_index = hx + hy * dx + hz * dx * dy
            if str(grid_index) in voxel_grid:
                voxel_grid[str(grid_index)]["nodes"].append(node["idx"])
            else:
                grid_pos = [
                    x_min + hx * self.voxelSize + self.voxelSize / 2,
                    y_min + hy * self.voxelSize + self.voxelSize / 2,
                    z_min + hz * self.voxelSize + self.voxelSize / 2,
                ]
                voxel_grid[str(grid_index)] = {
                    "pos": grid_pos,
                    "size": [self.voxelSize, self.voxelSize, self.voxelSize],
                    "nodes": [node["idx"]]
                }

        # todo block combine

        #

        # dict to list处理
        voxel_grid_list = []
        for grid_idx, value in voxel_grid.items():
            voxel_grid_list.append(value)

        return voxel_grid_list

    def voxelCropAndCombine(self, box_padding=5):
        # 计算AABB
        x_min = self.swcNodes[0]["x"]
        x_max = self.swcNodes[0]["x"]

        y_min = self.swcNodes[0]["y"]
        y_max = self.swcNodes[0]["y"]

        z_min = self.swcNodes[0]["z"]
        z_max = self.swcNodes[0]["z"]

        for node in self.swcNodes:
            x_min = min(node["x"], x_min)
            x_max = max(node["x"], x_max)

            y_min = min(node["y"], y_min)
            y_max = max(node["y"], y_max)

            z_min = min(node["z"], z_min)
            z_max = max(node["z"], z_max)

        # voxel grid 操作
        x_min = x_min - box_padding
        x_max = x_max + box_padding

        y_min = y_min - box_padding
        y_max = y_max + box_padding

        z_min = z_min - box_padding
        z_max = z_max + box_padding

        dx = (x_max - x_min) // self.voxelSize + 1
        dy = (y_max - y_min) // self.voxelSize + 1
        dz = (z_max - z_min) // self.voxelSize + 1

        self.dx = dx
        self.dy = dy
        self.dz = dz

        voxel_grid = {}
        for node in self.swcNodes:
            # 计算index
            hx = (node["x"] - x_min) // self.voxelSize
            hy = (node["y"] - y_min) // self.voxelSize
            hz = (node["z"] - z_min) // self.voxelSize

            grid_index = hx + hy * dx + hz * dx * dy
            if str(grid_index) in voxel_grid:
                voxel_grid[str(grid_index)]["nodes"].append(node["idx"])
            else:
                grid_pos = [
                    x_min + hx * self.voxelSize + self.voxelSize / 2,
                    y_min + hy * self.voxelSize + self.voxelSize / 2,
                    z_min + hz * self.voxelSize + self.voxelSize / 2,
                ]
                voxel_grid[str(grid_index)] = {
                    "pos": grid_pos,
                    "size": [self.voxelSize, self.voxelSize, self.voxelSize],
                    "nodes": [node["idx"]],
                    "combined": False
                }

        # todo block combine
        idx_all_list = voxel_grid.keys()

        for grid_idx, value in voxel_grid.items():
            adj_index_list = self.getAdjacentList(int(grid_idx))
            for adj_idx in adj_index_list:
                if str(adj_idx) in idx_all_list:
                    # 邻近的block在列表中

                    pass
                pass
        #

        # dict to list处理
        voxel_grid_list = []
        for grid_idx, value in voxel_grid.items():
            voxel_grid_list.append(value)

        return voxel_grid_list
        pass
