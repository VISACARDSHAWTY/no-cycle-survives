import networkx as nx
import matplotlib.pyplot as plt

def visualize_precedence_graph(graph_data):
    """
    Visualizes the precedence graph using NetworkX and Matplotlib.
    graph_data: Dictionary where keys are transaction IDs and 
                values are sets of transaction IDs they depend on.
    """
    # 1. Create a Directed Graph object
    G = nx.DiGraph()

    # 2. Add edges from the graph dictionary
    for node, neighbors in graph_data.items():
        for neighbor in neighbors:
            G.add_edge(node, neighbor)

    # 3. Handle nodes with no outgoing edges (ensure they appear in the plot)
    for node in graph_data.keys():
        if node not in G:
            G.add_node(node)

    # 4. Set up the layout (spring_layout looks good for small schedules)
    pos = nx.spring_layout(G, seed=42) 

    plt.figure(figsize=(8, 6))
    plt.title("Precedence Graph (Conflict Serializability)")

    # 5. Draw the components
    nx.draw_networkx_nodes(G, pos, node_size=700, node_color='skyblue')
    nx.draw_networkx_labels(G, pos, font_size=12, font_family="sans-serif")
    nx.draw_networkx_edges(
        G, pos, 
        edgelist=G.edges(), 
        edge_color='black', 
        arrowsize=20, 
        arrowstyle='->',
        connectionstyle='arc3,rad=0.1' # Slight curve to show bidirectional edges
    )

    plt.axis('off')
    plt.tight_layout()
    
    # Show the plot
    print("Displaying graph...")
    plt.show()

