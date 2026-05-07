from __future__ import annotations

import json
import os
from importlib import import_module
from typing import Any

from ipl_agentic_coach.ai_agents.agentic_pipeline import AgenticPipeline
from ipl_agentic_coach.backend.app.cricket_data_service import cricket_data_service


class TacticalAIService:
    def __init__(self) -> None:
        self._pipeline = AgenticPipeline()
        self._pipeline_mode = os.getenv("TACTICAL_PIPELINE_MODE", "auto").strip().lower()
        self._gemini_api_key = os.getenv("GEMINI_API_KEY", "").strip()
        self._gemini_model_name = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
        self._gemini_model = None
        self._langchain_pipeline = None
        self._langgraph_workflow = None

        self._load_optional_pipelines()
        genai = self._load_genai_module()

        if self._gemini_api_key and genai is not None:
            try:
                genai.configure(api_key=self._gemini_api_key)
                self._gemini_model = genai.GenerativeModel(self._gemini_model_name)
            except Exception:
                self._gemini_model = None

    def _load_optional_pipelines(self) -> None:
        try:
            from ipl_agentic_coach.ai_agents.langchain_pipeline import langchain_pipeline

            self._langchain_pipeline = langchain_pipeline
        except Exception:
            self._langchain_pipeline = None

        try:
            from ipl_agentic_coach.ai_agents.langgraph_workflow import langgraph_workflow

            self._langgraph_workflow = langgraph_workflow
        except Exception:
            self._langgraph_workflow = None

    def _load_genai_module(self):
        try:
            return import_module("google.generativeai")
        except Exception:
            return None

    @property
    def using_gemini(self) -> bool:
        return self._gemini_model is not None

    def evaluate_decision(
        self,
        field_input: str,
        bowler_input: str,
        strategy_input: str,
        historical_move: dict[str, Any],
    ) -> dict[str, Any]:
        if self._pipeline_mode == "langgraph" and self._langgraph_workflow is not None:
            result = self._langgraph_workflow.run(
                field_input,
                bowler_input,
                strategy_input,
                historical_move,
            )
            result["data_insights"] = "Evaluated via LangGraph workflow pipeline."
            return result

        if self._pipeline_mode == "langchain" and self._langchain_pipeline is not None:
            result = self._langchain_pipeline.evaluate(
                field_input,
                bowler_input,
                strategy_input,
                historical_move,
            )
            result["data_insights"] = "Evaluated via LangChain tool pipeline."
            return result

        if self._pipeline_mode == "local":
            return self._pipeline.evaluate_fan_decision(
                field_input,
                bowler_input,
                strategy_input,
                historical_move,
            )

        if self._gemini_model is None and self._pipeline_mode == "auto":
            if self._langgraph_workflow is not None:
                result = self._langgraph_workflow.run(
                    field_input,
                    bowler_input,
                    strategy_input,
                    historical_move,
                )
                result["data_insights"] = "Evaluated via LangGraph workflow pipeline."
                return result

            if self._langchain_pipeline is not None:
                result = self._langchain_pipeline.evaluate(
                    field_input,
                    bowler_input,
                    strategy_input,
                    historical_move,
                )
                result["data_insights"] = "Evaluated via LangChain tool pipeline."
                return result

            return self._pipeline.evaluate_fan_decision(
                field_input,
                bowler_input,
                strategy_input,
                historical_move,
            )

        prompt = self._build_prompt(field_input, bowler_input, strategy_input, historical_move)
        try:
            response = self._gemini_model.generate_content(prompt)
            raw_text = (response.text or "").strip()
            parsed = self._parse_json(raw_text)
            if parsed is None:
                raise ValueError("Gemini response was not valid JSON")
            return self._normalize_response(parsed, field_input, bowler_input, strategy_input)
        except Exception:
            if self._langgraph_workflow is not None:
                result = self._langgraph_workflow.run(
                    field_input,
                    bowler_input,
                    strategy_input,
                    historical_move,
                )
                result["data_insights"] = "Gemini unavailable; fallback to LangGraph workflow."
                return result

            if self._langchain_pipeline is not None:
                result = self._langchain_pipeline.evaluate(
                    field_input,
                    bowler_input,
                    strategy_input,
                    historical_move,
                )
                result["data_insights"] = "Gemini unavailable; fallback to LangChain pipeline."
                return result

            return self._pipeline.evaluate_fan_decision(
                field_input,
                bowler_input,
                strategy_input,
                historical_move,
            )

    def _build_prompt(
        self,
        field_input: str,
        bowler_input: str,
        strategy_input: str,
        historical_move: dict[str, Any],
    ) -> str:
        """Build data-driven prompt with real IPL statistics and cricket intelligence."""
        
        # Extract field positions from input
        field_positions = [pos.strip() for pos in field_input.split(",") if pos.strip()]
        
        # Get dynamic cricket data
        bowler_stats = cricket_data_service.get_bowler_stats(bowler_input)
        field_score = cricket_data_service.get_field_combination_score(field_positions, "death")
        tactical_insights = cricket_data_service.get_tactical_insights(
            bowler_input, field_positions, "death"
        )

        field_breakdown = []
        for position in field_positions:
            field_stats = cricket_data_service.get_field_effectiveness(position)
            if not field_stats:
                continue
            field_breakdown.append(
                {
                    "position": position,
                    "catch_probability": field_stats.get("catch_probability", 0.0),
                    "effectiveness_vs_pace": field_stats.get("effectiveness_vs_pace", 0.5),
                    "effectiveness_vs_spin": field_stats.get("effectiveness_vs_spin", 0.5),
                    "run_prevention": field_stats.get("run_prevention", 0.0),
                    "best_for": field_stats.get("best_for", []),
                    "placement_depth": field_stats.get("placement_depth", "close"),
                }
            )
        
        # Format phases for comprehensive analysis
        bowler_phases = {
            "powerplay": bowler_stats.get("vs_powerplay", {}),
            "middle": bowler_stats.get("vs_middle", {}),
            "death": bowler_stats.get("vs_death", {}),
        }
        
        return f"""
You are an IPL cricket tactical analyst with deep domain knowledge.

REAL IPL BOWLER STATISTICS FOR {bowler_input.upper()}:
- Overall Economy Rate: {bowler_stats.get('economy', 8.0)} runs/over
- Wickets per Match: {bowler_stats.get('wickets_per_match', 1.2)}
- Yorker Accuracy: {bowler_stats.get('yorker_accuracy', 0.6) * 100}%
- Dot Ball %: {bowler_stats.get('dot_ball_percentage', 0.37) * 100}%
- Strong Zones: {', '.join(bowler_stats.get('strong_zones', []))}
- Weak Zones: {', '.join(bowler_stats.get('weak_zones', []))}

PHASE-SPECIFIC PERFORMANCE:
- Powerplay: {bowler_phases['powerplay'].get('economy', 7.5)} econ, {bowler_phases['powerplay'].get('wickets', 1.0)} wkts
- Middle Overs: {bowler_phases['middle'].get('economy', 8.0)} econ, {bowler_phases['middle'].get('wickets', 1.3)} wkts
- Death Overs: {bowler_phases['death'].get('economy', 9.0)} econ, {bowler_phases['death'].get('wickets', 1.2)} wkts

FIELD PLACEMENT ANALYSIS:
- Selected Positions: {', '.join(field_positions) if field_positions else 'None'}
- Field Configuration Score: {field_score}/1.0
- Recommended Bowling Area: {tactical_insights.get('recommended_bowling_area', 'consistent lengths')}
- Position Effectiveness Breakdown: {json.dumps(field_breakdown, ensure_ascii=False)}

FAN TACTICAL STRATEGY:
"{strategy_input}"

HISTORICAL CONTEXT:
{json.dumps(historical_move, ensure_ascii=False)}

EVALUATION TASK:
Analyze this tactical decision based on:
1. Real IPL bowler performance data
2. Field positioning effectiveness
3. Phase-specific context (this is DEATH OVERS - high pressure)
4. Strategic coherence between bowler choice, field, and strategy

Return ONLY valid JSON with these EXACT keys:
{{
  "score": <float 0-1, reflecting how well this tactical combo exploits the bowler's strengths>,
  "feedback": "<1-2 sentence tactical assessment referencing real stats>",
  "historical_score": <float 0-1, comparison to successful historical moves>,
  "simulation_impact": {{
    "wicket_chance": <float 0-1, probability this field+bowler combo gets a wicket>,
    "runs_saved": <float 0-20, estimated runs prevented vs this field>
  }},
  "normalized_move": {{
    "field_placement": "{field_input}",
    "bowler": "{bowler_input}",
    "strategy": "{strategy_input}"
  }},
  "data_insights": "<Brief analysis of how real stats informed this scoring>"
}}

Rules:
- Use REAL stats: {bowler_input}'s economy is {bowler_stats.get('economy', 8.0)}, not generic 8.0
- Reward field placements that combat bowler's WEAK ZONES
- Consider death-over context: economy rate {bowler_phases['death'].get('economy', 9.0)} is critical
- Score reflects tactical execution probability given real data
- Feedback must reference actual statistics
""".strip()

    def _parse_json(self, raw_text: str) -> dict[str, Any] | None:
        if not raw_text:
            return None

        try:
            return json.loads(raw_text)
        except Exception:
            pass

        start = raw_text.find("{")
        end = raw_text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            return None

        candidate = raw_text[start : end + 1]
        try:
            return json.loads(candidate)
        except Exception:
            return None

    def _normalize_response(
        self,
        parsed: dict[str, Any],
        field_input: str,
        bowler_input: str,
        strategy_input: str,
    ) -> dict[str, Any]:
        score = float(parsed.get("score", 0.5))
        historical_score = float(parsed.get("historical_score", score))
        score = max(0.0, min(1.0, score))
        historical_score = max(0.0, min(1.0, historical_score))

        simulation = parsed.get("simulation_impact") or {}
        wicket_chance = float(simulation.get("wicket_chance", 0.25))
        runs_saved = float(simulation.get("runs_saved", 3.0))
        simulation_impact = {
            "wicket_chance": max(0.0, min(1.0, wicket_chance)),
            "runs_saved": max(0.0, min(20.0, runs_saved)),
        }

        normalized = parsed.get("normalized_move") or {}
        normalized_move = {
            "field_placement": str(normalized.get("field_placement", field_input)),
            "bowler": str(normalized.get("bowler", bowler_input)),
            "strategy": str(normalized.get("strategy", strategy_input)),
        }

        feedback = str(parsed.get("feedback", "Balanced tactical call with room to optimize field pressure."))
        data_insights = str(parsed.get("data_insights", "Analysis based on real IPL statistics."))

        return {
            "score": round(score, 4),
            "feedback": feedback,
            "historical_score": round(historical_score, 4),
            "simulation_impact": simulation_impact,
            "normalized_move": normalized_move,
            "data_insights": data_insights,
        }


tactical_ai_service = TacticalAIService()
