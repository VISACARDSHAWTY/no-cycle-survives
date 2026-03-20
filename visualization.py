import networkx as nx
import matplotlib.pyplot as plt

def visualize_precedence_graph(graph_dict):
    """
    Takes the graph dictionary from your precedence_graph function 
    and displays a visual representation.
    """
    G = nx.DiGraph()
    
    # Add nodes and edges from your graph dictionary
    for node, neighbors in graph_dict.items():
        G.add_node(f"T{node}")
        for neighbor in neighbors:
            G.add_edge(f"T{node}", f"T{neighbor}")
    
    plt.figure(figsize=(8, 6))
    pos = nx.spring_layout(G)  # Positioning algorithm
    
    nx.draw(G, pos, with_labels=True, node_color='skyblue', 
            node_size=2000, edge_color='black', linewidths=2, 
            font_size=15, font_weight='bold', arrowsize=20)
    
    plt.title("Transaction Precedence (Serialization) Graph")
    plt.show()