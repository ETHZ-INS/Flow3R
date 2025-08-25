# TODO: find a good system to define which source nodes each node expects (based on output type == supported input type)
class AnalysisNode:
    def __init__(self):
        self.node_id = None

class PoseEstimationNode(AnalysisNode):
    def __init__(self):
        super().__init__()
        self.image_source_node_id = None

class AnalysisConfig:
    def __init__(self):
        self.nodes = {}
