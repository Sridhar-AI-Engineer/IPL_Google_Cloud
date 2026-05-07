class ScoringAgent:
    """
    Combines historical evaluation + simulation to produce final score
    """
    def calculate_score(self, historical_score: float, simulation_impact: dict):
        runs_component = min(simulation_impact.get("runs_saved", 0.0) / 2.0, 1.0)
        wicket_component = simulation_impact.get("wicket_chance", 0.0)
        pressure_component = simulation_impact.get("pressure_index", 0.0)

        total = (
            (historical_score * 0.45)
            + (runs_component * 0.25)
            + (wicket_component * 0.2)
            + (pressure_component * 0.1)
        )
        return round(min(max(total, 0.0), 1.0), 3)

    def generate_feedback(self, score: float, simulation_impact: dict):
        wicket_chance = int(simulation_impact.get("wicket_chance", 0.0) * 100)
        runs_saved = simulation_impact.get("runs_saved", 0.0)

        if score >= 0.8:
            return (
                f"Excellent tactical choice. Predicted pressure is high with around {wicket_chance}% "
                f"wicket chance and about {runs_saved} runs controlled over the next mini-phase."
            )

        if score >= 0.6:
            return (
                f"Good decision with balanced control. Expected wicket chance is {wicket_chance}% "
                f"and projected run containment is {runs_saved}."
            )

        return (
            f"Tactical move is risky for this phase. Predicted wicket chance is only {wicket_chance}% "
            f"with limited run control ({runs_saved})."
        )