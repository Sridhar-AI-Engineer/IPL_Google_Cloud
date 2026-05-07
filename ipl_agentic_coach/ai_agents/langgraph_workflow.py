"""
LangGraph Workflow
==================
Defines the IPL Tactical Decision Pipeline as a LangGraph StateGraph.
Each agent becomes a node; edges define ordered execution flow.
Falls back gracefully if LangGraph is not installed.
"""

from __future__ import annotations

import json
from importlib import import_module
from typing import Any, TypedDict

from .fan_decision_agent import FanDecisionAgent
from .historical_evaluator_agent import HistoricalEvaluatorAgent
from .simulator_agent import SimulatorAgent
from .scoring_agent import ScoringAgent


# ── Shared State Schema ────────────────────────────────────────────────────────

class TacticalState(TypedDict, total=False):
    field_input: str
    bowler_input: str
    strategy_input: str
    historical_move: dict
    fan_move: dict
    historical_score: float
    simulation_impact: dict
    final_score: float
    feedback: str
    error: str


# ── Agent Node Functions ───────────────────────────────────────────────────────

_fan_agent = FanDecisionAgent()
_hist_agent = HistoricalEvaluatorAgent()
_sim_agent = SimulatorAgent()
_score_agent = ScoringAgent()


def node_parse_fan_input(state: TacticalState) -> TacticalState:
    """Node 1: Parse raw fan inputs into structured tactical move."""
    fan_move = _fan_agent.parse_input(
        state.get("field_input", ""),
        state.get("bowler_input", ""),
        state.get("strategy_input", ""),
    )
    return {**state, "fan_move": fan_move}


def node_evaluate_historical(state: TacticalState) -> TacticalState:
    """Node 2: Evaluate fan move against historical captain decisions."""
    fan_move = state.get("fan_move", {})
    historical_move = state.get("historical_move", {})
    score = _hist_agent.evaluate(fan_move, historical_move)
    return {**state, "historical_score": score}


def node_simulate_impact(state: TacticalState) -> TacticalState:
    """Node 3: Simulate the match impact (runs saved, wicket chance, pressure)."""
    fan_move = state.get("fan_move", {})
    impact = _sim_agent.simulate(fan_move)
    return {**state, "simulation_impact": impact}


def node_calculate_score(state: TacticalState) -> TacticalState:
    """Node 4: Combine outputs into final score and feedback."""
    hist_score = state.get("historical_score", 0.5)
    sim_impact = state.get("simulation_impact", {})
    final = _score_agent.calculate_score(hist_score, sim_impact)
    feedback = _score_agent.generate_feedback(final, sim_impact)
    return {**state, "final_score": final, "feedback": feedback}


# ── LangGraph Graph Builder ────────────────────────────────────────────────────

def _build_langgraph() -> Any | None:
    """Build a compiled LangGraph StateGraph for the tactical pipeline."""
    try:
        langgraph_mod = import_module("langgraph.graph")
        StateGraph = langgraph_mod.StateGraph
        END = langgraph_mod.END
    except Exception:
        return None

    try:
        graph = StateGraph(TacticalState)

        # Register nodes
        graph.add_node("parse_fan_input", node_parse_fan_input)
        graph.add_node("evaluate_historical", node_evaluate_historical)
        graph.add_node("simulate_impact", node_simulate_impact)
        graph.add_node("calculate_score", node_calculate_score)

        # Define edges (sequential flow)
        graph.set_entry_point("parse_fan_input")
        graph.add_edge("parse_fan_input", "evaluate_historical")
        graph.add_edge("evaluate_historical", "simulate_impact")
        graph.add_edge("simulate_impact", "calculate_score")
        graph.add_edge("calculate_score", END)

        return graph.compile()
    except Exception:
        return None


