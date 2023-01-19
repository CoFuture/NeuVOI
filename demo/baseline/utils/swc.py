import os
import copy


class SWCNode:
    def __init__(self, index, node_type, x, y, z, radius, parent_id):
        self.index = index
        self.node_type = node_type
        self.x = x
        self.y = y
        self.z = z
        self.radius = radius
        self.parent_id = parent_id
        # link to parent
        self.parent = None

        self.isEnd = True

    def setParent(self, parent_node):
        self.parent = parent_node

    def getData(self):
        data = {
            "idx": self.index,
            "type": self.node_type,
            "x": self.x,
            "y": self.y,
            "z": self.z,
            "radius": self.radius,
            "parent": self.parent_id
        }
        return data


# 读取swc的相关信息
class SWCReader:
    def __init__(self, path):
        # 根据swc path，解析相关信息
        self.file_name = os.path.basename(path)
        self.swc_node_list = []

        # read data
        with open(path, "r") as f:
            content = f.readlines()
            # 只读取info，不需要注释信息
            for node_info in content:
                if node_info[0] == "#":
                    # print("get annotation, skipped")
                    continue

                node_info = (node_info.strip()).split()
                idx = int(node_info[0])
                node_type = int(node_info[1])
                x = float(node_info[2])
                y = float(node_info[3])
                z = float(node_info[4])
                radius = float(node_info[5])
                parent = int(node_info[6])

                node = SWCNode(idx, node_type, x, y, z, radius, parent)
                self.swc_node_list.append(node)

        # build link
        for node in self.swc_node_list:
            if node.parent_id == -1:
                continue

            parent_node = self.swc_node_list[node.parent_id - 1]
            parent_node.isEnd = False
            node.setParent(parent_node)

    def getNodeCnt(self):
        return len(self.swc_node_list)

    def getSWCFileName(self):
        return self.file_name

    def getSWCData(self):
        data = []
        for node in self.swc_node_list:
            data.append(node.getData())
        return data

    def getSWCSegments(self):
        seg_list = []
        seg_temp = []

        index_bit_map = [0] * len(self.swc_node_list)

        for node in self.swc_node_list:
            # 首node特殊处理
            # if node.parent is None:
            #     index_bit_map[node.index - 1] = 1
            #     seg_temp.append(node.getData())
            #     seg_list.append(copy.deepcopy(seg_temp))
            #     seg_temp = []
            #     continue

            if index_bit_map[node.index - 1] == 1 or node.isEnd is False:
                continue

            # print(node.index)
            temp_node = node

            while index_bit_map[temp_node.index - 1] == 0:
                seg_temp.append(temp_node.getData())
                index_bit_map[temp_node.index - 1] = 1
                temp_node = temp_node.parent

                if temp_node is None:
                    break

                # print(temp_node.index)

            seg_list.append(copy.deepcopy(seg_temp))
            seg_temp = []

        # 处理最后一个seg
        if len(seg_temp) != 0:
            seg_list.append(copy.deepcopy(seg_temp))

        return seg_list


if __name__ == '__main__':
    # swc_path = os.path.join(os.getcwd(), "swc/191797_x6369_y23270_z9122_task00001.swc")
    # swc_path = os.path.join(os.getcwd(), "swc_test/18454_00158.swc")
    swc_path = os.path.join(os.getcwd(), "swc_test/18454_00158.swc")
    SWC = SWCReader(swc_path)
    print("filename:", SWC.getSWCFileName())
    swc_data = SWC.getSWCData()

    swc_segments = SWC.getSWCSegments()
    cnt = 0
    print("branch cnt:", cnt)

    print("swc data:", len(SWC.getSWCData()))
