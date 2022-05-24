from utils.swc import SWCReader


# 输入参数，swc node数量 bb size [x_size, y_size, z_size]
def calBaseline(node_cnt, bb_size):

    # n(int) type(int) x(float/double) y(float/double) z(float/double) r(float/double) parent(int)
    # 单位 Byte
    mem_per_node = 28

    volume_total = node_cnt * bb_size[0] * bb_size[1] * bb_size[2]
    mem_total = node_cnt * mem_per_node

    return volume_total, mem_total


if __name__ == '__main__':

    pass
