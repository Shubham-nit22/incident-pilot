import random 
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

ActionName = Literal[
    "clear_cache","scale_up","restart_service","rollback_deploy","block_ip"
]

# The risk of each action is decided HERE, in code. Never by the LLM.
ACTIONS : dict[str,dict[str,str]] = {
    "clear_cache":{
        "risk":"low",
        "description":"Clear the application cache of a service",
    },
    "scale_up":{
        "risk":"low",
        "description":"Add more instance of a service to handle extra load",
    },
    "restart_service":{
        "risk":"high",
        "description":"Restart a running service (cause brief downtime)",
    },
    "rollback_deploy":{
        "risk":"high",
        "description":"Roll a service back to its previous release.",
    },
    "block_ip":{
        "risk":"high",
        "description":"Block an IP address or range at the firewall.",
    },
}

LOG_FILE = Path("logs/action.log")
HEALTH_SUCCESS_RATE = 0.6

def get_risk(action_name : str) -> str:
    return ACTIONS[action_name]["risk"]

def run_action(name: str, target : str)-> dict :
    """SIMULATED : Only appends a line to a log file."""
    LOG_FILE.parent.mkdir(exist_ok=True)
    timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    with LOG_FILE.open("a",encoding="utf-8") as f:
        f.write(f"{timestamp} | {name} | {target} \n")
        return {"ok":True,"message": f"[SIMULATED] {name} executed on {target}"}


def check_health(target : str) -> bool:
    """SIMULATED health check : randomly passes of fails."""
    return random.random() < HEALTH_SUCCESS_RATE