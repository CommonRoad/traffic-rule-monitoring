from typing import Dict, List

import matplotlib
import networkx as nx
import rvm

matplotlib.use("TkAgg")


def visualize_tree_from_dict(tree_dict: Dict[int, List[int]], root_nodes: List[int], labels: Dict[int, str]) -> None:
    """
    Visualizes Hydra2 tree structure highlighting root and leaf nodes.

    :param tree_dict: Tree structure.
    :param root_nodes: List of root nodes.
    :param labels: Mapping of node IDs to logical representation.
    """
    node_size = 1500
    tree = nx.DiGraph(tree_dict)

    leaf_nodes = [node for node in tree.nodes() if tree.out_degree(node) == 0]
    pos = nx.drawing.layout.bfs_layout(tree, root_nodes)
    nx.draw(
        tree,
        pos,
        with_labels=True,
        labels=labels,
        node_size=node_size,
        node_color="lightblue",
        font_size=10,
    )
    nx.draw_networkx_nodes(tree, pos, nodelist=root_nodes, node_color="green", node_size=node_size)
    nx.draw_networkx_nodes(tree, pos, nodelist=leaf_nodes, node_color="red", node_size=node_size)

    matplotlib.pyplot.title("Tree Visualization")
    matplotlib.pyplot.axis("off")
    matplotlib.pyplot.show()


specs = [
    (
        "R_G1",
        "A x_o in DALL. (!((!((true S[0, 30] (!(in_single_lane(x_o)) & P((in_single_lane(x_o) & orientation_towards(x_o, 'x_ego'))) & in_same_lane(x_o, 'x_ego') & orientation_towards(x_o, 'x_ego')))) & in_front_of('x_ego', x_o) & in_same_lane('x_ego', x_o) & lane_based_orientation_similar('x_ego', x_o))) | keeps_safe_distance_prec('x_ego', x_o))",
    ),
    (
        "R_G2",
        "(!(decelerates('x_ego', 'a_brake')) | (!(E x_o in DALL. (in_front_of('x_ego', x_o) & in_same_lane('x_ego', x_o) & lane_based_orientation_similar('x_ego', x_o))) & !(decelerates('x_ego', 'a_abrupt'))) | E x_o in DALL. (!(brakes_stronger('x_ego', x_o, 'a_abrupt')) & in_front_of('x_ego', x_o) & in_same_lane('x_ego', x_o) & keeps_safe_distance_prec('x_ego', x_o) & lane_based_orientation_similar('x_ego', x_o)))",
    ),
    (
        "R_G3",
        "G(keeps_braking_speed_limit('x_ego') & keeps_fov_speed_limit('x_ego') & keeps_lane_speed_limit('x_ego') & keeps_type_speed_limit('x_ego'))",
    ),
]


formulas = [rvm.Parser.parse(form[1], form[0]) for form in specs]
mon = rvm.Hydra2(formulas)
tree_vis = mon.to_tree()
visualize_tree_from_dict(tree_vis.tree, tree_vis.rootIDs, tree_vis.nodeTypes)
