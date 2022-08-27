import json
from sklearn.decomposition import PCA
import numpy as np
import matplotlib.pyplot as plt
import mpl_toolkits.mplot3d  # noqa: F401


# input: 3D node data in a block
# output: rotation angle
class ProofReading:
    def __init__(self, block_data, block_pos, block_size, method=None):
        self.block_data = block_data
        self.method = method
        self.block_pos = block_pos
        self.block_size = block_size
        # 去中心化处理
        self.Decentralize()

    def Decentralize(self):
        for node_pos in self.block_data:
            node_pos[0] -= self.block_pos[0]
            node_pos[1] -= self.block_pos[1]
            node_pos[2] -= self.block_pos[2]

    # 获取对block的旋转角度
    def getRotMatrix(self):
        if self.method == "PCA":
            return self.getRotMatrix_PCA()
        else:
            print("method not completed")

    def getRotMatrix_PCA(self):
        pca = PCA(n_components=2)
        pca.fit(self.block_data)

        component_matrix = pca.components_.T
        print("pca components:", pca.components_.T)
        print("pca variance_ratio:", pca.explained_variance_ratio_)

        # 计算特征平面的法向量
        eigenvector1 = pca.components_[0]
        eigenvector2 = pca.components_[1]
        print("eigen matrix", pca.components_)
        print("eigen vector", eigenvector1, eigenvector2)

        norm_vector = np.cross(eigenvector1, eigenvector2)
        print("norm vector", norm_vector)

        data_new = pca.transform(self.block_data)
        # 可视化测试
        self.plot_figs(1, 30, 20, component_matrix)
        # self.plot_2d_figs(data_new)
        pass

    # 通过遍历投影计算获得旋转矩阵
    def getRotMatrix_Projection(self):
        pass

    def plot_2d_figs(self, data_new):
        plt.scatter(data_new[:, 0], data_new[:, 1], marker='o', c='r')
        plt.show()
        pass

    def plot_figs(self, fig_num, elev, azim, component_matrix):
        fig = plt.figure(fig_num, figsize=(12, 8))
        plt.clf()
        ax = fig.add_subplot(111, projection="3d", elev=elev, azim=azim)
        ax.set_position([0, 0, 0.95, 1])

        ax.scatter(self.block_data[:, 0], self.block_data[:, 1], self.block_data[:, 2], c='r', marker="o")

        # pca = PCA(n_components=3)
        # pca.fit(Y)
        # V = pca.components_.T
        # print(V)

        x_pca_axis, y_pca_axis, z_pca_axis = 100 * component_matrix
        x_pca_plane = np.r_[x_pca_axis[:2], -x_pca_axis[1::-1]]
        y_pca_plane = np.r_[y_pca_axis[:2], -y_pca_axis[1::-1]]
        z_pca_plane = np.r_[z_pca_axis[:2], -z_pca_axis[1::-1]]

        x_pca_plane.shape = (2, 2)
        y_pca_plane.shape = (2, 2)
        z_pca_plane.shape = (2, 2)

        ax.plot_surface(x_pca_plane, y_pca_plane, z_pca_plane)
        # ax.w_xaxis.set_ticklabels([])
        # ax.w_yaxis.set_ticklabels([])
        # ax.w_zaxis.set_ticklabels([])

        plt.show()


#

# 可视化测试
if __name__ == '__main__':
    with open("results/random_block.json", "r") as f:
        block_info = json.load(f)
        # print(block_info)

    b_pos = block_info["pos"]
    b_size = block_info["size"]

    nodes_data_tmp = []
    for i in range(len(block_info["nodes"])):
        nodes_data_tmp.append(block_info["nodes"][i]["pos"])

    nodes_data = np.array(nodes_data_tmp)

    # print(nodes_data.shape)
    pr = ProofReading(nodes_data, b_pos, b_size, "PCA")
    pr.getRotMatrix()
