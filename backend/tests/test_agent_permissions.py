"""Tests for bounded agent permissions and operational scopes."""

import pytest
from app.agents.detective import RevenueDetective
from app.agents.diagnosis import DiagnosisAgent
from app.agents.planner import RecoveryPlanner
from app.agents.execution import ExecutionAgent
from app.tools.gateway import ToolGateway


def test_agent_permission_boundaries():
    detective = RevenueDetective()
    diagnosis = DiagnosisAgent()
    planner = RecoveryPlanner()
    exec_agent = ExecutionAgent()

    # Detective, Diagnosis, and Planner MUST NOT possess gateway execution handles
    assert not hasattr(detective, "execute_payment")
    assert not hasattr(detective, "gateway")
    assert not hasattr(diagnosis, "gateway")
    assert not hasattr(planner, "gateway")

    # Only ExecutionAgent dispatches via ToolGateway
    assert hasattr(exec_agent, "gateway")
    assert isinstance(exec_agent.gateway, ToolGateway)
