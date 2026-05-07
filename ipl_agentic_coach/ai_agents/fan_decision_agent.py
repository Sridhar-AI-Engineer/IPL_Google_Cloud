class FanDecisionAgent:
    """
    Converts raw fan input into structured tactical moves
    """
    def parse_input(self, field_input: str, bowler_input: str, strategy_input: str = ""):
        field = (field_input or "").strip().lower()
        bowler = (bowler_input or "").strip().lower()
        strategy = (strategy_input or "").strip().lower()

        style = "balanced"
        aggressive_signals = ["slip", "attacking", "wicket", "bouncer", "yorker"]
        defensive_signals = ["deep", "long on", "long off", "contain", "dot ball"]

        if any(token in f"{field} {bowler} {strategy}" for token in aggressive_signals):
            style = "aggressive"
        if any(token in f"{field} {bowler} {strategy}" for token in defensive_signals):
            style = "defensive"

        return {
            "field_placement": field,
            "bowler": bowler,
            "strategy": strategy,
            "style": style,
        }