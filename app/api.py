import json
import os
import secrets
import uuid
from contextlib import asynccontextmanager
from typing import Literal,Optional

from dotenv import load_dotenv
from fastapi import Depends,FastAPI,HTTPException,Request
from fastapi.responses import StreamingResponse
from fastapi.security import APIKeyHeader
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.types import Command
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool
from pydantic import BaseModel,Field

from app.graph.build import build_graph
from app.graph.state import new_incident

load_dotenv()

# ----------- Startup: connection pool + graph -------

@asynccontextmanager
async def lifespan(app: FastAPI):
    pool = ConnectionPool(
        conninfo=os.environ["DATABASE_URL"],
        max_size=5,
        kwargs={"autocommit":True,"prepare_threshold":0,"row_factory":dict_row},
        check=ConnectionPool.check_connection,
        open=False,
    )
    pool.open()
    checkpointer = PostgresSaver(pool)
    checkpointer.setup()
    app.state.graph = build_graph(checkpointer=checkpointer)
    yield
    pool.close()

app = FastAPI(title="IncidentPilot",version="0.1.0",lifespan=lifespan)

api_key_header = APIKeyHeader(name="X-API-Key",auto_error=False)

def require_api_key(key: Optional[str]= Depends(api_key_header)) -> None:
    expected = os.environ.get("API_KEY","")
    if not expected or not key or not secrets.compare_digest(key.encode(),expected.encode()):
        raise HTTPException(status_code=401,detail="Invalid or missing API key")


def get_graph(request : Request):
    return request.app.state.graph

#---- request and response shapes -------

class IncidentRequest(BaseModel):
    text : str = Field(min_length=10, max_length=2000)

class ApprovalRequest(BaseModel):
    approval : Literal["approved","rejected"]
    note : Optional[str] = Field(default=None,max_length=500)

class IncidentStatus(BaseModel):
    thread_id : str
    status : Literal["awaiting_approval","resolved","escalated","answered"]
    category : Optional[str] = None
    pending_action : Optional[dict] = None
    summary : Optional[str] = None
    history : list[str] = []


#--------- helpers ---------

def config_for(thread_id : str) -> dict:
    return {"configurable":{"thread_id":thread_id}}


def describe(graph,thread_id:str) -> IncidentStatus:
    snapshot = graph.get_state(config_for(thread_id))
    values = snapshot.values
    if not values:
        raise HTTPException(status_code=404,detail="Incident not found")

    pending = None
    if snapshot.next:
        status = "awaiting_approval"
        for task in snapshot.tasks:
            if task.interrupts:
                pending = task.interrupts[0].value.get("action")
                break
    elif values.get("intent") == "info_request":
        status = "answered"
    elif values.get("resolved"):
        status = "resolved"
    else:
        status = "escalated"


    return IncidentStatus(
        thread_id=thread_id,
        status=status,
        category=values.get("category"),
        pending_action=pending,
        summary = values.get("summary"),
        history=values.get("history",[]),
    )

def sse(event : str, data : dict) -> str:
    return f"event: {event}\ndata : {json.dumps(data)}\n\n"


# -- endpoints --------

@app.get("/health")
def health():
    return {"ok":True}

@app.post("/incidents",response_model=IncidentStatus,dependencies=[Depends(require_api_key)])
def create_incident(body: IncidentRequest,graph=Depends(get_graph)):
    """Run an incident untill it finishes or needs a human decision"""
    thread_id = f"incident-{uuid.uuid4().hex[:8]}"
    graph.invoke(new_incident(body.text), config_for(thread_id))
    return describe(graph,thread_id)

@app.post("/incident/stream",dependencies=[Depends(require_api_key)])
def stream_incident(body: IncidentRequest, graph=Depends(get_graph)):
    """Same as above, but sends progess events as each step finishes,"""
    thread_id = f"incident-{uuid.uuid4().hex[:8]}"

    def events():
        yield sse("started",{"thread_id":thread_id})
        try:
            for update in graph.stream(
                new_incident(body.text), config_for(thread_id), stream_mode = "updates"
            ):
                for node, payload in update.items():
                    if node == "__interrupt__":
                        yield sse( "awaiting_approval",{"thread_id":thread_id})
                    else:
                        log = (payload or {}).get("history",[])
                        yield sse("step",{"node":node,"log":log})

            yield sse("status",describe(graph,thread_id).model_dump())
        except Exception as error:
            yield sse("error",{"message":repr(error)[:300]})
    return StreamingResponse(events(), media_type="text/event-stream")

@app.get(
    "/incidents/{thread_id}",
    response_model=IncidentStatus,
    dependencies=[Depends(require_api_key)],
)
def get_incidents(thread_id:str,graph=Depends(get_graph)):
    return describe(graph,thread_id)


@app.post("/incidents/{thread_id}/approve",
          response_model=IncidentStatus,
          dependencies=[Depends(require_api_key)])
)
def approve_incident(thread_id:str, body : ApprovalRequest, graph=Depends(get_graph)):
    current = describe(graph, thread_id)
    if current.status != "awaiting_approval":
        raise HTTPException(
            status_code=409,
            detail=f"Incident is not waiting for approval (status : {current.status})",
        )
    graph.invoke(Command(resume=body.model_dump()), config_for(thread_id))
    return describe(graph, thread_id)



