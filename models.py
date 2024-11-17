import os
import logging
import streamlit as st
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field
from dotenv import load_dotenv

from queries import get_query, list_queries
from validation_agent import validate_response_tool, get_validation_logs
from langchain_community.graphs import Neo4jGraph
from langchain_community.vectorstores.neo4j_vector import remove_lucene_chars
from langchain_groq import ChatGroq
from langchain.agents import AgentExecutor
from langchain.agents.output_parsers.openai_tools import OpenAIToolsAgentOutputParser
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema import AIMessage, HumanMessage
from langchain.tools import tool

# load environment variables
load_dotenv()

# global configurations
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# set up logging
logging.basicConfig(level=logging.INFO)

# initialize Neo4j graph connection
graph = Neo4jGraph(refresh_schema=False)

# initialize logs for tracking tool usage
logs = []

# singleton pattern for ChatGroq
_chatgroq_instance = None


def get_llm_instance():
    """initialize or retrieve a ChatGroq instance"""
    global _chatgroq_instance
    if _chatgroq_instance is None:
        try:
            _chatgroq_instance = ChatGroq(
                model="llama-3.2-3b-preview",
                temperature=0.0,
            )
        except ImportError:
            logging.warning("ChatGroq not available; using mock response.")
            _chatgroq_instance = None
    return _chatgroq_instance


llm = get_llm_instance()

# LlamaGuard for response safety
class LlamaGuard:
    def is_safe(self, response: str) -> bool:
        """validate if the response is safe (mock implementation for now)"""
        # custom logic can be added here
        return True


llama_guard = LlamaGuard()

# create full-text search indices in Neo4j
graph.query(
    """
    CREATE FULLTEXT INDEX child_benefit_topic IF NOT EXISTS FOR (cb:ChildBenefit) ON EACH [cb.topic];
    CREATE FULLTEXT INDEX document_type IF NOT EXISTS FOR (cb:Document) ON EACH [cb.documentType];
    CREATE FULLTEXT INDEX requirement_type IF NOT EXISTS FOR (cb:Requirement) ON EACH [cb.requirementType];
    """
)


def generate_full_text_query(input: str) -> str:
    """
    generate a full-text search query for Neo4j based on input
    """
    words = [remove_lucene_chars(word) for word in input.split()]
    return " AND ".join([f"{word}~2" for word in words])


@tool
def get_benefit_info(
    query_name: Optional[str] = Field(description="query to fetch benefit details"),
    parameters: Optional[Dict[str, Any]] = Field(
        default_factory=dict, description="optional parameters for query customization"
    ),
) -> str:
    """
    fetch benefit information from the graph using query name and parameters
    """
    if not query_name:
        return "Please specify a benefit or type of information you're looking for."

    # validate the query name
    available_queries = list_queries()
    if query_name not in available_queries:
        return "The requested query is not available. Please specify a valid query."

    try:
        # retrieve the Cypher query
        cypher_query = get_query(query_name)
        if not cypher_query:
            raise ValueError(f"Query '{query_name}' could not be found in the query library.")
        
        # execute the query
        data = graph.query(cypher_query, params=parameters)
        if not data:
            return "No results found. Please refine your query or provide more details."

        # format and return the result
        return str(data)
    except Exception as e:
        return f"An error occurred while processing the query: {str(e)}"


# define the prompt for LLM interaction
prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a knowledgeable assistant providing accurate information about UK government benefits. "
            "Interpret user input and use the appropriate tools to generate responses. Avoid guessing or hallucinating."
        ),
        MessagesPlaceholder(variable_name="chat_history"),
        ("user", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ]
)


def validate_response_against_graph(tool_result: List[Dict], chatbot_response: str) -> bool:
    """validate chatbot response against graph data to prevent hallucinations"""
    allowed_data = {str(value) for record in tool_result for value in record.values()}
    response_words = set(chatbot_response.split())
    return response_words.issubset(allowed_data)


def process_query(user_query: str, query_name: str, parameters: Optional[Dict[str, Any]] = None) -> Dict:
    """
    process a user query and return validated results
    """
    try:
        # validate and process query
        result = get_benefit_info(query_name=query_name, parameters=parameters or {})
        chatbot_response = str(result)

        # safety validation
        if not llama_guard.is_safe(chatbot_response):
            return {"error": "Response contains unsafe content.", "response": None}

        # log response and validation
        logs.append({"query": user_query, "response": chatbot_response})

        return {"response": chatbot_response, "logs": logs}

    except Exception as e:
        logging.error(f"Error processing query: {str(e)}")
        return {"error": str(e), "response": None}


# configure the agent
tools = [get_benefit_info]
llm_with_tools = llm.bind_tools(tools=tools) if llm else None

agent = (
    {
        "input": lambda x: x["input"],
        "chat_history": lambda x: _format_chat_history(x["chat_history"]) if x.get("chat_history") else [],
        "agent_scratchpad": lambda x: x.get("intermediate_steps", []),
    }
    | prompt
    | llm_with_tools
    | OpenAIToolsAgentOutputParser()
)


# Streamlit app example (main entry point)
def run_app():
    st.title("Government Benefits Knowledge Assistant")
    user_input = st.text_input("Ask about UK government benefits:")
    query_name = st.text_input("Specify query name:")
    parameters = st.text_area("Enter parameters (JSON format):")

    if st.button("Submit Query"):
        try:
            params = eval(parameters) if parameters else {}
            response = process_query(user_input, query_name, parameters=params)
            st.json(response)
        except Exception as e:
            st.error(f"Error: {e}")


if __name__ == "__main__":
    run_app()
