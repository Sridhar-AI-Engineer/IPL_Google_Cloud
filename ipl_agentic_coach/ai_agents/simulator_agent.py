class SimulatorAgent:
    """
    Simple predictive simulation for next few balls
    """
    def simulate(self, fan_move: dict):
        style = fan_move.get("style", "balanced")
        bowler = fan_move.get("bowler", "")

        runs_saved = 1.0
        wicket_chance = 0.25
        pressure_index = 0.5

        if style == "aggressive":
            runs_saved = 0.8
            wicket_chance = 0.42
            pressure_index = 0.72
        elif style == "defensive":
            runs_saved = 1.6
            wicket_chance = 0.22
            pressure_index = 0.64

        if "spinner" in bowler:
            runs_saved += 0.2
            wicket_chance += 0.03
        if "yorker" in bowler or "fast" in bowler:
            wicket_chance += 0.05
            pressure_index += 0.04

        impact = {
            "runs_saved": round(max(0.0, runs_saved), 2),
            "wicket_chance": round(min(max(wicket_chance, 0.0), 1.0), 2),
            "pressure_index": round(min(max(pressure_index, 0.0), 1.0), 2),
        }
        return impact