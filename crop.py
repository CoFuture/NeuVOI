import copy
import json


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
    def __init__(self, swc_nodes, voxel_size=64, box_max_size=512):
        self.swcNodes = swc_nodes

        # voxel grid相关参数
        self.voxelSize = voxel_size
        self.boxMaxSize = box_max_size

        # voxel划分信息
        self.dx = -1
        self.dy = -1
        self.dz = -1

        # combine paras default: 5 5
        # self.blockNodeThreshold = node_threshold
        self.blockDensityThreshold = -1

    # 对swc进行voxel grid化
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
            print(grid_index)
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

    # 计算combine分数, 返回值：value, new_bb_box
    def calCombineValue(self, b1_dict, b2_dict):
        # 计算AABB
        b1_size = b1_dict["size"]
        b1_bb_min = [b1_dict["pos"][0] - b1_dict["size"][0] / 2,
                     b1_dict["pos"][1] - b1_dict["size"][1] / 2,
                     b1_dict["pos"][2] - b1_dict["size"][2] / 2]
        b1_bb_max = [b1_dict["pos"][0] + b1_dict["size"][0] / 2,
                     b1_dict["pos"][1] + b1_dict["size"][1] / 2,
                     b1_dict["pos"][2] + b1_dict["size"][2] / 2]

        b2_size = b2_dict["size"]
        b2_bb_min = [b2_dict["pos"][0] - b2_dict["size"][0] / 2,
                     b2_dict["pos"][1] - b2_dict["size"][1] / 2,
                     b2_dict["pos"][2] - b2_dict["size"][2] / 2]
        b2_bb_max = [b2_dict["pos"][0] + b2_dict["size"][0] / 2,
                     b2_dict["pos"][1] + b2_dict["size"][1] / 2,
                     b2_dict["pos"][2] + b2_dict["size"][2] / 2]

        # new bounding box
        x_min = min(b1_bb_min[0], b2_bb_min[0])
        x_max = max(b1_bb_max[0], b2_bb_max[0])
        box_size_x = x_max - x_min
        if box_size_x > self.boxMaxSize:
            return None

        y_min = min(b1_bb_min[1], b2_bb_min[1])
        y_max = max(b1_bb_max[1], b2_bb_max[1])
        box_size_y = y_max - y_min
        if box_size_y > self.boxMaxSize:
            return None

        z_min = min(b1_bb_min[2], b2_bb_min[2])
        z_max = max(b1_bb_max[2], b2_bb_max[2])
        box_size_z = z_max - z_min
        if box_size_z > self.boxMaxSize:
            return None

        bb_new_min = [x_min, y_min, z_min]
        bb_new_max = [x_max, y_max, z_max]

        # 合并后的node总数和density
        new_node_total = len(b1_dict["nodes"]) + len(b2_dict["nodes"])

        # 合并后的新体积，以grid_size为单位
        new_volume = round((x_max - x_min) * (y_max - y_min) * (z_max - z_min) / pow(self.voxelSize, 3))
        new_density = round(new_node_total / new_volume, 2)
        # 引入的体积，以voxel_grid为单位
        volume_inc = (box_size_x * box_size_y * box_size_z - b1_size[0] * b1_size[1] * b1_size[2] - b2_size[0] *
                      b2_size[1] * b2_size[2]) / pow(self.voxelSize, 3)

        if volume_inc < 0:
            volume_inc = 0
        # print("---cal score---", new_node_total, new_volume, new_density, volume_inc)
        # 计算分数 原则，尽可能均化density，同时在阈值范围内获得尽可能大的block体积
        # 密度值的相近度
        # print("---cal score: ---", abs(new_density - self.blockDensityThreshold))

        densityDiff = round(abs(new_density - self.blockDensityThreshold), 2)
        # print("+++density diff+++", new_density, self.blockDensityThreshold, densityDiff)
        if densityDiff > 20.0:
            score_density = 0
        elif densityDiff < 0.1:
            score_density = 1
        else:
            score_density = 1 / (pow(2, densityDiff))

        score_volume_inc = volume_inc / new_volume
        return score_density + score_volume_inc

    def combineBB(self, b1_dict, b2_dict):
        # 计算AABB
        b1_bb_min = [b1_dict["pos"][0] - b1_dict["size"][0] / 2,
                     b1_dict["pos"][1] - b1_dict["size"][1] / 2,
                     b1_dict["pos"][2] - b1_dict["size"][2] / 2]
        b1_bb_max = [b1_dict["pos"][0] + b1_dict["size"][0] / 2,
                     b1_dict["pos"][1] + b1_dict["size"][1] / 2,
                     b1_dict["pos"][2] + b1_dict["size"][2] / 2]

        b2_bb_min = [b2_dict["pos"][0] - b2_dict["size"][0] / 2,
                     b2_dict["pos"][1] - b2_dict["size"][1] / 2,
                     b2_dict["pos"][2] - b2_dict["size"][2] / 2]
        b2_bb_max = [b2_dict["pos"][0] + b2_dict["size"][0] / 2,
                     b2_dict["pos"][1] + b2_dict["size"][1] / 2,
                     b2_dict["pos"][2] + b2_dict["size"][2] / 2]

        # new bounding box
        x_min = min(b1_bb_min[0], b2_bb_min[0])
        x_max = max(b1_bb_max[0], b2_bb_max[0])
        box_size_x = x_max - x_min
        # if box_size_x > self.boxMaxSize:
        #     return None, "BB out of size"

        y_min = min(b1_bb_min[1], b2_bb_min[1])
        y_max = max(b1_bb_max[1], b2_bb_max[1])
        box_size_y = y_max - y_min
        # if box_size_y > self.boxMaxSize:
        #     return None, "BB out of size"

        z_min = min(b1_bb_min[2], b2_bb_min[2])
        z_max = max(b1_bb_max[2], b2_bb_max[2])
        box_size_z = z_max - z_min
        # if box_size_z > self.boxMaxSize:
        #     return None, "BB out of size"

        # 计算新BB
        # | 并集运算  - 差集运算
        new_bb_nodes = b1_dict["nodes"] | b2_dict["nodes"]
        new_combined_id = b1_dict["combined_id"] | b2_dict["combined_id"]
        new_adjacent_id = (b1_dict["adjacent_id"] | b2_dict["adjacent_id"]) - new_combined_id

        new_bb_dict = {
            "pos": [(x_min + x_max) / 2, (y_min + y_max) / 2, (z_min + z_max) / 2],
            "size": [box_size_x, box_size_y, box_size_z],
            "nodes": new_bb_nodes,
            "combined_id": new_combined_id,
            "adjacent_id": new_adjacent_id
        }
        return new_bb_dict

    # 获取最大value值的dict
    def getMaxValueDict(self, pv_dict):
        max_value = -1
        max_pv = None
        for pv, value in pv_dict.items():
            if value > max_value:
                max_pv = pv
                max_value = value
        return max_pv, max_value

    # crop之后进行bounding box的combine操作
    def voxelCropAndCombine(self, box_padding=5):
        print("-----start compute voxel grid------")
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

        dx = int((x_max - x_min) // self.voxelSize + 1)
        dy = int((y_max - y_min) // self.voxelSize + 1)
        dz = int((z_max - z_min) // self.voxelSize + 1)

        self.dx = dx
        self.dy = dy
        self.dz = dz
        self.blockDensityThreshold = round(len(self.swcNodes) / (self.dx * self.dy * self.dz), 2)

        voxel_grid = {}
        for node in self.swcNodes:
            # 计算index
            hx = int((node["x"] - x_min) // self.voxelSize)
            hy = int((node["y"] - y_min) // self.voxelSize)
            hz = int((node["z"] - z_min) // self.voxelSize)
            grid_index = hx + hy * dx + hz * dx * dy

            if str(grid_index) in voxel_grid:
                voxel_grid[str(grid_index)]["nodes"].add(node["idx"])
            else:
                grid_pos = [
                    x_min + hx * self.voxelSize + self.voxelSize / 2,
                    y_min + hy * self.voxelSize + self.voxelSize / 2,
                    z_min + hz * self.voxelSize + self.voxelSize / 2,
                ]

                # adjacent id用于保存临近的，未曾合并的grid id
                # combined id用于保存已经合并的 grid id
                voxel_grid[str(grid_index)] = {
                    "pos": grid_pos,
                    "size": [self.voxelSize, self.voxelSize, self.voxelSize],
                    "nodes": {node["idx"]},
                    "adjacent_id": set({}),
                    "combined_id": {grid_index}
                    # "combined_id": set({})
                }

        print("voxel size:", self.voxelSize)
        print("total voxels:", len(voxel_grid))

        # save voxel grid file
        gridList = []
        for index, grid in voxel_grid.items():
            grid_data = {
                "pos": grid["pos"],
                "size": grid["size"]
            }
            gridList.append(grid_data)
        with open("RunData/voxel_grid.json", 'w') as f:
            print("------save grid data------")
            json.dump(gridList, f, indent=2, sort_keys=True, ensure_ascii=False)  # 写为多行

        """------------------------------block combine----------------------------------"""
        print("-----start block combine------")
        # pair value dict
        pv_dict = {}

        # step1 计算block node数量和前景密度，邻接grid_list
        # 复杂度O(n^2)有优化空间
        print("======step1 initial pv_dict && combined_bb_dict======")
        idx_all_list = voxel_grid.keys()
        for grid_idx, value in voxel_grid.items():
            adj_index_list = self.getAdjacentList(int(grid_idx))
            for adj_idx in adj_index_list:
                if str(adj_idx) in idx_all_list:
                    # 初始化邻接grid index，集合添加运算
                    voxel_grid[grid_idx]["adjacent_id"].add(adj_idx)

                    # 初始化pair--value对
                    if int(grid_idx) < adj_idx:
                        pair_name = str(grid_idx) + "_" + str(adj_idx)
                    else:
                        pair_name = str(adj_idx) + "_" + str(grid_idx)

                    # 计算邻接block的合并value
                    if pair_name not in pv_dict.keys():
                        score = self.calCombineValue(voxel_grid[grid_idx], voxel_grid[str(adj_idx)])
                        if score is not None:
                            pv_dict[pair_name] = score

        print("initial len of pv_dict:", len(pv_dict))

        combined_bb_dict = copy.deepcopy(voxel_grid)
        # 全局的id计数器，用于给合并后的bb命名
        bb_id_cnt = self.dx * self.dy * self.dz + 1

        # 循环终止条件 无可合并价值的block
        print("======step2 start combine======")
        iter_cnt = 0
        while len(pv_dict) > 0:
            max_pv, max_value = self.getMaxValueDict(pv_dict)
            # print("iter cnt:", iter_cnt, "---", "pv:", max_pv, "---", "value:", max_value)
            # 合并
            old_bb1_idx, old_bb2_idx = max_pv.split("_")
            # new_dict = self.combineBB(combined_bb_dict[old_bb1_idx], combined_bb_dict[old_bb2_idx])

            """combine bb dict"""
            b1_dict = combined_bb_dict[old_bb1_idx]
            b2_dict = combined_bb_dict[old_bb2_idx]
            # 计算AABB
            b1_bb_min = [b1_dict["pos"][0] - b1_dict["size"][0] / 2,
                         b1_dict["pos"][1] - b1_dict["size"][1] / 2,
                         b1_dict["pos"][2] - b1_dict["size"][2] / 2]
            b1_bb_max = [b1_dict["pos"][0] + b1_dict["size"][0] / 2,
                         b1_dict["pos"][1] + b1_dict["size"][1] / 2,
                         b1_dict["pos"][2] + b1_dict["size"][2] / 2]

            b2_bb_min = [b2_dict["pos"][0] - b2_dict["size"][0] / 2,
                         b2_dict["pos"][1] - b2_dict["size"][1] / 2,
                         b2_dict["pos"][2] - b2_dict["size"][2] / 2]
            b2_bb_max = [b2_dict["pos"][0] + b2_dict["size"][0] / 2,
                         b2_dict["pos"][1] + b2_dict["size"][1] / 2,
                         b2_dict["pos"][2] + b2_dict["size"][2] / 2]

            # new bounding box
            x_min = min(b1_bb_min[0], b2_bb_min[0])
            x_max = max(b1_bb_max[0], b2_bb_max[0])
            box_size_x = x_max - x_min
            # if box_size_x > self.boxMaxSize:
            #     return None, "BB out of size"

            y_min = min(b1_bb_min[1], b2_bb_min[1])
            y_max = max(b1_bb_max[1], b2_bb_max[1])
            box_size_y = y_max - y_min
            # if box_size_y > self.boxMaxSize:
            #     return None, "BB out of size"

            z_min = min(b1_bb_min[2], b2_bb_min[2])
            z_max = max(b1_bb_max[2], b2_bb_max[2])
            box_size_z = z_max - z_min
            # if box_size_z > self.boxMaxSize:
            #     return None, "BB out of size"

            # 计算新BB
            # | 并集运算  - 差集运算
            new_bb_nodes = b1_dict["nodes"] | b2_dict["nodes"]
            new_combined_id = b1_dict["combined_id"] | b2_dict["combined_id"]
            # 去掉被合并的两个bb id
            new_adjacent_id = (b1_dict["adjacent_id"] | b2_dict["adjacent_id"]) - {int(old_bb1_idx), int(old_bb2_idx)}

            new_bb_dict = {
                "pos": [(x_min + x_max) / 2, (y_min + y_max) / 2, (z_min + z_max) / 2],
                "size": [box_size_x, box_size_y, box_size_z],
                "nodes": new_bb_nodes,
                # combine grid list ATTENTION: GRID not equal to block id in  combined_bb_dict
                "combined_id": new_combined_id,
                "adjacent_id": new_adjacent_id
            }

            # 新bb的id
            new_bb_id = str(bb_id_cnt)
            bb_id_cnt += 1

            # 更新combined bb dict
            combined_bb_dict[new_bb_id] = new_bb_dict
            combined_bb_dict.pop(old_bb1_idx)
            combined_bb_dict.pop(old_bb2_idx)
            # print("iter cnt:", iter_cnt, "---", "new bb id:", new_bb_id)

            # 更新 相邻的 pv dict
            # 删除直接相连的pv
            pv_dict.pop(max_pv)
            tmp_pv_dict = copy.deepcopy(pv_dict)

            for pv in pv_dict.keys():
                # 更新邻近的pv
                pv_list = pv.split("_")
                # 邻接关系，计算全新的
                if old_bb1_idx in pv_list or old_bb2_idx in pv_list:
                    # 删除相邻的pv
                    tmp_pv_dict.pop(pv)

                    # update相邻的pv
                    if pv_list[0] == old_bb1_idx or pv_list[0] == old_bb2_idx:
                        adj_bb_idx = pv_list[1]
                    else:
                        adj_bb_idx = pv_list[0]

                    # 更新邻接关系map
                    raw_adjacent_id_list = combined_bb_dict[adj_bb_idx]["adjacent_id"]
                    new_adjacent_id_list = raw_adjacent_id_list - {int(old_bb1_idx), int(old_bb2_idx)}
                    new_adjacent_id_list.add(int(new_bb_id))
                    combined_bb_dict[adj_bb_idx]["adjacent_id"] = new_adjacent_id_list

                    score = self.calCombineValue(new_bb_dict, combined_bb_dict[adj_bb_idx])
                    if score is not None:
                        if int(adj_bb_idx) < int(new_bb_id):
                            pair_name = str(adj_bb_idx) + "_" + str(new_bb_id)
                        else:
                            pair_name = str(new_bb_id) + "_" + str(adj_bb_idx)

                        tmp_pv_dict[pair_name] = score

            del pv_dict
            pv_dict = tmp_pv_dict
            # print("iter cnt:", iter_cnt, "---", "len pv-dict:", len(pv_dict))
            iter_cnt += 1
        # step2 计算 block pair --> combine_value 对

        # step3 选择value最大的pair进行合并，更新block value对

        # dict to list处理
        final_bb_list = []
        for grid_idx, value in combined_bb_dict.items():
            value_new = {
                "pos": value["pos"],
                "size": value["size"],
                "nodes": list(value["nodes"])
            }
            final_bb_list.append(value_new)

        return final_bb_list

    # crop之后进行bounding box的combine操作
    def voxelCropAndCombineNew(self, box_padding=5):
        print("-----start compute voxel grid------")
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

        dx = int((x_max - x_min) // self.voxelSize + 1)
        dy = int((y_max - y_min) // self.voxelSize + 1)
        dz = int((z_max - z_min) // self.voxelSize + 1)

        self.dx = dx
        self.dy = dy
        self.dz = dz
        self.blockDensityThreshold = round(len(self.swcNodes) / (self.dx * self.dy * self.dz), 2)

        voxel_grid = {}
        for node in self.swcNodes:
            # 计算index
            hx = int((node["x"] - x_min) // self.voxelSize)
            hy = int((node["y"] - y_min) // self.voxelSize)
            hz = int((node["z"] - z_min) // self.voxelSize)
            grid_index = hx + hy * dx + hz * dx * dy

            if str(grid_index) in voxel_grid:
                voxel_grid[str(grid_index)]["nodes"].add(node["idx"])
            else:
                grid_pos = [
                    x_min + hx * self.voxelSize + self.voxelSize / 2,
                    y_min + hy * self.voxelSize + self.voxelSize / 2,
                    z_min + hz * self.voxelSize + self.voxelSize / 2,
                ]

                # adjacent id用于保存临近的，未曾合并的grid id
                # combined id用于保存已经合并的 grid id
                voxel_grid[str(grid_index)] = {
                    "pos": grid_pos,
                    "size": [self.voxelSize, self.voxelSize, self.voxelSize],
                    "nodes": {node["idx"]},
                    "adjacent_id": set({}),
                    "combined_id": {grid_index}
                    # "combined_id": set({})
                }

        print("voxel size:", self.voxelSize)
        print("total voxels:", len(voxel_grid))

        # save voxel grid file
        gridList = []
        for index, grid in voxel_grid.items():
            grid_data = {
                "pos": grid["pos"],
                "size": grid["size"]
            }
            gridList.append(grid_data)
        with open("RunData/voxel_grid.json", 'w') as f:
            print("------save grid data------")
            json.dump(gridList, f, indent=2, sort_keys=True, ensure_ascii=False)  # 写为多行

        """------------------------------block combine----------------------------------"""
        print("-----start block combine------")
        # pair value dict
        pv_dict = {}

        # step1 计算block node数量和前景密度，邻接grid_list
        # 复杂度O(n^2)有优化空间
        print("======step1 initial pv_dict && combined_bb_dict======")
        idx_all_list = voxel_grid.keys()
        for grid_idx, value in voxel_grid.items():
            adj_index_list = self.getAdjacentList(int(grid_idx))
            for adj_idx in adj_index_list:
                if str(adj_idx) in idx_all_list:
                    # 初始化邻接grid index，集合添加运算
                    voxel_grid[grid_idx]["adjacent_id"].add(adj_idx)

                    # 初始化pair--value对
                    if int(grid_idx) < adj_idx:
                        pair_name = str(grid_idx) + "_" + str(adj_idx)
                    else:
                        pair_name = str(adj_idx) + "_" + str(grid_idx)

                    # 计算邻接block的合并value
                    if pair_name not in pv_dict.keys():
                        score = self.calCombineValue(voxel_grid[grid_idx], voxel_grid[str(adj_idx)])
                        if score is not None:
                            pv_dict[pair_name] = score

        print("initial len of pv_dict:", len(pv_dict))

        combined_bb_dict = copy.deepcopy(voxel_grid)
        # 全局的id计数器，用于给合并后的bb命名
        bb_id_cnt = self.dx * self.dy * self.dz + 1

        # 循环终止条件 无可合并价值的block
        print("======step2 start combine======")
        iter_cnt = 0
        while len(pv_dict) > 0:

            max_pv, max_value = self.getMaxValueDict(pv_dict)
            # print("iter cnt:", iter_cnt, "---", "pv:", max_pv, "---", "value:", max_value)
            # 合并
            old_bb1_idx, old_bb2_idx = max_pv.split("_")
            # new_dict = self.combineBB(combined_bb_dict[old_bb1_idx], combined_bb_dict[old_bb2_idx])
            print("iter count", iter_cnt, bb_id_cnt, max_pv)

            """combine bb dict"""
            b1_dict = combined_bb_dict[str(old_bb1_idx)]
            b2_dict = combined_bb_dict[str(old_bb2_idx)]

            b1_dict_pos = b1_dict["pos"]
            b1_dict_size = b1_dict["size"]

            b2_dict_pos = b2_dict["pos"]
            b2_dict_size = b2_dict["size"]

            # 计算AABB
            b1_bb_min = [b1_dict_pos[0] - b1_dict_size[0] / 2,
                         b1_dict_pos[1] - b1_dict_size[1] / 2,
                         b1_dict_pos[2] - b1_dict_size[2] / 2]
            b1_bb_max = [b1_dict_pos[0] + b1_dict_size[0] / 2,
                         b1_dict_pos[1] + b1_dict_size[1] / 2,
                         b1_dict_pos[2] + b1_dict_size[2] / 2]

            b2_bb_min = [b2_dict_pos[0] - b2_dict_size[0] / 2,
                         b2_dict_pos[1] - b2_dict_size[1] / 2,
                         b2_dict_pos[2] - b2_dict_size[2] / 2]
            b2_bb_max = [b2_dict_pos[0] + b2_dict_size[0] / 2,
                         b2_dict_pos[1] + b2_dict_size[1] / 2,
                         b2_dict_pos[2] + b2_dict_size[2] / 2]

            # new bounding box
            x_min = min(b1_bb_min[0], b2_bb_min[0])
            x_max = max(b1_bb_max[0], b2_bb_max[0])
            box_size_x = x_max - x_min
            # if box_size_x > self.boxMaxSize:
            #     return None, "BB out of size"

            y_min = min(b1_bb_min[1], b2_bb_min[1])
            y_max = max(b1_bb_max[1], b2_bb_max[1])
            box_size_y = y_max - y_min
            # if box_size_y > self.boxMaxSize:
            #     return None, "BB out of size"

            z_min = min(b1_bb_min[2], b2_bb_min[2])
            z_max = max(b1_bb_max[2], b2_bb_max[2])
            box_size_z = z_max - z_min
            # if box_size_z > self.boxMaxSize:
            #     return None, "BB out of size"

            # 计算新BB
            # | 并集运算  - 差集运算
            # new_bb_nodes = b1_dict["nodes"] | b2_dict["nodes"]
            # new_combined_id = b1_dict["combined_id"] | b2_dict["combined_id"]
            # # 去掉被合并的两个bb id
            # new_adjacent_id = (b1_dict["adjacent_id"] | b2_dict["adjacent_id"]) - {int(old_bb1_idx),
            #                                                                        int(old_bb2_idx)}

            # 相邻的id的并集 减去两个box自身
            adjacent_id_set = b1_dict["adjacent_id"] | b2_dict["adjacent_id"]
            print(str(old_bb1_idx), " adjacent", b1_dict["adjacent_id"])
            print(str(old_bb2_idx), " adjacent", b2_dict["adjacent_id"])
            print("adjacent id set1", adjacent_id_set)

            adjacent_id_set = adjacent_id_set - {int(old_bb1_idx), int(old_bb2_idx)}

            # 隐藏的adjacent和合并的处理
            combinedIdxSet = set({})
            print("adjacent id set2", adjacent_id_set)

            for adj_idx in adjacent_id_set:
                # 包围盒检测
                adjBoxPos = combined_bb_dict[str(adj_idx)]["pos"]
                adjBoxSize = combined_bb_dict[str(adj_idx)]["size"]
                adjBoxXRange = [adjBoxPos[0] - adjBoxSize[0] / 2, adjBoxPos[0] + adjBoxSize[0] / 2]
                adjBoxYRange = [adjBoxPos[1] - adjBoxSize[1] / 2, adjBoxPos[1] + adjBoxSize[1] / 2]
                adjBoxZRange = [adjBoxPos[2] - adjBoxSize[2] / 2, adjBoxPos[2] + adjBoxSize[2] / 2]

                newBoxXRange = [x_min, x_max]
                newBoxYRange = [y_min, y_max]
                newBoxZRange = [z_min, z_max]

                xCrossed = True
                yCrossed = True
                zCrossed = True

                if adjBoxXRange[0] > newBoxXRange[1] or adjBoxXRange[1] < newBoxXRange[0]:
                    xCrossed = False

                if adjBoxYRange[0] > newBoxYRange[1] or adjBoxYRange[1] < newBoxYRange[0]:
                    yCrossed = False

                if adjBoxZRange[0] > newBoxZRange[1] or adjBoxZRange[1] < newBoxZRange[0]:
                    zCrossed = False

                if xCrossed and yCrossed and zCrossed:
                    # 包含在其中, 记录
                    combinedIdxSet.add(adj_idx)
                    print("==add to combine set===", adj_idx)

            # 新的邻接index集合 遍历combinedSet
            # 被combined id set
            combinedIdxSet = combinedIdxSet | {int(old_bb1_idx), int(old_bb2_idx)}
            print("need to combine id set", combinedIdxSet)

            # 计算combined voxel list
            combined_id_set = set({})
            nodes_id_set = set({})
            adjacent_id_set = set({})
            for c_id in combinedIdxSet:
                adjacent_id_set = adjacent_id_set | combined_bb_dict[str(c_id)]["adjacent_id"]
                combined_id_set = combined_id_set | combined_bb_dict[str(c_id)]["combined_id"]
                nodes_id_set = nodes_id_set | combined_bb_dict[str(c_id)]["nodes"]

            adjacent_id_set = adjacent_id_set - combinedIdxSet
            print("new adjacent id set", adjacent_id_set)

            """生成新的bb"""
            new_bb_dict = {
                "pos": [(x_min + x_max) / 2, (y_min + y_max) / 2, (z_min + z_max) / 2],
                "size": [box_size_x, box_size_y, box_size_z],
                "nodes": nodes_id_set,
                # combine grid list ATTENTION: GRID not equal to block id in  combined_bb_dict
                "combined_id": combined_id_set,
                "adjacent_id": adjacent_id_set
            }

            # 新bb的id
            new_bb_id = str(bb_id_cnt)
            bb_id_cnt += 1

            # 更新combined bb dict
            combined_bb_dict[new_bb_id] = new_bb_dict

            # todo 更新combined list中的邻接关系

            # 清除combined bb dict
            for c_id in combinedIdxSet:
                combined_bb_dict.pop(str(c_id))
                if c_id == 314114:
                    print("aaa")
            # print("iter cnt:", iter_cnt, "---", "new bb id:", new_bb_id)

            """更新 pv dict"""
            # 受到影响的：combined set中的bb，重新计算邻接pair

            tmp_pv_dict = copy.deepcopy(pv_dict)

            for pv in pv_dict.keys():
                # 更新邻近的pv
                pv_list = pv.split("_")
                # 删除直接相连的pv
                if int(pv_list[0]) in combinedIdxSet:
                    # print("delete pv", pv)
                    tmp_pv_dict.pop(pv)
                    if int(pv_list[1]) in combinedIdxSet:

                        continue
                    else:
                        # 正常处理
                        adj_bb_idx = pv_list[1]
                        cob_bb_idx = pv_list[0]
                elif int(pv_list[1]) in combinedIdxSet:
                    # print("delete pv", pv)
                    tmp_pv_dict.pop(pv)
                    if int(pv_list[0]) in combinedIdxSet:
                        continue
                    else:
                        # 正常处理
                        adj_bb_idx = pv_list[0]
                        cob_bb_idx = pv_list[1]
                else:
                    continue

                # if pv_list[0] == "280729" and pv_list[1] == "280824":
                #     print("aaaa")

                # 更新邻接关系map 删除pv
                raw_adjacent_id_list = combined_bb_dict[adj_bb_idx]["adjacent_id"]
                new_adjacent_id_list = raw_adjacent_id_list - {int(cob_bb_idx)}
                new_adjacent_id_list.add(int(new_bb_id))
                combined_bb_dict[adj_bb_idx]["adjacent_id"] = new_adjacent_id_list

                score = self.calCombineValue(new_bb_dict, combined_bb_dict[adj_bb_idx])
                if score is not None:
                    if int(adj_bb_idx) < int(new_bb_id):
                        pair_name = str(adj_bb_idx) + "_" + str(new_bb_id)
                    else:
                        pair_name = str(new_bb_id) + "_" + str(adj_bb_idx)

                    tmp_pv_dict[pair_name] = score

            del pv_dict
            pv_dict = tmp_pv_dict
            print("iter cnt:", iter_cnt, "---", "len pv-dict:", len(pv_dict))
            iter_cnt += 1
        # step2 计算 block pair --> combine_value 对

        # step3 选择value最大的pair进行合并，更新block value对

        # dict to list处理
        final_bb_list = []
        for grid_idx, value in combined_bb_dict.items():
            value_new = {
                "pos": value["pos"],
                "size": value["size"],
                "nodes": list(value["nodes"])
            }
            final_bb_list.append(value_new)

        return final_bb_list
