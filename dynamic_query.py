import os
from typing import Dict, List
from langchain_community.graphs import Neo4jGraph
from dotenv import load_dotenv

# load environment variables
load_dotenv()

# setup neo4j connection
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

graph = Neo4jGraph(uri=NEO4J_URI, username=NEO4J_USERNAME, password=NEO4J_PASSWORD)


def fetch_available_queries() -> List[Dict[str, str]]:
    """
    fetch query templates dynamically from neo4j.

    returns:
        list of dictionaries with query names and corresponding cypher queries.
    """
    query_template = """
    MATCH (q:QueryTemplate)
    RETURN q.name AS query_name, q.template AS query_template
    """
    try:
        results = graph.query(query_template)
        return [{"query_name": record["query_name"], "query_template": record["query_template"]} for record in results]
    except Exception as e:
        raise RuntimeError(f"failed to fetch queries from the database: {e}")


def get_query(query_name: str) -> str:
    """
    retrieve a specific query by its name.

    args:
        query_name: the name of the query to fetch.

    returns:
        the cypher query string for the specified query name.
    """
    queries = fetch_available_queries()
    query_dict = {query["query_name"]: query["query_template"] for query in queries}
    return query_dict.get(query_name, "")


def list_queries() -> List[str]:
    """
    list all available query names.

    returns:
        list of query names.
    """
    queries = fetch_available_queries()
    return [query["query_name"] for query in queries]


# test dynamic queries
if __name__ == "__main__":
    try:
        available_queries = list_queries()
        print("available queries:", available_queries)

        if available_queries:
            first_query_name = available_queries[0]
            print(f"query for '{first_query_name}':")
            print(get_query(first_query_name))
        else:
            print("no queries available.")
    except Exception as e:
        print(f"error: {e}")
