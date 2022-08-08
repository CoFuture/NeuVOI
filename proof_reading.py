import json

from sklearn.decomposition import PCA
import numpy as np


# input: 3D node data in a block
# output: rotation angle
class ProofReading:
    def __init__(self, block_data, method=None):
        self.block_data = block_data
        self.method = method

    # 获取对block的旋转角度
    def getRotMatrix(self):
        if self.method == "PCA":
            return self.getRotMatrix_PCA()
        else:
            print("method not completed")

    def getRotMatrix_PCA(self):
        pca = PCA(n_components=2)
        pca.fit(self.block_data)

        print("pca components:", pca.components_)
        print("pca variance_ratio:", pca.explained_variance_ratio_)

        # 可视化测试

        pass


# 可视化测试
if __name__ == '__main__':
    with open("results/random_block.json", "r") as f:
        block_info = json.load(f)
        # print(block_info)

    nodes_data_tmp = []
    for i in range(len(block_info["nodes"])):
        nodes_data_tmp.append(block_info["nodes"][i]["pos"])

    nodes_data = np.array(nodes_data_tmp)

    # print(nodes_data.shape)
    pr = ProofReading(nodes_data, "PCA")
    pr.getRotMatrix()



