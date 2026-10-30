import pytest

from app.graph.routing import (
    MAX_ATTEMPTS,
    MAX_REVISIONS,
    after_approval,
    after_propose,
    after_retrieve,
    after_verify,
)

from app.graph.state import new_incident

def make_state(**changes):
    state = new_incident("test incident")
    state.update(changes)
    return state

def action(risk: str)-> dict:
    return {"name":"x","target":"y","reason":"z","risk":risk}

# ----------- After retrieve: question or incident? ----

def test_question_goes_to_answer():
    assert after_retrieve(make_state(intent="info_request")) == "answer"


def test_incident_goes_to_propose_fix():
    assert after_retrieve(make_state(intent="info_request")) == "answer"


# ---- after propose: is a human needed? ----
@pytest.mark.parametrize("risk ,expected",[("high","human_approval"),("low","execute")])
def test_risk_decides_whether_a_humn_is_needed(risk,expected):
    assert after_propose(make_state(proposed_action=action(risk))) == expected


def test_stale_approval_cannot_bypass_the_gate():
    state = make_state(approval = "approved",proposed_action=action("high"))
    assert after_propose(state) == "human_approval"


# ---- after approval -- 

def test_approved_action_executes():
    assert after_approval(make_state(approval="approved")) == "execute"

def test_rejection_loops_back_while_under_the_limit():
    state = make_state(approval="rejected", revisions=MAX_REVISIONS-1)
    assert after_approval(state) == "propose_fix"

def test_too_many_rejections_escalate():
    state = make_state(approval="rejected",revisions=MAX_REVISIONS)
    assert after_approval(state) == "escalate"


# ---- after verify -----

def test_resolved_incident_is_summarized():
    assert after_verify(make_state(resolved=True,attempts=1)) == "summarize"

def test_failed_fix_retries_while_under_the_limit():
    state = make_state(resolved=False,attempts=MAX_ATTEMPTS-1)
    assert after_verify(state) == "propose_fix"

def test_too_many_failed_attempts_escalate():
    state = make_state(resolved=False, attempts=MAX_ATTEMPTS)
    assert after_verify(state) == "escalate"

