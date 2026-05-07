
# **Problem Statement: IPL Coaching Simulator with Agentic AI**

### **Context**

In cricket, especially in the Indian Premier League (IPL), **the captain’s tactical decisions**—like **field placements, bowling changes, and batting order**—have a huge impact on match outcomes. Traditionally, these decisions are made by the team captain using:

* Match situation awareness
* Player statistics
* Historical trends
* Intuition & experience

Fans watching live IPL matches often **debate or suggest tactical decisions**, but there is **no platform to test their cricketing IQ in real-time**.

---

### **The Problem**

Create an **interactive platform** where:

1. **Fans make tactical decisions in real-time** during IPL matches (field placements, bowling changes, etc.).
2. Their decisions are **compared against the actual captain’s moves** and against historical data to evaluate **tactical merit**.
3. **AI agents analyze these decisions**:

   * Are they optimal given the situation?
   * Would they save runs or increase wickets?
   * How do they compare historically?
4. Fans are **scored, ranked, and given feedback**—like a cricket tactical simulator.

---

### **Challenges**

1. **Real-time decision processing**

   * Fan inputs must be captured and evaluated immediately.
   * Leaderboards and AI feedback should update dynamically.

2. **Tactical merit evaluation**

   * Comparing fan moves with the captain isn’t enough.
   * Decisions must be evaluated using **historical scenarios and simulation predictions**.

3. **AI orchestration (Agentic AI)**

   * Fan inputs → structured tactical moves
   * Historical evaluation → scoring vs past matches
   * Simulation → predicting runs/wickets impact
   * Feedback generation → AI reasoning in natural language

4. **Scalable architecture**

   * Must support multiple fans simultaneously
   * Must integrate frontend, backend, database, and AI modules seamlessly

5. **Resource constraints (Optional)**

   * Can’t use heavy cloud resources (like GPUs) for simulation
   * Must work **locally** or with **small cloud credits** ($5 GCP trial)

---

### **Expected Outputs**

1. **Fan Decision Score**

   * A numerical score reflecting tactical quality
2. **AI Feedback**

   * Natural language explanation of reasoning behind score
3. **Leaderboard**

   * Top-performing fans ranked by cumulative tactical IQ
4. **Visual Insights**

   * Graphs showing predicted impact of fan decisions vs captain decisions
5. **Agentic AI Demonstration**

   * Modular AI agents orchestrating the evaluation process
   * LangChain + LangGraph visualization of reasoning flow

---

### **Why This is Hard**

* Cricket strategy is **complex, dynamic, and context-dependent**.
* Decisions are **multi-factorial**:

  * Field placement vs batsman type
  * Bowler choice vs pitch condition
  * Game situation (overs remaining, runs required)
* Combining **historical data, simulations, and real-time fan input** in a scoring system is **non-trivial**.
* Making the AI reasoning **transparent and explainable** adds an extra layer of sophistication.

---

### **Why This is a Great Project**

1. Demonstrates **real-time system design**
2. Showcases **agentic AI orchestration skills** (LangChain + LangGraph)
3. Uses **full-stack development skills** (FastAPI + frontend + SQLite)
4. Presents **data-driven decision-making**
5. Can be scaled or enhanced with **predictive analytics, opponent modeling, or weather/pitch agents**

---

💡 **In short:**

> You are building a **real-time cricket tactical simulator** where fans act as captains. An **Agentic AI pipeline evaluates their decisions** against historical data, captain moves, and predictive simulations, provides **scoring and AI feedback**, and maintains **dynamic leaderboards**—all while being lightweight enough to run locally or on a $5 GCP budget.

