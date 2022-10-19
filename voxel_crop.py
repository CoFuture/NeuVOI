import copy
import json


class Voxel:
    def __init__(self, x=0, y=0, z=0, index=0, size=64, pos=None, nodes=None):
        # grid index
        self.x = x
        self.y = y
        self.z = z
        self.index = index

        self.size = [size, size, size]

        if pos is None:
            pos = [0, 0, 0]
        self.position = pos

        if nodes is None:
            nodes = []
        self.nodes = nodes

        # 被索引的BB的id
        self.inverseBBIndex = set({})

    def indexedByBB(self, bb_index):
        self.inverseBBIndex.add(bb_index)

    def getInverseIndexSet(self):
        return self.inverseBBIndex

    def removeBBIndex(self, bb_index):
        self.inverseBBIndex.remove(bb_index)

    def addNodes(self, node_idx):
        self.nodes.append(node_idx)

    def getNodes(self):
        return self.nodes


class BoundingBox:
    def __init__(self, index=0, pos=None, size=None):
        self.index = index

        if pos is None:
            pos = [0, 0, 0]
        self.position = pos

        if size is None:
            size = [64, 64, 64]
        self.size = size

        self.adjacentDict = {}
        self.containedVoxelDict = {}

    def getVoxelSize(self):
        tempVoxelKey = tuple(self.containedVoxelDict.keys())[0]
        voxel = self.containedVoxelDict[tempVoxelKey]
        v_size = voxel.size[0]

        final_size = int(self.size[0] / v_size) * int(self.size[1] / v_size) * int(self.size[2] / v_size)
        return final_size

    def addAdjacent(self, bb):
        if bb.index not in self.adjacentDict.keys():
            self.adjacentDict[bb.index] = bb

    def getAdjacentIndexSet(self):
        adjSet = set({})
        for adj_id in self.adjacentDict.keys():
            adjSet.add(adj_id)
        return adjSet

    def getAllVoxel(self):
        return self.containedVoxelDict

    def getAllVoxelIdxSet(self):
        return set(self.containedVoxelDict.keys())

    def addVoxel(self, voxel):
        if voxel.index not in self.containedVoxelDict.keys():
            self.containedVoxelDict[voxel.index] = voxel
            voxel.indexedByBB(self.index)

    def removeAdjacent(self, bb_idx_set):
        for bb_idx in bb_idx_set:
            if bb_idx in self.adjacentDict.keys():
                self.adjacentDict.pop(bb_idx)

    def getNodes(self):
        nodesList = []
        for v_idx, voxel in self.containedVoxelDict.items():
            nodesList.extend(voxel.getNodes())
        return nodesList


class PairBB:
    def __init__(self, bb1, bb2, value=None):
        self.bb1 = bb1
        self.bb2 = bb2

        if value is None:
            value = 0

        self.value = value

    def getBBSet(self):
        return {self.bb1.index, self.bb2.index}


