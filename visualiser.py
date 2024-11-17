import os
import logging
from pyvis.network import Network
from langchain_groq import ChatGroq
from test_model import get_llm_instance
from langchain_community.graphs import Neo4jGraph
from dotenv import load_dotenv

load_dotenv()

# set up the environment variables
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# initialize logging
logging.basicConfig(level=logging.INFO)


class KnowledgeGraph:
    def __init__(self):
        self.llm = get_llm_instance()
        self.graph = Neo4jGraph(uri=NEO4J_URI, username=NEO4J_USERNAME, password=NEO4J_PASSWORD)

    def fetch_tool_output(self):
        """
        Dynamically query Neo4j to fetch relationships for the graph.

        Returns:
        - A list of tuples representing relationships (start_node, relationship, end_node).
        """
        try:
            query = """
            MATCH (start)-[rel]->(end)
            RETURN start.name AS start_node, type(rel) AS relationship, end.name AS end_node
            """
            results = self.graph.query(query)
            relationships = [
                (record["start_node"], record["relationship"], record["end_node"]) for record in results
            ]
            logging.info(f"Fetched relationships: {relationships}")
            return relationships
        except Exception as e:
            logging.error(f"Error fetching relationships from Neo4j: {e}")
            return []

    def add_relationships(self, tool_output):
        """
        Generate relationships dynamically based on tool output, filling in missing data with Groq if needed.

        Parameters:
        - tool_output: List of relationships in the format:
          [
              ("Node1", "RELATIONSHIP_TYPE", "Node2"),
              ("NodeA", "RELATIONSHIP_TYPE", "NodeB")
          ]

        Returns:
        - A completed list of relationships.
        """
        if not tool_output:
            # Use Groq to generate relationships if none are available
            prompt = "Generate relationships for a knowledge graph about UK child benefits."
            groq_response = self.llm.generate_response(prompt)
            logging.info(f"Groq response for missing data: {groq_response}")
            return self.parse_groq_response(groq_response)

        incomplete = any(len(item) != 3 for item in tool_output)
        if incomplete:
            # Use Groq to fill in incomplete relationships
            prompt = f"Complete the following relationships: {tool_output}"
            groq_response = self.llm.generate_response(prompt)
            logging.info(f"Groq response for incomplete data: {groq_response}")
            return self.parse_groq_response(groq_response)

        return tool_output

    @staticmethod
    def parse_groq_response(response):
        """
        Parse the Groq response into a list of relationships.

        Parameters:
        - response: The raw response from Groq.

        Returns:
        - A list of relationships in the format [(Node1, RELATIONSHIP_TYPE, Node2), ...].
        """
        relationships = []
        lines = response.split("\n")
        for line in lines:
            parts = line.strip().split(",")
            if len(parts) == 3:
                relationships.append(tuple(part.strip() for part in parts))
        return relationships

    def visualize_graph(self, relationships, output_file="knowledge_graph_visualization.html"):
        """
        Visualize the knowledge graph using PyVis and save it as an HTML file.

        Parameters:
        - relationships: A list of tuples representing relationships (start_node, relationship, end_node).
        - output_file: The name of the HTML file where the visualization will be saved.
        """
        net = Network(height="750px", width="100%", bgcolor="#222222", font_color="white")

        net.barnes_hut(gravity=-3000, central_gravity=0.2, spring_length=150, spring_strength=0.02)
        net.set_options("""
        var options = {
          "nodes": {
            "font": {
              "size": 16,
              "face": "arial",
              "color": "white",
              "strokeWidth": 2
            }
          },
          "edges": {
            "arrows": {"to": { "enabled": true, "scaleFactor": 1 }},
            "color": {"inherit": "both"},
            "smooth": true
          },
          "physics": {
            "enabled": true,
            "solver": "barnesHut",
            "barnesHut": {
              "gravitationalConstant": -20000,
              "centralGravity": 0.04,
              "springLength": 200,
              "springConstant": 0.01,
              "damping": 0.9
            },
            "minVelocity": 0.75
          }
        }
        """)

        # add nodes and edges from relationships
        for start_node, relationship, end_node in relationships:
            net.add_node(start_node, label=start_node, title=start_node)
            net.add_node(end_node, label=end_node, title=end_node)
            net.add_edge(start_node, end_node, title=relationship)

        # save the visualization to an HTML file
        net.write_html(output_file)
        logging.info(f"Graph visualization saved as {output_file}")

        return output_file  # return the path to the HTML file

    def generate_pyvis_graph(self):
        """
        Generate the PyVis graph dynamically and return the HTML file path.

        Returns:
        - The path to the generated HTML file.
        """
        # fetch tool output using Neo4j logic
        tool_output = self.fetch_tool_output()

        # generate relationships, filling in any missing information
        completed_relationships = self.add_relationships(tool_output)

        # visualize the graph in an HTML file and return the file path
        return self.visualize_graph(completed_relationships)


# if used as a standalone script
if __name__ == "__main__":
    kg = KnowledgeGraph()
    html_path = kg.generate_pyvis_graph()
    print(f"Knowledge graph HTML saved at: {html_path}")
