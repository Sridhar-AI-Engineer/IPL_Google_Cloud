"""
LangChain-powered Agentic Pipeline
===================================
Wraps the IPL tactical decision workflow using LangChain Tools and SequentialChain.
Falls back gracefully to the local agentic pipeline if LangChain / Gemini not available.
"""

from __future__ import annotations

import json
import os
from importlib import import_module
from typing import Any

from .fan_decision_agent import FanDecisionAgent
from .historical_evaluator_agent import HistoricalEvaluatorAgent
from .simulator_agent import SimulatorAgent
from .scoring_agent import ScoringAgent


def _load_langchain():
    """Dynamically import LangChain core modules."""
    try:
        lc_core = import_module("langchain_core.tools")
        lc_chains = import_module("langchain.chains")
        return lc_core, lc_chains
    except Exception:
        return None, None


def _load_langchain_gemini():
    """Dynamically import LangChain Google Gemini integration."""
    try:
        return import_module("langchain_google_genai")
    except Exception:
        return None


# ── LangChain Tool Definitions ─────────────────────────────────────────────────

def _make_tools():
    """Return LangChain StructuredTools wrapping each agent."""
    lc_core, _ = _load_langchain()
    if lc_core is None:
        return None

    StructuredTool = getattr(lc_core, "StructuredTool", None)
    if StructuredTool is None:
        return None

    fan_agent = FanDecisionAgent()
    hist_agent = HistoricalEvaluatorAgent()
    sim_agent = SimulatorAgent()
    score_agent = ScoringAgent()

    def parse_fan_input(field_input: str, bowler_input: str, strategy_input: str = "") -> str:
        """Parse raw fan inputs into a structured tactical move dict."""
        move = fan_agent.parse_input(field_input, bowler_input, strategy_input)
        return json.dumps(move)

    def evaluate_historical(fan_move_json: str, historical_move_json: str) -> str:
        """Compare fan decision against historical IPL captain moves. Returns score 0-1."""
        fan_move = json.loads(fan_move_json)
        historical_move = json.loads(historical_move_json)
        score = hist_agent.evaluate(fan_move, historical_move)
        return json.dumps({"historical_score": score})

    def simulate_impact(fan_move_json: str) -> str:
        """Simulate match impact of the tactical decision (runs, wicket chance, pressure)."""
        fan_move = json.loads(fan_move_json)
        impact = sim_agent.simulate(fan_move)
        return json.dumps(impact)

    def calculate_final_score(historical_score: float, simulation_json: str) -> str:
        """Combine historical score and simulation into final tactical score + feedback."""
        simulation = json.loads(simulation_json)
        final = score_agent.calculate_score(historical_score, simulation)
        feedback = score_agent.generate_feedback(final, simulation)
        return json.dumps({"score": final, "feedback": feedback})

    tools = [
        StructuredTool.from_function(parse_fan_input, name="ParseFanInput",
            description="Parse raw fan inputs into structured tactical move."),
        StructuredTool.from_function(evaluate_historical, name="EvaluateHistorical",
            description="Evaluate fan decision against historical captain moves."),
        StructuredTool.from_function(simulate_impact, name="SimulateImpact",
            description="Simulate the match impact of a tactical decision."),
        StructuredTool.from_function(calculate_final_score, name="CalculateFinalScore",
            description="Calculate combined tactical score and generate AI feedback."),
    ]
    return tools


# ── LangChain LLM Setup ────────────────────────────────────────────────────────

def _make_llm():
    """Create Gemini LLM via LangChain Google GenAI integration."""
    genai_lc = _load_langchain_gemini()
    if genai_lc is None:
        return None

    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        return None

    try:
        ChatGoogleGenerativeAI = getattr(genai_lc, "ChatGoogleGenerativeAI")
        model_name = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
        return ChatGoogleGenerativeAI(
            model=model_name,
            google_api_key=api_key,
            temperature=0.3,
        )
    except Exception:
        return None


