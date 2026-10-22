import os
from contextlib import contextmanager

from dotenv import load_dotenv
from langgraph.checkpoint.postgres import PostgresSaver

from app.graph.build import build_graph

load_dotenv()

@contextmanager
def get_graph():
    """Build the graph with its state saved in PostgreSQL."""
    with PostgresSaver.from_conn_string(os.environ["DATABASE_URL"]) as checkpointer:
        checkpointer.setup()
        yield build_graph(checkpointer=checkpointer)
