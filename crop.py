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
