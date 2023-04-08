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
        self.seg_id = -1
        self.grid_id = -1
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

    def getDataString(self):
        return str(self.index) + " " + str(self.node_type) + " " + str(self.x) + " " + str(self.y) + " " + str(
            self.z) + " " + str(self.radius) + " " + str(self.parent_id) + "\n"


class ESWCNode:
    def __init__(self, index, node_type, x, y, z, radius, parent_id, segment_id, level, mode, timestamp):
        self.index = index
        self.node_type = node_type
        self.x = x
        self.y = y
        self.z = z
        self.radius = radius
        self.parent_id = parent_id

        self.segment_id = segment_id
        self.level = level
        self.mode = mode
        self.timestamp = timestamp

        # link to parent
        self.parent = None
        self.seg_id = -1
        self.grid_id = -1
        self.isEnd = True

    def setParent(self, parent_node):
        self.parent = parent_node

    def getData(self):
        data = {
            "n": self.index,
            "type": self.node_type,
            "x": self.x,
            "y": self.y,
            "z": self.z,
            "radius": self.radius,
            "parent": self.parent_id,
            "seg_id": self.segment_id,
            "level": self.level,
            "mode": self.mode,
            "timestamp": self.timestamp
        }
        return data

    def getDataString(self):
        return str(self.index) + " " + str(self.node_type) + " " + str(self.x) + " " + str(self.y) + " " + str(
            self.z) + " " + str(self.radius) + " " + str(self.parent_id) + " " + str(self.segment_id) + " " + str(
            self.level) + " " + str(self.mode) + " " + str(self.timestamp) + "\n"


# 读取swc的相关信息
class SWCReader:
    def __init__(self, f_path):
        # 根据swc path，解析相关信息
        self.file_name = os.path.basename(f_path)

        self.swcNodeList = []
        self.swcNodes = {}

        # segment node map
        self.segments = {}

        if str(f_path).endswith(".swc"):
            self.parseSWC(f_path)
        elif str(f_path).endswith(".eswc"):
            self.parseESWC(f_path)
        else:
            print("Not supported file type")

    def parseSWC(self, f_path):
        # read data
        with open(f_path, "r") as f:
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
                self.swcNodeList.append(node)
                self.swcNodes[idx] = node

        # build link
        for node in self.swcNodeList:
            if node.parent_id == -1:
                continue

            parent_node = self.swcNodes[node.parent_id]
            parent_node.isEnd = False
            node.setParent(parent_node)

        # build raw segments
        segment_id = 0
        seg_temp = []

        index_bit_map = [0] * len(self.swcNodeList)
        for node in self.swcNodeList:
            if index_bit_map[node.index - 1] == 1 or node.isEnd is False:
                continue

            temp_node = node
            while index_bit_map[temp_node.index - 1] == 0:
                seg_temp.append(temp_node)
                node.seg_id = segment_id
                index_bit_map[temp_node.index - 1] = 1

                temp_node = temp_node.parent
                if temp_node is None:
                    break

            self.segments[segment_id] = seg_temp
            segment_id += 1
            seg_temp = []

        for node in self.swcNodeList:
            if node.seg_id == -1:
                print("find unsegmented node:", node.index, node.parent_id)
        pass

    def parseESWC(self, f_path):
        # read data
        with open(f_path, "r") as f:
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

                # something new
                segment_id = node_info[7]
                level = node_info[8]
                mode = node_info[9]
                timestamp = node_info[10]

                node = ESWCNode(idx, node_type, x, y, z, radius, parent, segment_id, level, mode, timestamp)
                self.swcNodeList.append(node)

        # build link
        for node in self.swcNodeList:
            if node.parent_id == -1:
                continue

            parent_node = self.swcNodeList[node.parent_id - 1]
            parent_node.isEnd = False
            node.setParent(parent_node)

        # build raw segments
        segment_id = 0
        seg_temp = []

        index_bit_map = [0] * len(self.swcNodeList)
        for node in self.swcNodeList:
            if index_bit_map[node.index - 1] == 1 or node.isEnd is False:
                continue

            temp_node = node
            while index_bit_map[temp_node.index - 1] == 0:
                seg_temp.append(temp_node)
                node.seg_id = segment_id
                index_bit_map[temp_node.index - 1] = 1

                temp_node = temp_node.parent
                if temp_node is None:
                    break

            self.segments[segment_id] = seg_temp
            segment_id += 1
            seg_temp = []

        for node in self.swcNodeList:
            if node.seg_id == -1:
                print("find unsegmented node:", node.index, node.parent_id)

    def getNodeCnt(self):
        return len(self.swcNodeList)

    def getSWCFileName(self):
        return self.file_name

    def getSWCData(self):
        data = []
        for node in self.swcNodeList:
            data.append(node.getData())
        return data

    def getSWCSegments(self):
        seg_list = []
        for temp_seg_list in self.segments.values():
            seg_list.append(temp_seg_list)
        return seg_list


if __name__ == '__main__':
    # swc_path = os.path.join(os.getcwd(), "swc/191797_x6369_y23270_z9122_task00001.swc")
    # swc_path = os.path.join(os.getcwd(), "swc_test/18454_00158.swc")
    # swc_path = os.path.join(os.getcwd(), "18454_00158.swc")
    swc_path = os.path.join(os.getcwd(), "18458_00375.eswc")
    SWC = SWCReader(swc_path)
    print("filename:", SWC.getSWCFileName())
    swc_data = SWC.getSWCData()

    swc_segments = SWC.getSWCSegments()
    cnt = 0
    print("branch cnt:", cnt)

    print("swc data:", len(SWC.getSWCData()))
