import os
import copy


# 读取swc的相关信息
class SWCReader:
    def __init__(self, path):
        # 根据swc path，解析相关信息
        self.file_name = os.path.basename(path)
        self.swc_data = []
        with open(path, "r") as f:
            content = f.readlines()
            # 只读取info，不需要注释信息
            for node_info in content:
                if node_info[0] == "#":
                    print("get annotation, skipped")
                    continue

                node_info = (node_info.strip()).split()
                temp = {
                    "idx": int(node_info[0]),
                    "type": int(node_info[1]),
                    "x": float(node_info[2]),
                    "y": float(node_info[3]),
                    "z": float(node_info[4]),
                    "radius": float(node_info[5]),
                    "parent": int(node_info[6])
                }
                self.swc_data.append(temp)

    def getNodeCnt(self):
        return len(self.swc_data)

    def getSWCFileName(self):
        return self.file_name

    def getSWCData(self):
        return self.swc_data

    def getSWCSegments(self):
        seg_list = []
        seg_temp = []
        for node in self.swc_data:
            # 首节点特殊处理
            if node["parent"] == -1:
                seg_temp.append(node)
                continue

            if node["parent"] != node["idx"] - 1:
                # branch node 导出 空栈
                seg_list.append(copy.deepcopy(seg_temp))
                seg_temp = [node]
            else:
                # 非branch node 加入栈中
                seg_temp.append(node)

        # 处理最后一个seg
        seg_list.append(copy.deepcopy(seg_temp))
        return seg_list


if __name__ == '__main__':
    # swc_path = os.path.join(os.getcwd(), "swc/191797_x6369_y23270_z9122_task00001.swc")
    swc_path = os.path.join(os.getcwd(), "swc_test/18454_00158.swc")
    SWC = SWCReader(swc_path)
    print("filename:", SWC.getSWCFileName())
    swc_data = SWC.getSWCData()

    swc_segments = SWC.getSWCSegments()
    cnt = 0
    print("branch cnt:", cnt)

    print("swc data:", len(SWC.getSWCData()))
