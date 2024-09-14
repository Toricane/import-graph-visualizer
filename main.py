import ast
import json
import os

from pyvis.network import Network


# New function to read requirements.txt
def read_requirements(project_directory):
    req_file = os.path.join(project_directory, "requirements.txt")
    if os.path.exists(req_file):
        with open(req_file, "r") as file:
            return {line.split("==")[0].lower() for line in file if line.strip()}
    return set()


# Step 1: Walk through directories and extract imports
def get_imports_from_file(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        node = ast.parse(file.read(), filename=file_path)

    imports = []

    for n in ast.walk(node):
        if isinstance(n, ast.Import):
            for alias in n.names:
                imports.append(alias.name)
        elif isinstance(n, ast.ImportFrom):
            module = n.module if n.module else ""
            imports.append(module)

    return imports


# Step 2: Traverse project directory and build graph
def build_import_graph(project_directory):
    net = Network(height="750px", width="100%", bgcolor="#222222", font_color="white")
    added_nodes = set()
    external_modules = read_requirements(project_directory)

    for root, _, files in os.walk(project_directory):
        for file in files:
            if file.endswith(".py"):
                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, project_directory)

                # Add node for this Python file
                if relative_path not in added_nodes:
                    net.add_node(relative_path, label=relative_path, color="#4CAF50")
                    added_nodes.add(relative_path)

                # Get imports from the file
                imports = get_imports_from_file(file_path)

                for imp in imports:
                    # Determine the color based on whether it's an external module
                    color = "#FF5722" if imp.lower() in external_modules else "#2196F3"

                    # Add node for imported module if it doesn't exist
                    if imp not in added_nodes:
                        net.add_node(imp, label=imp, color=color)
                        added_nodes.add(imp)
                    # Add edge: file -> imported module
                    net.add_edge(relative_path, imp)

    return net


# Step 3: Visualize the graph with a legend
def visualize_import_graph(net, output_file="import_graph.html"):
    # Configure physics for better initial layout
    physics_options = {
        "physics": {
            "forceAtlas2Based": {
                "gravitationalConstant": -50,
                "centralGravity": 0.01,
                "springLength": 100,
                "springConstant": 0.08,
                "damping": 0.4,
                "avoidOverlap": 0,
            },
            "maxVelocity": 50,
            "minVelocity": 0.1,
            "solver": "forceAtlas2Based",
            "stabilization": {
                "enabled": True,
                "iterations": 1000,
                "updateInterval": 25,
            },
            "enabled": True,
        }
    }

    # Set physics options
    net.set_options(json.dumps(physics_options))

    # Generate HTML content
    html_content = net.generate_html()

    # Custom elements to inject (including a legend for node colors)
    custom_elements = """
    <style>
    #physics-button {
        position: absolute;
        top: 10px;
        left: 10px;
        z-index: 1000;
    }
    #legend {
        position: absolute;
        top: 50px;
        left: 10px;
        z-index: 1000;
        background-color: white;
        padding: 10px;
        border-radius: 5px;
        box-shadow: 0 0 10px rgba(0,0,0,0.5);
    }
    #legend div {
        margin-bottom: 5px;
    }
    #legend div span {
        display: inline-block;
        width: 12px;
        height: 12px;
        margin-right: 5px;
        vertical-align: middle;
    }
    .external-module { background-color: #FF5722; }
    .internal-module { background-color: #2196F3; }
    .file-node { background-color: #4CAF50; }
    </style>

    <div id="legend">
        <div><span class="file-node"></span> Python File</div>
        <div><span class="internal-module"></span> Internal Module</div>
        <div><span class="external-module"></span> External Library</div>
    </div>

    <button id="physics-button" onclick="togglePhysics()">Disable Physics</button>
    <script>
    function togglePhysics() {
        var physics = network.physics.options.enabled;
        network.setOptions({ physics: { enabled: !physics } });
        document.getElementById("physics-button").innerHTML = physics ? "Enable Physics" : "Disable Physics";
    }
    </script>
    """

    # Find a suitable injection point
    injection_point = html_content.find('<div id="mynetwork">')
    if injection_point == -1:
        injection_point = html_content.find("<body")
        if injection_point == -1:
            injection_point = html_content.find("<html")
            if injection_point == -1:
                # If all else fails, inject at the beginning of the file
                injection_point = 0

    # Inject custom elements
    html_content = f"{html_content[:injection_point]}{custom_elements}{html_content[injection_point:]}"

    # Save the final HTML
    with open(output_file, "w", encoding="utf-8") as file:
        file.write(html_content)

    print(f"Graph visualization saved to {output_file}")


# Helper function to identify the project folder with Python files
def find_project_folder(current_directory):
    for folder_name in os.listdir(current_directory):
        folder_path = os.path.join(current_directory, folder_name)
        if os.path.isdir(folder_path):
            # Check if the folder contains any .py files (directly or within subfolders)
            for root, _, files in os.walk(folder_path):
                if any(file.endswith(".py") for file in files):
                    return folder_path  # Return the first folder that has Python files
    return None


# Step 4: Main function
if __name__ == "__main__":
    # Get the folder next to this main.py file (parent directory)
    current_directory = os.path.dirname(os.path.abspath(__file__))

    # Find the project folder next to main.py containing Python files
    project_directory = find_project_folder(current_directory)

    if project_directory:
        print(f"Project folder found: {project_directory}")
        net = build_import_graph(project_directory)
        visualize_import_graph(net)
    else:
        print("No project folder with Python files found.")
