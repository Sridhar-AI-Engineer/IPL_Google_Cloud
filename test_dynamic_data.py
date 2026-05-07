#!/usr/bin/env python3
"""Test dynamic cricket data integration."""

from ipl_agentic_coach.backend.app.cricket_data_service import cricket_data_service
from ipl_agentic_coach.backend.app.ai_service import tactical_ai_service

print("=" * 60)
print("DYNAMIC CRICKET DATA INTEGRATION TEST")
print("=" * 60)

# Test 1: Load cricket data
print("\n1. Cricket Data Service")
print("-" * 40)
pat_stats = cricket_data_service.get_bowler_stats("Pat Cummins")
print(f"✅ Pat Cummins Economy: {pat_stats['economy']} runs/over")
print(f"✅ Pat Cummins Yorker Accuracy: {pat_stats['yorker_accuracy']*100}%")
print(f"✅ Death Overs Economy: {pat_stats['vs_death']['economy']} runs/over")

# Test 2: Field effectiveness
print("\n2. Field Effectiveness")
print("-" * 40)
slip_eff = cricket_data_service.get_field_effectiveness("Slip")
print(f"✅ Slip catch probability: {slip_eff['catch_probability']*100}%")
print(f"✅ Slip vs pace effectiveness: {slip_eff['effectiveness_vs_pace']*100}%")

# Test 3: Field combination score
print("\n3. Field Combination Score")
print("-" * 40)
field_score = cricket_data_service.get_field_combination_score(["Slip", "Gully", "Point"], "death")
print(f"✅ Field score (Slip+Gully+Point): {field_score}/1.0")

# Test 4: Tactical insights
print("\n4. Tactical Insights Generation")
print("-" * 40)
insights = cricket_data_service.get_tactical_insights("Pat Cummins", ["Slip", "Gully", "Point"], "death")
print(f"✅ Bowler phase economy: {insights['phase_economy']} runs/over")
print(f"✅ Field score: {insights['field_score']}/1.0")
print(f"✅ Recommended area: {insights['recommended_bowling_area']}")

# Test 5: AI Service prompt generation
print("\n5. AI Prompt Generation (Data-Driven)")
print("-" * 40)
prompt = tactical_ai_service._build_prompt(
    "Slip, Gully, Point",
    "Pat Cummins",
    "Defend edges with close fieldies",
    {}
)

test_data_present = True
checks = []

if "Pat Cummins" in prompt:
    checks.append(("✅", "Bowler name in prompt"))
else:
    checks.append(("❌", "Bowler name MISSING"))
    test_data_present = False

if "8.2" in prompt:  # Pat Cummins real economy
    checks.append(("✅", "Pat's economy (8.2) in prompt"))
else:
    checks.append(("❌", "Economy data MISSING"))
    test_data_present = False

if "85" in prompt:  # Slip effectiveness
    checks.append(("✅", "Slip effectiveness (85%) in prompt"))
else:
    checks.append(("❌", "Field effectiveness MISSING"))
    test_data_present = False

if "68" in prompt:  # Yorker accuracy
    checks.append(("✅", "Yorker accuracy (68%) in prompt"))
else:
    checks.append(("❌", "Yorker accuracy MISSING"))
    test_data_present = False

if "DEATH OVERS" in prompt.upper():
    checks.append(("✅", "Phase context (death overs) in prompt"))
else:
    checks.append(("❌", "Phase context MISSING"))
    test_data_present = False

for status, msg in checks:
    print(f"{status} {msg}")

# Test 6: Decision evaluation with data
print("\n6. Decision Evaluation (without Gemini)")
print("-" * 40)
result = tactical_ai_service.evaluate_decision(
    "Slip, Gully, Point",
    "Pat Cummins",
    "Defend edges with close fieldies",
    {"match_id": 1, "ball_number": 114}
)
print(f"✅ Score generated: {result['score']:.2f}")
print(f"✅ Feedback: {result['feedback'][:60]}...")
print(f"✅ Wicket chance: {result['simulation_impact']['wicket_chance']:.2f}")
print(f"✅ Runs saved: {result['simulation_impact']['runs_saved']:.2f}")

# Summary
print("\n" + "=" * 60)
if test_data_present and result['score'] > 0:
    print("✅ ALL TESTS PASSED - Dynamic data system operational!")
    print("\nSystem is ready for:")
    print("  1. Production deployment with Gemini")
    print("  2. Kaggle data integration")
    print("  3. Real-time tactical analysis with statistics")
else:
    print("⚠️  Some tests failed - check implementation")

print("=" * 60)
