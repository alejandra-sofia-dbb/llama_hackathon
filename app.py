import streamlit as st
import time
from test_model import agent_executor, logs  # import agent executor and logs
from see_graph import KnowledgeGraph  # import visualization generation function

# initialize the knowledge graph
kg = KnowledgeGraph()
html_file = kg.generate_pyvis_graph()

# page configuration
st.set_page_config(
    page_title="GovAssist",
    page_icon="✅",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# custom CSS to style the app and improve layout
st.markdown("""
<style>
    /* adjust chat and graph column spacing */
    [data-testid="stVerticalBlock"] > [style*="flex-direction: column;"] > [data-testid="stVerticalBlock"]:nth-child(1) {
        margin-right: 20px;
    }
    .stApp, [data-testid="stAppViewContainer"] {
        background-color: #001f3f; /* dark background */
    }
    .chat-container {
        padding: 10px;
    }
    .user-message, .bot-message {
        padding: 10px 15px;
        border-radius: 15px;
        margin: 5px 0;
        max-width: 75%;
        word-wrap: break-word;
    }
    .user-message {
        background-color: #e9ecef;
        margin-left: auto;
        text-align: right;
    }
    .bot-message {
        background-color: #007bff;
        color: white;
    }
    #MainMenu, footer {visibility: hidden;}
    .stButton>button {
        background-color: #007bff;
        color: white;
        border-radius: 5px;
        padding: 10px 24px;
    }
    .stButton>button:hover {
        background-color: #0056b3;
    }
    .stTextArea textarea {
        background-color: white;
        color: black;
        border-radius: 5px;
    }
    .graph-title {
        text-align: center;
        color: black;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# define layout with two columns (chat and graph visualization)
chat_col, graph_col = st.columns([2, 1])

# initialize session state for chat history, user input, and graph visualization
if "chat_history" not in st.session_state:
    st.session_state.chat_history = [
        {"role": "assistant", "content": "Hello! I can help you with information about benefits. What would you like to know?"}
    ]

if "user_input" not in st.session_state:
    st.session_state.user_input = ""

if "html_file" not in st.session_state:
    st.session_state.html_file = None

# chat interface in the left column
with chat_col:
    # header
    st.markdown("""
    <div style="text-align: center;">
        <h1 style='margin: 0; font-size: 2.5rem; color: white;'>GovAssist 🦙</h1>
        <h3 style='color: white;'>Your virtual assistant for exploring government aid programs</h3>
    </div>
    """, unsafe_allow_html=True)

    # display chat history
    st.markdown("<div class='chat-container'>", unsafe_allow_html=True)
    for i, message in enumerate(st.session_state.chat_history):
        if message["role"] == "user":
            st.markdown(f"<div class='user-message'>{message['content']}</div>", unsafe_allow_html=True)
        else:
            # show a "generate graph" button for the most recent bot message
            is_latest_bot = (i == len(st.session_state.chat_history) - 1 and message["role"] == "assistant")
            if is_latest_bot:
                st.markdown(f"<div class='bot-message'>{message['content']}</div>", unsafe_allow_html=True)
                if st.button("🧠", key=f"viz_latest_{i}"):
                    st.session_state.html_file = kg.generate_pyvis_graph()
            else:
                st.markdown(f"<div class='bot-message'>{message['content']}</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # user input text area
    user_input = st.text_area("Your message:", placeholder="Type your question here...", key="user_input")

    if st.button("Send"):
        if user_input.strip():
            # add user input to chat history
            st.session_state.chat_history.append({"role": "user", "content": user_input})

            try:
                # format chat history for agent processing
                formatted_history = [
                    (st.session_state.chat_history[i]["content"], st.session_state.chat_history[i + 1]["content"])
                    for i in range(0, len(st.session_state.chat_history) - 1, 2)
                ]

                # invoke agent executor
                result = agent_executor.invoke({"input": user_input, "chat_history": formatted_history})
                assistant_response = result["output"]

                # add assistant response to chat history
                st.session_state.chat_history.append({"role": "assistant", "content": assistant_response})

                # save logs if available
                if logs:
                    st.session_state.logs = logs.copy()

            except Exception as e:
                # handle errors gracefully
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": f"An error occurred: {str(e)}. Please try again."
                })

            # rerun app to refresh chat
            st.experimental_rerun()

# visualization interface in the right column
with graph_col:
    st.markdown("<h3 class='graph-title'>Graph Visualization</h3>", unsafe_allow_html=True)
    if st.session_state.html_file:
        # render the HTML file if generated
        with open(st.session_state.html_file, "r") as f:
            html_content = f.read()
        st.components.v1.html(html_content, height=750, scrolling=True)
    else:
        st.markdown(
            "<p style='color: black;'>Click the 🧠 button to generate and view the knowledge graph.</p>",
            unsafe_allow_html=True,
        )