# ── LangChain Pipeline Class ───────────────────────────────────────────────────

class LangChainTacticalPipeline:
    """
    Orchestrates IPL tactical decision evaluation using LangChain tools.

    Pipeline flow:
        FanDecisionAgent ──► HistoricalEvaluatorAgent ──► SimulatorAgent ──► ScoringAgent
                     (all wrapped as LangChain StructuredTools)
    """

    def __init__(self):
        self._fan_agent = FanDecisionAgent()
        self._hist_agent = HistoricalEvaluatorAgent()
        self._sim_agent = SimulatorAgent()
        self._score_agent = ScoringAgent()

        self._llm = _make_llm()
        self._tools = _make_tools()
        self._langchain_available = self._tools is not None

    @property
    def using_langchain(self) -> bool:
        return self._langchain_available

    @property
    def using_llm(self) -> bool:
        return self._llm is not None

    def evaluate(
        self,
        field_input: str,
        bowler_input: str,
        strategy_input: str,
        historical_move: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Main evaluation entry point.
        Uses LangChain tool chain if available, else runs identical local logic.
        """
        if self._langchain_available:
            return self._run_langchain_pipeline(
                field_input, bowler_input, strategy_input, historical_move
            )
        return self._run_local_pipeline(
            field_input, bowler_input, strategy_input, historical_move
        )

    def _run_langchain_pipeline(
        self,
        field_input: str,
        bowler_input: str,
        strategy_input: str,
        historical_move: dict[str, Any],
    ) -> dict[str, Any]:
        """Execute sequential LangChain tool calls for the full pipeline."""
        try:
            # Step 1: Parse fan input
            fan_move = self._fan_agent.parse_input(field_input, bowler_input, strategy_input)
            fan_move_json = json.dumps(fan_move)

            # Step 2: Historical evaluation
            hist_result_json = self._tools[1].func(
                fan_move_json=fan_move_json,
                historical_move_json=json.dumps(historical_move),
            )
            hist_result = json.loads(hist_result_json)
            historical_score = hist_result["historical_score"]

            # Step 3: Simulate impact
            sim_result_json = self._tools[2].func(fan_move_json=fan_move_json)
            simulation_impact = json.loads(sim_result_json)

            # Step 4: Calculate final score
            final_json = self._tools[3].func(
                historical_score=historical_score,
                simulation_json=json.dumps(simulation_impact),
            )
            final = json.loads(final_json)

            return {
                "score": final["score"],
                "feedback": final["feedback"],
                "historical_score": round(historical_score, 3),
                "simulation_impact": simulation_impact,
                "normalized_move": fan_move,
                "pipeline": "langchain",
            }
        except Exception:
            return self._run_local_pipeline(
                field_input, bowler_input, strategy_input, historical_move
            )

    def _run_local_pipeline(
        self,
        field_input: str,
        bowler_input: str,
        strategy_input: str,
        historical_move: dict[str, Any],
    ) -> dict[str, Any]:
        """Fallback: run pure Python agents directly."""
        fan_move = self._fan_agent.parse_input(field_input, bowler_input, strategy_input)
        hist_score = self._hist_agent.evaluate(fan_move, historical_move)
        sim_impact = self._sim_agent.simulate(fan_move)
        final_score = self._score_agent.calculate_score(hist_score, sim_impact)
        feedback = self._score_agent.generate_feedback(final_score, sim_impact)
        return {
            "score": final_score,
            "feedback": feedback,
            "historical_score": round(hist_score, 3),
            "simulation_impact": sim_impact,
            "normalized_move": fan_move,
            "pipeline": "local",
        }

    def describe_tools(self) -> list[dict[str, str]]:
        """Return a list of registered LangChain tool descriptions."""
        if not self._tools:
            return []
        return [{"name": t.name, "description": t.description} for t in self._tools]


langchain_pipeline = LangChainTacticalPipeline()