def get_workflow_schema() -> dict[str, Any]:
    """Return the workflow graph schema for API documentation and visualization."""
    return {
        "name": "IPL Tactical Decision Workflow",
        "description": "LangGraph StateGraph orchestrating multi-agent IPL analysis",
        "nodes": [
            {
                "id": "parse_fan_input",
                "label": "Fan Decision Agent",
                "description": "Parse field, bowler, strategy inputs into structured move",
                "input_keys": ["field_input", "bowler_input", "strategy_input"],
                "output_keys": ["fan_move"],
            },
            {
                "id": "evaluate_historical",
                "label": "Historical Evaluator Agent",
                "description": "Compare fan move against historical IPL captain decisions",
                "input_keys": ["fan_move", "historical_move"],
                "output_keys": ["historical_score"],
            },
            {
                "id": "simulate_impact",
                "label": "Simulator Agent",
                "description": "Predict runs saved, wicket chance, and pressure index",
                "input_keys": ["fan_move"],
                "output_keys": ["simulation_impact"],
            },
            {
                "id": "calculate_score",
                "label": "Scoring Agent",
                "description": "Combine scores into final tactical rating and feedback",
                "input_keys": ["historical_score", "simulation_impact"],
                "output_keys": ["final_score", "feedback"],
            },
        ],
        "edges": [
            {"from": "START", "to": "parse_fan_input"},
            {"from": "parse_fan_input", "to": "evaluate_historical"},
            {"from": "evaluate_historical", "to": "simulate_impact"},
            {"from": "simulate_impact", "to": "calculate_score"},
            {"from": "calculate_score", "to": "END"},
        ],
        "state_keys": list(TacticalState.__annotations__.keys()),
    }


# ── Main Pipeline Class ────────────────────────────────────────────────────────

class LangGraphTacticalWorkflow:
    """
    Runs the IPL tactical pipeline as a LangGraph compiled workflow.
    Provides identical results to AgenticPipeline but with graph-based execution.
    """

    def __init__(self):
        self._compiled = _build_langgraph()
        self._schema = get_workflow_schema()

    @property
    def using_langgraph(self) -> bool:
        return self._compiled is not None

    def run(
        self,
        field_input: str,
        bowler_input: str,
        strategy_input: str,
        historical_move: dict[str, Any],
    ) -> dict[str, Any]:
        """Execute the full workflow and return structured result."""
        initial_state: TacticalState = {
            "field_input": field_input,
            "bowler_input": bowler_input,
            "strategy_input": strategy_input,
            "historical_move": historical_move,
        }

        if self._compiled is not None:
            try:
                final_state = self._compiled.invoke(initial_state)
                return self._format_result(final_state)
            except Exception:
                pass

        # Fallback: run nodes manually in sequence
        state = node_parse_fan_input(initial_state)
        state = node_evaluate_historical(state)
        state = node_simulate_impact(state)
        state = node_calculate_score(state)
        return self._format_result(state)

    @staticmethod
    def _format_result(state: TacticalState) -> dict[str, Any]:
        return {
            "score": state.get("final_score", 0.0),
            "feedback": state.get("feedback", ""),
            "historical_score": round(state.get("historical_score", 0.0), 3),
            "simulation_impact": state.get("simulation_impact", {}),
            "normalized_move": state.get("fan_move", {}),
        }

    def get_schema(self) -> dict[str, Any]:
        return self._schema

    def mermaid_diagram(self) -> str:
        """Generate a Mermaid flowchart string for UI embedding."""
        lines = ["flowchart TD"]
        for edge in self._schema["edges"]:
            src = edge["from"].replace("START", "🏏 START").replace("END", "🏆 END")
            dst = edge["to"].replace("START", "🏏 START").replace("END", "🏆 END")
            # Find label for non-special nodes
            node_labels = {n["id"]: n["label"] for n in self._schema["nodes"]}
            src_label = node_labels.get(edge["from"], src)
            dst_label = node_labels.get(edge["to"], dst)
            lines.append(f"    {edge['from']}[\"{src_label}\"] --> {edge['to']}[\"{dst_label}\"]")
        return "\n".join(lines)


langgraph_workflow = LangGraphTacticalWorkflow()
