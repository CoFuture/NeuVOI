# NeuVOI

---

This is an acceleration kits for **back indexing** large scale image data from its digitalized structures. \
E.g. Back index raw Neuron image according to its tracing structure(*.swc) to get an image of a specific area.

![workflow.png](Images%2Fworkflow.png)

This projected is started by Yu-Ning Hang ([CoFuture](https://github.com/CoFuture)) and Sheng-Dian Jiang in 2022, SEU-ALLEN, Nanjing, China.

## Tutorial

---

In order to cope with different applicable scenarios, here we propose and implement two back indexing methods: `point-level` algorithm and `segment-level` algorithm. These two algorithms have a high degree of freedom and customizable space. The workflow and usage of the two algorithms are described in detail below. 

### point-level algorithm
#### Overall effect
![point-level effect.png](Images%2Fpoint-level%20effect.png)

#### Applicable scene

- No need to consider the topological relationship between data units (E.g. swc nodes)
- Higher requirements for IO optimization\
E.g. L0 transmission performance optimization


#### Workflow
The algorithm is mainly divided into two steps
1. Voxel gridding, mapping the original data units (swc node) to a voxel grid with a spatial index
2. Calculate the combine value and iteratively combine the voxel grid

Here are two flowcharts of the algorithm
![point-level flowchart1.png](Images%2Fpoint-level%20flowchart1.png)
![point-level flowchart2.png](Images%2Fpoint-level%20flowchart2.png)

ps. The combined value calculation function is currently hard-coded. If you have a deep understanding of the source code, you can try to modify the `calCombineValue` function in `voxel_crop.py`. Subsequent updates will provide a custom interface for the value function.


#### Usage
1. Open config.py and configure the parameters in it
2. run voxel_crop.py with the command below
~~~python
python voxel_crop.py
~~~

Here is a detailed description of the parameters below.

| Parameter  | Description                                              | Range        | Default |
|------------|----------------------------------------------------------|--------------|---------|
| Input      | input file (.swc) path                                   | /            | /       |
| Output     | output file (.json) path                                 | /            | /       |
| voxel_size | The size of voxel grid in voxel gridding                 | unlimited    | 64      |
| max_size   | The maximum size of bounding box (BB) during combination | unlimited    | 512     |
| overlap    | Allow overlap between BBs when doing combination         | True / False | False   |


### segment-level algorithm
#### Overall effect
![segment-level effect.png](Images%2Fsegment-level%20effect.png)

#### Applicable scene

- Need to consider the topological relationship between data units (E.g. swc nodes)
- Certain requirements for IO optimization\
E.g. Backtracking swc-specific morphological structures


#### Workflow
The algorithm is mainly divided into two steps
1. Divide swc into segments
2. For each segment, the bounding box growth algorithm (see BB growth algorithm in supplementary) is used for division.

Here is the flowchart of the algorithm
![segment-level flowchart.png](Images%2Fsegment-level%20flowchart.png)

#### Usage
1. Open config.py and configure the parameters in it
2. run segment_crop.py with the command below
~~~python
python segment_crop.py
~~~

Here is a detailed description of the parameters below.

| Parameter    | Description                                         | Range     | Default |
|--------------|-----------------------------------------------------|-----------|---------|
| Input        | input file (.swc) path                              | /         | /       |
| Output       | output file (.json) path                            | /         | /       |
| max_bb_size  | The max size of bounding box when dividing segments | unlimited | 256     |
| padding_size | The padding size when finalizing bounding box       | unlimited | 64      |


### supplementary
#### Bounding box (BB) growth

Here is the flowchart of the algorithm
![bb growth flowchart.png](Images%2Fbb%20growth%20flowchart.png)

First, a bounding box is initialized by two nodes. As long as the BB size limit is not exceeded, a new node is added to the bounding box. If it exceeds, a new bounding box is re-initialized and the node is added to the new BB.Traverse all nodes until all nodes of the segment are divided.

## Acknowledgements

---

Thanks to the guidance of Sheng-Dian Jiang and Han-Chuan Peng

## License

---