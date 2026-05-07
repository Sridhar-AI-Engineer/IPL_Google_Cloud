from .fan_decision_agent import FanDecisionAgent
from .historical_evaluator_agent import HistoricalEvaluatorAgent
from .simulator_agent import SimulatorAgent
from .scoring_agent import ScoringAgent

class AgenticPipeline:
    def __init__(self):
        self.fan_agent = FanDecisionAgent()
        self.hist_agent = HistoricalEvaluatorAgent()
        self.sim_agent = SimulatorAgent()
        self.score_agent = ScoringAgent()

    def evaluate_fan_decision(self, field_input, bowler_input, strategy_input, historical_move):
        fan_move = self.fan_agent.parse_input(field_input, bowler_input, strategy_input)
        hist_score = self.hist_agent.evaluate(fan_move, historical_move)
        sim_impact = self.sim_agent.simulate(fan_move)
        final_score = self.score_agent.calculate_score(hist_score, sim_impact)
        feedback = self.score_agent.generate_feedback(final_score, sim_impact)
        return {
            "score": final_score,
            "feedback": feedback,
            "historical_score": round(hist_score, 3),
            "simulation_impact": sim_impact,
            "normalized_move": fan_move,
        }