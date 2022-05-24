import os


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

    def getSWCFileName(self):
        return self.file_name

    def getSWCData(self):
        return self.swc_data


if __name__ == '__main__':
    # swc_path = os.path.join(os.getcwd(), "swc/191797_x6369_y23270_z9122_task00001.swc")
    swc_path = os.path.join(os.getcwd(), "swc_test/18454_00158.swc")
    SWC = SWCReader(swc_path)
    print("filename:", SWC.getSWCFileName())
    swc_data = SWC.getSWCData()

    cnt = 0
    for node_info in swc_data:
        if int(node_info["parent"]) != int(node_info["idx"]) - 1:
            cnt += 1

    print("branch cnt:", cnt)

    print("swc data:", len(SWC.getSWCData()))
