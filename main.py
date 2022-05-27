import copy
import os
from utils.swc import SWCReader


# 输入参数，swc node数量 bb size [x_size, y_size, z_size]
def calBaseline(node_cnt, bb_size):

    # n(int) type(int) x(float/double) y(float/double) z(float/double) r(float/double) parent(int)
    # 单位 Byte
    mem_per_node = 28

    volume_total = node_cnt * bb_size[0] * bb_size[1] * bb_size[2]
    mem_total = node_cnt * mem_per_node

    return volume_total, mem_total


# 加入一个新点后的AABB计算
def getAABB(node_pos, p_min, p_max):
    x_min = min(node_pos[0], p_min[0])
    x_max = max(node_pos[0], p_max[0])

    y_min = max(node_pos[1], p_min[1])
    y_max = max(node_pos[1], p_max[1])

    z_min = max(node_pos[2], p_min[2])
    z_max = max(node_pos[2], p_max[2])

    p_min = [x_min, y_min, z_min]
    p_max = [x_max, y_max, z_max]
    return p_min, p_max


# 输出包围盒大小
def getAABBSize(p_min, p_max):
    return [p_max[0] - p_min[0], p_max[1] - p_min[1], p_max[2] - p_min[2]]


# 输出包围盒中心
def getBBCenter(p_min, p_max):
    center = [(p_min[0] + p_max[0]) / 2, (p_min[1] + p_max[1]) / 2, (p_min[2] + p_max[2]) / 2]
    return center


# 以segment为基础的crop
# 输入swc segment， bb-size
# 输出bb 的 位置，包含的点的index list信息
def swcSegmentCrop(swc_segment, bb_size):
    seg_bb_list = []

    node_list = []
    # aabb 基本信息
    p_min = [0, 0, 0]
    p_max = [0, 0, 0]

    for node in swc_segment:
        if len(node_list) == 0:
            # 保存node
            node_list.append(node["idx"])
            p_min = [node["x"], node["y"], node["z"]]
            p_max = [node["x"], node["y"], node["z"]]
        elif len(node_list) == 1:
            # todo 基本假设：segment两个相邻node距离不会 > dist
            node_list.append(node["idx"])
            # 计算aabb
            node_pos = [node["x"], node["y"], node["z"]]
            p_min, p_max = getAABB(node_pos, p_min, p_max)

            # todo compare with bb size
        else:
            # 计算 node 加入后的bb
            node_pos = [node["x"], node["y"], node["z"]]
            pmin_tmp, pmax_temp = getAABB(node_pos, p_min, p_max)
            bb_size_temp = getAABBSize(pmin_tmp, pmax_temp)

            # 判断bb box是否符合
            if bb_size_temp[0] >= bb_size[0] or bb_size_temp[1] >= bb_size[1] or bb_size_temp[2] >= bb_size[2]:
                # 导出bb
                bb_center = getBBCenter(p_min, p_max)
                bb_info = {
                    "pos": bb_center,
                    "size": bb_size,
                    "nodes": copy.deepcopy(node_list)
                }
                seg_bb_list.append(bb_info)

                # 初始化参数
                node_list = [node["idx"]]
                # aabb 基本信息
                p_min = [0, 0, 0]
                p_max = [0, 0, 0]
            else:
                # 合理bb 更新
                p_min = pmin_tmp
                p_max = pmax_temp
                node_list.append(node["idx"])

    # 最后一个bb的处理
    bb_center = getBBCenter(p_min, p_max)
    bb_info = {
        "pos": bb_center,
        "size": bb_size,
        "nodes": copy.deepcopy(node_list)
    }
    seg_bb_list.append(bb_info)
    return seg_bb_list


# 根据bb计算性能
def calPerformance(bbList):
    volume_total = 0
    mem_total = 0
    # 单位 Byte
    mem_per_node = 28

    box_cnt = 0
    for sbbList in bbList:
        for bb in sbbList:
            volume_total += bb["size"][0] * bb["size"][1] * bb["size"][2]
            box_cnt += 1

    return volume_total, box_cnt


if __name__ == '__main__':
    swc_path = os.path.join(os.getcwd(), "swc/18454_00158.swc")
    SWC = SWCReader(swc_path)
    print("filename:", SWC.getSWCFileName())
    swc_segments = SWC.getSWCSegments()

    bb_list = []
    for segment in swc_segments:
        s_bb_list = swcSegmentCrop(segment, [256, 256, 256])
        bb_list.append(s_bb_list)

    # 计算baseline
    volume_base, mem_base = calBaseline(SWC.getNodeCnt(), [256, 256, 256])
    volume_optimize, box_cnt = calPerformance(bb_list)
    print("baseline volume:", volume_base)
    print("baseline memory(Byte):", mem_base)
    print("baseline box cnt", SWC.getNodeCnt())

    print("\n")

    print("optimize memory(Byte):", volume_optimize)
    print("optimize memory(Byte):", mem_base)
    print("optimize box cnt", box_cnt)
    pass
