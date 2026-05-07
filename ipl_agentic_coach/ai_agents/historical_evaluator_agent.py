class HistoricalEvaluatorAgent:
    """
    Evaluates fan decision against historical decisions
    """
    def evaluate(self, fan_move: dict, historical_move: dict):
        score = 0.0

        historical_field = (historical_move.get("field_placement") or "").lower()
        historical_bowler = (historical_move.get("bowler") or "").lower()
        expected_score = float(historical_move.get("expected_score") or 0.6)

        fan_field_tokens = set(fan_move.get("field_placement", "").split())
        historical_field_tokens = set(historical_field.split())
        field_overlap = fan_field_tokens.intersection(historical_field_tokens)

        if fan_move.get("field_placement") == historical_field:
            score += 0.45
        elif field_overlap:
            score += 0.25

        fan_bowler = fan_move.get("bowler", "")
        if fan_bowler == historical_bowler:
            score += 0.4
        elif any(token in fan_bowler for token in historical_bowler.split()):
            score += 0.2

        score += max(0.0, min(expected_score, 1.0)) * 0.15
        return max(0.0, min(score, 1.0))