class VoxelCrop:
    def __init__(self, swc_nodes, voxel_size=64, box_max_size=512, zero_overlap=False):
        self.swcNodes = swc_nodes

        # voxel grid相关参数
        self.voxelSize = voxel_size
        self.boxMaxSize = box_max_size
        # zero overlap
        self.zero_overlap = zero_overlap

        # voxel划分信息
        self.dx = -1
        self.dy = -1
        self.dz = -1

        # combine paras default: 5 5
        # self.blockNodeThreshold = node_threshold
        self.blockDensityThreshold = -1

        # voxel dict
        self.voxelDict = {}
        # bb hash dict
        self.bbDict = {}
        # combine pair dict
        self.pairValueDict = {}

        # accelerate compute —— overlap / hidden set
        self.overlapAndHiddenBuffer = {}

    # pmin, pmax内的overlap
    def calculateOverlap(self, pmin, pmax, ):
        pass

    def getAdjacentVoxelIndexList(self, voxel_index):
        voxel_index_list = []

        if self.dx == -1 or self.dy == -1 or self.dz == -1:
            return voxel_index_list

        total_block = self.dx * self.dy * self.dz

        potentialVoxelIdxList = [voxel_index - 1, voxel_index + 1,
                                 voxel_index - self.dx, voxel_index + self.dx,
                                 voxel_index - self.dx * self.dy, voxel_index + self.dx * self.dy]

        for p_index in potentialVoxelIdxList:
            if (0 <= p_index < total_block) and p_index in self.voxelDict.keys():
                voxel_index_list.append(p_index)

        return voxel_index_list

    # 检查是否有overlap，输出范围内的hidden voxel id set和overlap id set
    # input： pmin pmax exclusive_set{}
    # output: overlap voxel set
    def checkHiddenAndOverlap(self, pmin, pmax, exclusive_voxel_idx_set):
        # print("xxx", self.voxelDict[291942].getInverseIndexSet())
        # overlap不考虑自身已有的
        allVoxelKeysSet = set(self.voxelDict.keys())
        scanVoxelKeySet = allVoxelKeysSet - exclusive_voxel_idx_set

        # 隐藏的 voxel/block set
        hiddenBlockIndexSet = set({})
        hiddenVoxelIndexSet = set({})

        potentialOverlapIndexDict = {}

        # 被其他block 索引的voxel 存在overlap
        overlapVoxelIndexSet = set({})

        for v_idx in scanVoxelKeySet:
            voxel = self.voxelDict[v_idx]
            voxel_position = voxel.position
            if pmin[0] < voxel_position[0] < pmax[0] and pmin[1] < voxel_position[1] < pmax[1] and pmin[2] < voxel_position[2] < pmax[2]:
                indexedSet = voxel.getInverseIndexSet()

                # 按照bb idx重新整理
                for bb_idx in indexedSet:
                    if bb_idx in potentialOverlapIndexDict.keys():
                        potentialOverlapIndexDict[bb_idx].add(v_idx)
                    else:
                        potentialOverlapIndexDict[bb_idx] = {v_idx}

        # 判断是否完全包含其他block
        # print("======", len(potentialOverlapIndexDict))
        for bb_idx, voxel_set in potentialOverlapIndexDict.items():
            bb = self.bbDict[bb_idx]
            bb_all_voxel_set = bb.getAllVoxelIdxSet()
            # if len(bb_all_voxel_set) == len(voxel_set):
            #     print("+++++++++", bb_all_voxel_set, voxel_set)
            if len(bb_all_voxel_set - voxel_set) == 0:
                # 完全包含

                hiddenBlockIndexSet.add(bb_idx)
                for v_idx in voxel_set:
                    hiddenVoxelIndexSet.add(v_idx)
            else:
                for v_idx in voxel_set:
                    overlapVoxelIndexSet.add(v_idx)

        return hiddenBlockIndexSet, hiddenVoxelIndexSet, overlapVoxelIndexSet

    # 计算combine分数, 返回值：value, new_bb_box
    def calCombineValue(self, bb1, bb2):
        # 计算AABB
        bb1_pos = bb1.position
        bb1_size = bb1.size

        bb2_pos = bb2.position
        bb2_size = bb2.size

        # 计算AABB
        bb1_pmin = [bb1_pos[0] - bb1_size[0] / 2,
                    bb1_pos[1] - bb1_size[1] / 2,
                    bb1_pos[2] - bb1_size[2] / 2]
        bb1_pmax = [bb1_pos[0] + bb1_size[0] / 2,
                    bb1_pos[1] + bb1_size[1] / 2,
                    bb1_pos[2] + bb1_size[2] / 2]

        bb2_pmin = [bb2_pos[0] - bb2_size[0] / 2,
                    bb2_pos[1] - bb2_size[1] / 2,
                    bb2_pos[2] - bb2_size[2] / 2]
        bb2_pmax = [bb2_pos[0] + bb2_size[0] / 2,
                    bb2_pos[1] + bb2_size[1] / 2,
                    bb2_pos[2] + bb2_size[2] / 2]

        # new bounding box
        x_min = min(bb1_pmin[0], bb2_pmin[0])
        x_max = max(bb1_pmax[0], bb2_pmax[0])
        box_size_x = x_max - x_min
        if box_size_x > self.boxMaxSize:
            return None

        y_min = min(bb1_pmin[1], bb2_pmin[1])
        y_max = max(bb1_pmax[1], bb2_pmax[1])
        box_size_y = y_max - y_min
        if box_size_y > self.boxMaxSize:
            return None

        z_min = min(bb1_pmin[2], bb2_pmin[2])
        z_max = max(bb1_pmax[2], bb2_pmax[2])
        box_size_z = z_max - z_min
        if box_size_z > self.boxMaxSize:
            return None

        bb_new_min = [x_min, y_min, z_min]
        bb_new_max = [x_max, y_max, z_max]

        # 检查overlap
        bb1_voxel_idx_set = bb1.getAllVoxelIdxSet()
        bb2_voxel_idx_set = bb2.getAllVoxelIdxSet()
        exclusive_voxel_idx_set = bb1_voxel_idx_set | bb2_voxel_idx_set
        hiddenBlockIdxSet, hiddenVoxelIdxSet, overlapVoxelIdxSet = self.checkHiddenAndOverlap(bb_new_min, bb_new_max, exclusive_voxel_idx_set)

        # 极端一点zero overlap
        if self.zero_overlap and len(overlapVoxelIdxSet) != 0:
            return None

        # 将hidden overlap保存至运算dict
        if bb1.index < bb2.index:
            p_name = str(bb1.index) + "_" + str(bb2.index)
        else:
            p_name = str(bb2.index) + "_" + str(bb1.index)

        self.overlapAndHiddenBuffer[p_name] = (hiddenBlockIdxSet, hiddenVoxelIdxSet, overlapVoxelIdxSet)

        # 其他参数阈值：block内总的node数量
        # 正相关参数：包含孤立voxel的个数，接近整体block density的程度
        # 负相关参数：overlap，

        # 优先合并孤立的voxel
        if len(bb1_voxel_idx_set) == 1 or len(bb2_voxel_idx_set) == 1:
            # if len(bb1_voxel_idx_set) == 1 and len(bb2_voxel_idx_set) == 1:
            #     priority_score = 1
            # else:
            #     priority_score = 0.5
            priority_score = 1.5
        else:
            # 优先合并小的voxel
            bb1_voxel_size = int(bb1_size[0] / self.voxelSize) * int(bb1_size[1] / self.voxelSize) * int(bb1_size[2] / self.voxelSize)
            bb2_voxel_size = int(bb2_size[0] / self.voxelSize) * int(bb2_size[1] / self.voxelSize) * int(bb2_size[2] / self.voxelSize)

            threshold = int(self.boxMaxSize / self.voxelSize)

            if bb1_voxel_size < threshold or bb2_voxel_size < threshold:
                priority_score = 0.5
            else:
                priority_score = 0

        if len(hiddenVoxelIdxSet) > len(overlapVoxelIdxSet):
            hidden_score = 1.5
        elif len(hiddenVoxelIdxSet) == len(overlapVoxelIdxSet):
            hidden_score = 0
        else:
            hidden_score = -1.5

        # 合并后的node总数和density
        new_node_total = len(bb1.getNodes()) + len(bb2.getNodes())
        for v_id in hiddenVoxelIdxSet:
            voxel = self.voxelDict[v_id]
            new_node_total += len(voxel.getNodes())

        for v_id in overlapVoxelIdxSet:
            voxel = self.voxelDict[v_id]
            new_node_total += len(voxel.getNodes())

        # 合并后的新体积，以grid_size为单位
        new_volume = round((x_max - x_min) * (y_max - y_min) * (z_max - z_min) / pow(self.voxelSize, 3))
        new_density = round(new_node_total / new_volume, 2)

        # 引入的体积，以voxel_grid为单位
        # volume_inc = (box_size_x * box_size_y * box_size_z - bb1[0] * b1_size[1] * b1_size[2] - b2_size[0] *
        #               b2_size[1] * b2_size[2]) / pow(self.voxelSize, 3)
        #
        # if volume_inc < 0:
        #     volume_inc = 0
        # score_volume_inc = volume_inc / new_volume

        # print("---cal score---", new_node_total, new_volume, new_density, volume_inc)
        # 计算分数 原则，尽可能均化density，同时在阈值范围内获得尽可能大的block体积
        # 密度值的相近度
        # print("---cal score: ---", abs(new_density - self.blockDensityThreshold))

        densityDiff = round(abs(new_density - self.blockDensityThreshold), 2)
        # print("+++density diff+++", new_density, self.blockDensityThreshold, densityDiff)
        if densityDiff > 20.0:
            density_score = 0
        elif densityDiff < 0.1:
            density_score = 1
        else:
            density_score = 1 / (pow(2, densityDiff))

        final_score = 2 * priority_score + hidden_score + density_score

        return final_score

    # 获取最大value值的dict
    def getMaxScorePair(self):
        if len(self.pairValueDict) == 0:
            return None

        maxPairName = tuple(self.pairValueDict.keys())[0]
        maxPair = self.pairValueDict[maxPairName]

        # iter_cnt = 0
        for p_name, pair in self.pairValueDict.items():

            if pair.value > maxPair.value:
                maxPairName = p_name
                maxPair = pair

        return maxPairName, maxPair

    def combine(self, bb1_idx, bb2_idx, new_bb_id):

        if bb1_idx not in self.bbDict.keys() or bb2_idx not in self.bbDict.keys():
            return

        bb1 = self.bbDict[bb1_idx]
        bb2 = self.bbDict[bb2_idx]
        bb1_pos = bb1.position
        bb1_size = bb1.size

        bb2_pos = bb2.position
        bb2_size = bb2.size

        # 计算AABB
        bb1_pmin = [bb1_pos[0] - bb1_size[0] / 2,
                    bb1_pos[1] - bb1_size[1] / 2,
                    bb1_pos[2] - bb1_size[2] / 2]
        bb1_pmax = [bb1_pos[0] + bb1_size[0] / 2,
                    bb1_pos[1] + bb1_size[1] / 2,
                    bb1_pos[2] + bb1_size[2] / 2]

        bb2_pmin = [bb2_pos[0] - bb2_size[0] / 2,
                    bb2_pos[1] - bb2_size[1] / 2,
                    bb2_pos[2] - bb2_size[2] / 2]
        bb2_pmax = [bb2_pos[0] + bb2_size[0] / 2,
                    bb2_pos[1] + bb2_size[1] / 2,
                    bb2_pos[2] + bb2_size[2] / 2]

        # new bounding box
        x_min = min(bb1_pmin[0], bb2_pmin[0])
        x_max = max(bb1_pmax[0], bb2_pmax[0])
        box_size_x = x_max - x_min
        # if box_size_x > self.boxMaxSize:
        #     return None, "BB out of size"

        y_min = min(bb1_pmin[1], bb2_pmin[1])
        y_max = max(bb1_pmax[1], bb2_pmax[1])
        box_size_y = y_max - y_min
        # if box_size_y > self.boxMaxSize:
        #     return None, "BB out of size"

        z_min = min(bb1_pmin[2], bb2_pmin[2])
        z_max = max(bb1_pmax[2], bb2_pmax[2])
        box_size_z = z_max - z_min

        # 检查overlap和hidden
        if bb1.index < bb2.index:
            p_name = str(bb1.index) + "_" + str(bb2.index)
        else:
            p_name = str(bb2.index) + "_" + str(bb1.index)

        # hiddenBlockIdxSet, hiddenVoxelIdxSet, overlapVoxelIdxSet = self.overlapAndHiddenBuffer[p_name]

        # 检查overlap
        bb_new_min = [x_min, y_min, z_min]
        bb_new_max = [x_max, y_max, z_max]

        bb1_voxel_idx_set = bb1.getAllVoxelIdxSet()
        bb2_voxel_idx_set = bb2.getAllVoxelIdxSet()
        exclusive_voxel_idx_set = bb1_voxel_idx_set | bb2_voxel_idx_set
        hiddenBlockIdxSet, hiddenVoxelIdxSet, overlapVoxelIdxSet = self.checkHiddenAndOverlap(bb_new_min, bb_new_max,
                                                                                              exclusive_voxel_idx_set)

        # 生成新的box
        new_bb_pos = [(x_min + x_max) / 2, (y_min + y_max) / 2, (z_min + z_max) / 2]
        new_bb_size = [box_size_x, box_size_y, box_size_z]
        newBB = BoundingBox(new_bb_id, new_bb_pos, new_bb_size)

        # print("ccccc", self.voxelDict[291942].getInverseIndexSet())

        # adjacent
        oldBBIndexSet = {bb1.index, bb2.index}
        newAdjSet = bb1.getAdjacentIndexSet() | bb2.getAdjacentIndexSet()
        for bb_idx in hiddenBlockIdxSet:
            oldBBIndexSet.add(bb_idx)
            hiddenBB = self.bbDict[bb_idx]
            newAdjSet = newAdjSet | hiddenBB.getAdjacentIndexSet()

        newAdjSet = newAdjSet - oldBBIndexSet

        for adj_idx in newAdjSet:
            adj_bb = self.bbDict[adj_idx]
            newBB.addAdjacent(adj_bb)
            adj_bb.addAdjacent(newBB)

            # adj bb删除 邻近的
            adj_bb.removeAdjacent(oldBBIndexSet)

        # addVoxel
        for bb_idx in oldBBIndexSet:
            bb = self.bbDict[bb_idx]
            bb_voxels = bb.getAllVoxel()

            for v_id, voxel in bb_voxels.items():
                voxel.removeBBIndex(bb_idx)
                newBB.addVoxel(voxel)

        # overlap voxel
        for op_v_idx in overlapVoxelIdxSet:
            op_voxel = self.voxelDict[op_v_idx]
            newBB.addVoxel(op_voxel)

        # 更新bb dict
        self.bbDict[new_bb_id] = newBB
        for bb_idx in oldBBIndexSet:
            self.bbDict.pop(bb_idx)
        # self.bbDict.pop(bb1.index)
        # self.bbDict.pop(bb2.index)

        # 更新pair dict
        addPairPool = {}
        popPairNameSet = set({})

        for p_name, pair in self.pairValueDict.items():
            pairIndexSet = pair.getBBSet()
            modifyBBSet = pairIndexSet - oldBBIndexSet

            # 删除直接相连的pv
            if len(modifyBBSet) == 2:
                # 没有交集
                continue
            elif len(modifyBBSet) == 1:
                # tempPairValueDict.pop(p_name)
                popPairNameSet.add(p_name)

                modify_bb = self.bbDict[tuple(modifyBBSet)[0]]
                if newBB.index < modify_bb.index:
                    pair_name = str(newBB.index) + "_" + str(modify_bb.index)
                    score = self.calCombineValue(modify_bb, newBB)
                    if score is not None:
                        newPair = PairBB(newBB, modify_bb, score)
                        # tempPairValueDict[pair_name] = newPair
                        addPairPool[pair_name] = newPair
                else:
                    pair_name = str(modify_bb.index) + "_" + str(newBB.index)
                    score = self.calCombineValue(modify_bb, newBB)
                    if score is not None:
                        newPair = PairBB(modify_bb, newBB, score)
                        # tempPairValueDict[pair_name] = newPair
                        addPairPool[pair_name] = newPair
            else:
                # 删除直接相连的
                # tempPairValueDict.pop(p_name)
                popPairNameSet.add(p_name)

        # 更新pair value
        for pop_name in popPairNameSet:
            self.pairValueDict.pop(pop_name)
            self.overlapAndHiddenBuffer.pop(pop_name)

        for pname, pair in addPairPool.items():
            self.pairValueDict[pname] = pair

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

        for node in self.swcNodes:
            # 计算index
            hx = int((node["x"] - x_min) // self.voxelSize)
            hy = int((node["y"] - y_min) // self.voxelSize)
            hz = int((node["z"] - z_min) // self.voxelSize)
            grid_index = hx + hy * dx + hz * dx * dy

            if grid_index in self.voxelDict:
                voxel = self.voxelDict[grid_index]
                voxel.addNodes(node["idx"])
            else:
                grid_pos = [
                    x_min + hx * self.voxelSize + self.voxelSize / 2,
                    y_min + hy * self.voxelSize + self.voxelSize / 2,
                    z_min + hz * self.voxelSize + self.voxelSize / 2,
                ]

                new_voxel = Voxel(hx, hy, hz, grid_index, self.voxelSize, grid_pos)
                self.voxelDict[grid_index] = new_voxel

        print("voxel size:", self.voxelSize)
        print("total voxels:", len(self.voxelDict))

        """保存grid的信息"""
        gridList = []
        for index, voxel in self.voxelDict.items():
            grid_data = {
                "pos": voxel.position,
                "size": voxel.size
            }
            gridList.append(grid_data)
        with open("RunData/voxel_grid.json", 'w') as f:
            print("------save grid data------")
            json.dump(gridList, f, indent=2, sort_keys=True, ensure_ascii=False)  # 写为多行

        """------------------------------block combine----------------------------------"""
        print("-----start block combine------")
        # pair value dict

        print("-----start init combined bounding box-----")
        for index, voxel in self.voxelDict.items():
            bb = BoundingBox(index, voxel.position, voxel.size)
            # 添加contained voxel
            bb.addVoxel(voxel)
            # voxel反向索引
            self.bbDict[index] = bb

        # step1 计算block node数量和前景密度，邻接grid_list
        # 复杂度O(n^2)有优化空间
        print("======step1 initial pv_dict && combined_bb_dict======")
        for index, bb in self.bbDict.items():
            # 更新邻接关系 adjacent voxel
            adjacentVoxelIdxList = self.getAdjacentVoxelIndexList(index)
            for adj_voxel_idx in adjacentVoxelIdxList:
                adj_bb = self.bbDict[adj_voxel_idx]
                # 双向连接关系
                bb.addAdjacent(adj_bb)
                adj_bb.addAdjacent(bb)

                # 初始化pair--value对
                if index < adj_voxel_idx:
                    pair_name = str(index) + "_" + str(adj_voxel_idx)
                    if pair_name not in self.pairValueDict.keys():
                        score = self.calCombineValue(bb, adj_bb)
                        if score is not None:
                            newPair = PairBB(bb, adj_bb, score)
                            self.pairValueDict[pair_name] = newPair

                else:
                    pair_name = str(adj_voxel_idx) + "_" + str(index)
                    if pair_name not in self.pairValueDict.keys():
                        score = self.calCombineValue(bb, adj_bb)
                        if score is not None:
                            newPair = PairBB(adj_bb, bb, score)
                            self.pairValueDict[pair_name] = newPair

        print("initial len of pv_dict:", len(self.pairValueDict))

        # 全局的id计数器，用于给合并后的bb命名
        bb_id_cnt = self.dx * self.dy * self.dz + 1

        # 循环终止条件 无可合并价值的block
        print("======step2 start combine======")
        iter_cnt = 0
        while len(self.pairValueDict) > 0:


            max_pair_name, max_pair = self.getMaxScorePair()
            # 合并
            bb1_index = max_pair.bb1.index
            bb2_index = max_pair.bb2.index


            print("------------------iter count", iter_cnt, bb_id_cnt, max_pair_name, "--------------------")
            self.combine(bb1_index, bb2_index, bb_id_cnt)
            bb_id_cnt += 1


            print("iter cnt:", iter_cnt, "---", "len pv-dict:", len(self.pairValueDict))
            iter_cnt += 1
        # step2 计算 block pair --> combine_value 对

        # step3 选择value最大的pair进行合并，更新block value对

    def getBBList(self):
        bb_list = []
        for bb_idx, bb in self.bbDict.items():
            node_list = bb.getNodes()
            value_new = {
                "index": bb.index,
                "pos": bb.position,
                "size": bb.size,
                "nodes": node_list
            }
            bb_list.append(value_new)

        return bb_list