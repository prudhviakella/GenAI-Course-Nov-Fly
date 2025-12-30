# Self-Consistency Prompting - Complete Guide

## What is Self-Consistency Prompting?

Self-Consistency prompting generates multiple independent reasoning paths for the same problem, then selects the answer that appears most frequently. It's like getting second and third opinions before making a critical decision.

### Think of it like this:

**Regular Approach:**
```
Problem → Single reasoning path → Answer
```
You get one answer, but what if the reasoning was flawed?

**Self-Consistency Approach:**
```
Problem → Reasoning Path 1 → Answer A
       → Reasoning Path 2 → Answer A
       → Reasoning Path 3 → Answer A
       → Most common: Answer A (HIGH confidence)
```

Or:
```
Problem → Reasoning Path 1 → Answer A
       → Reasoning Path 2 → Answer B
       → Reasoning Path 3 → Answer A
       → Most common: Answer A (MEDIUM confidence)
```

---

## Why Use Self-Consistency?

### Benefits:

1. **Higher Accuracy** - Multiple paths catch errors in single reasoning
2. **Confidence Measurement** - Agreement level shows how certain we are
3. **Error Detection** - Disagreement reveals problematic questions
4. **Reduces Bias** - One reasoning path might be biased, multiple average out
5. **Critical Decisions** - Essential when stakes are high

### When to Use Self-Consistency:

✓ **Use when:**
- Decision is high-stakes (medical, financial, legal)
- Need high confidence in answer
- Problem has ambiguity or uncertainty
- Multiple valid approaches exist
- Error cost is high

✗ **Don't use when:**
- Simple, straightforward problems
- Speed is critical
- Answer is objectively verifiable (like 2+2=4)
- Resources are limited (multiple generations cost more)

---

## How It Works

### The Process:

1. **Generate Multiple Paths**: Same problem, different reasoning approaches
2. **Independent Thinking**: Each path doesn't see the others
3. **Tally Results**: Count how many paths reach same conclusion
4. **Select Majority**: Most common answer wins
5. **Assess Confidence**: Agreement level = confidence level

### Confidence Levels:

```
3/3 paths agree (100%) = VERY HIGH confidence
2/3 paths agree (67%)  = MEDIUM confidence  
1/3 unique answers (33%) = LOW confidence - need more analysis
```

---

## Example 1: E-Commerce - Fraud Detection Decision

### Business Problem:
Determine if a high-value order ($4,500) is legitimate or fraudulent. Wrong decision costs money either way.

### Why Self-Consistency Helps:
- Missing fraud = $4,500 loss
- Blocking legitimate order = Lost customer + reputation damage
- Ambiguous signals (some red flags, some green flags)
- Need high confidence before deciding

### COSTAR Prompt:

```
Context: E-commerce fraud detection where we must decide whether to approve 
or decline a $4,500 order with mixed signals.

Objective: Determine if order is legitimate or fraudulent with high confidence 
by generating multiple independent reasoning paths.

Style: Generate 3 completely independent reasoning paths, each using a different 
analytical framework. Each path should analyze the same data but approach it 
from a different perspective without seeing the other paths' conclusions.

Tone: Investigative and thorough, like 3 different fraud analysts independently 
reviewing the same case.

Audience: Risk management team making approval decisions.

Response Format: 
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
REASONING PATH 1: [Methodology Name]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[Complete independent analysis]
[Show all reasoning steps]
[Reach conclusion]

PATH 1 CONCLUSION: [APPROVE or DECLINE]
Confidence: [High/Medium/Low]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
REASONING PATH 2: [Different Methodology Name]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[Complete independent analysis using different approach]
[Show all reasoning steps]
[Reach conclusion]

PATH 2 CONCLUSION: [APPROVE or DECLINE]
Confidence: [High/Medium/Low]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
REASONING PATH 3: [Third Different Methodology Name]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[Complete independent analysis using third approach]
[Show all reasoning steps]
[Reach conclusion]

PATH 3 CONCLUSION: [APPROVE or DECLINE]
Confidence: [High/Medium/Low]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SELF-CONSISTENCY RESULTS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Tally Results:
PATH 1: [Decision] ([Confidence])
PATH 2: [Decision] ([Confidence])
PATH 3: [Decision] ([Confidence])

Agreement: [X/3 paths] ([percentage]%)

Most Consistent Conclusion: [Final Decision]

Overall Confidence Level: [VERY HIGH/HIGH/MEDIUM/LOW]

Rationale for Confidence:
[Explain why this confidence level based on agreement]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FINAL RECOMMENDATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Decision: [APPROVE or DECLINE] Order #87453

Rationale:
[Summary of why this decision based on consensus]

Action Items:
1. [Specific action]
2. [Specific action]
3. [Specific action]

---

ORDER DETAILS FOR ANALYSIS:

Customer Profile:
- Account age: 3 days (NEW)
- Email: john.smith.2024@tempmail.com (temporary email service)
- IP address: Chicago, IL
- Phone: 312 area code (matches Chicago)
- Customer answered phone when we called: YES

Order Details:
- Item: MacBook Pro 16" ($2,499) × 1
- Item: iPhone 15 Pro Max ($1,199) × 1  
- Item: AirPods Pro ($249) × 1
- Item: Apple Watch Ultra ($799) × 1
- Total: $4,746
- Shipping: Express (2-day) to Chicago residential address
- Payment: Credit card (passed AVS check - Address Verification System)

Red Flags:
- New account (3 days old)
- Temporary email address (tempmail.com)
- High-value electronics order
- Multiple Apple products (high resale value)
- Express shipping (fraudsters want items fast)

Green Flags:
- IP and shipping address match (both Chicago)
- Phone area code matches location
- Credit card passed AVS (Address Verification System)
- Customer answered phone when we called
- Shipping to residential address (not business/freight forwarder)
- Not using multiple credit cards
- Order placed during normal hours (2pm, not 3am)

Historical Context:
- 87% of orders matching "new account + temp email + high-value electronics + express ship" 
  pattern were fraud in our data
- However, 13% were legitimate (privacy-conscious customers do use temp emails)
- Average fraud loss per incident: $4,500
- Average cost of declining legitimate customer: $712 profit + $2,000 LTV = $2,712

Generate 3 independent reasoning paths using these different methodologies:
Path 1: Risk-Weighted Scoring Approach
Path 2: Pattern Recognition & Historical Data Approach  
Path 3: Cost-Benefit Analysis & Expected Value Approach

Each path must:
1. Analyze the data independently
2. Use its specific methodology
3. Reach a conclusion (APPROVE or DECLINE)
4. State confidence level
5. NOT reference other paths
```

---

## Example 2: Healthcare - Clinical Diagnostic Decision

### Medical Problem:
Patient with severe acute headache. Multiple possible diagnoses. Wrong diagnosis could be fatal.

### Why Self-Consistency is CRITICAL:

⚠️ **LIFE-THREATENING DIAGNOSTIC UNCERTAINTY** ⚠️
- Missing SAH (subarachnoid hemorrhage) = patient dies
- Over-diagnosing SAH = unnecessary invasive testing
- Multiple reasoning paths prevent cognitive bias
- Confirmation of diagnosis increases safety

### COSTAR Prompt:

```
Context: Emergency department diagnostic decision-making where a patient presents 
with severe acute headache and multiple diagnostic possibilities exist. We need 
very high confidence before ordering invasive testing or sending patient home.

Objective: Arrive at the most likely diagnosis by generating multiple independent 
reasoning paths and selecting the most consistent conclusion. This is a 
life-or-death decision requiring careful analysis.

Style: Reason like 3 different emergency physicians independently evaluating 
the same patient. Each physician uses a different diagnostic framework but 
reviews the same clinical data. They cannot see each other's conclusions.

Tone: Methodical and evidence-based, showing clinical reasoning. Each path 
must be thorough and consider life-threatening diagnoses first.

Audience: Healthcare team in emergency department case conference.

Response Format:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
REASONING PATH 1: [Diagnostic Methodology Name]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Approach: [Explain the diagnostic framework being used]

[Complete independent clinical reasoning]
[Systematic evaluation of symptoms]
[Consider differential diagnoses]
[Apply diagnostic criteria]
[Reach conclusion]

PATH 1 CONCLUSION: [Primary Diagnosis]
Confidence: [Very High/High/Medium/Low]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
REASONING PATH 2: [Different Diagnostic Methodology]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Approach: [Explain different diagnostic framework]

[Complete independent clinical reasoning using different method]
[Systematic evaluation from different perspective]
[Calculate probabilities or apply different criteria]
[Reach conclusion]

PATH 2 CONCLUSION: [Primary Diagnosis]
Confidence: [Very High/High/Medium/Low]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
REASONING PATH 3: [Third Diagnostic Methodology]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Approach: [Explain third diagnostic framework]

[Complete independent clinical reasoning using third method]
[Systematic differential diagnosis]
[Rule out/rule in process]
[Reach conclusion]

PATH 3 CONCLUSION: [Primary Diagnosis]
Confidence: [Very High/High/Medium/Low]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SELF-CONSISTENCY RESULTS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Tally Results:
PATH 1 ([Methodology]): [Diagnosis] - [Confidence]
PATH 2 ([Methodology]): [Diagnosis] - [Confidence]
PATH 3 ([Methodology]): [Diagnosis] - [Confidence]

Agreement: [X/3 paths] ([percentage]%)

Most Consistent Conclusion: [Final Diagnosis]

Overall Confidence Level: [VERY HIGH/HIGH/MEDIUM/LOW]

Clinical Significance of Agreement:
[Explain what this level of agreement means for patient safety]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FINAL CLINICAL DECISION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Working Diagnosis: [Final Diagnosis]

Diagnostic Confidence: [Level]

Rationale:
[Why all 3 methods agreed/disagreed]
[Clinical implications]

⚠️ IMMEDIATE ACTIONS (Priority Order):

1. [First critical action]
2. [Second critical action]  
3. [Third critical action]
[Continue with full action plan]

IF [condition]:
[Contingency plan]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CRITICAL TEACHING POINTS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. [Key lesson from self-consistency analysis]
2. [Safety implication]
3. [Clinical pearl]

---

PATIENT PRESENTATION FOR ANALYSIS:

Demographics & Vital Signs:
- 45-year-old male, no significant past medical history
- BP: 165/95 mmHg (baseline usually 130/80)
- Heart Rate: 88 bpm (regular)
- Temperature: 98.6°F (37°C) - afebrile
- Respiratory Rate: 16 breaths/min
- O2 Saturation: 98% on room air
- Alert and oriented × 3 (person, place, time)
- Glasgow Coma Scale: 15/15 (fully alert)

Chief Complaint:
- "This is the worst headache of my life"
- Onset: 2 hours ago
- Character: Started suddenly, reached maximum intensity within seconds
- Patient description: "Like someone hit me in the head with a baseball bat"
- Pain location: Diffuse, worst in back of head
- Pain severity: 10/10

Associated Symptoms:
- Nausea: Present (vomited once)
- Photophobia: Yes (light sensitivity)
- Phonophobia: Mild (sound sensitivity)
- Neck stiffness: Mild nuchal rigidity on exam
- Vision changes: None
- Speech changes: None
- Weakness: None
- Loss of consciousness: None

Physical Examination:
- General: Appears uncomfortable, holding head
- HEENT: Pupils equal, round, reactive to light (3mm → 2mm)
- Neck: Mild resistance to passive flexion (nuchal rigidity)
- Neurological:
  * Cranial nerves II-XII: Intact
  * Motor: 5/5 strength all extremities
  * Sensory: Intact to light touch and pinprick
  * Reflexes: 2+ symmetric throughout
  * Coordination: Finger-to-nose intact
  * Gait: Not tested (patient in severe pain)
  * No focal neurological deficits identified

History:
- No head trauma
- No prior history of migraines or severe headaches
- No recent illness or fever
- No recent medications started
- No family history of aneurysms or SAH
- Non-smoker
- Social alcohol use only
- No illicit drug use

Timeline:
- 2 hours ago: Sudden onset while at work (sitting at desk)
- 1.5 hours ago: Went home, headache not improving
- 1 hour ago: Vomited once
- 30 minutes ago: Wife drove him to ED
- Currently: Pain unchanged, 10/10 severity

Generate 3 independent diagnostic reasoning paths using these methodologies:
Path 1: Classic Clinical Pattern Recognition Approach
Path 2: Bayesian Probability & Likelihood Ratio Approach
Path 3: Systematic Differential Diagnosis with Exclusion Criteria

Each path must:
1. Independently analyze all clinical data
2. Use its specific diagnostic methodology  
3. Consider life-threatening causes FIRST
4. Reach a working diagnosis
5. State confidence level based on that methodology
6. NOT reference conclusions from other paths
```

---

## What Students Should Learn

### Key Concepts:

1. **Independent Reasoning**: Each path must think independently - no peeking at other paths
2. **Different Methodologies**: Use genuinely different analytical approaches
3. **Majority Vote**: Most common answer wins
4. **Confidence from Agreement**: 3/3 = very high, 2/3 = medium, 1/3 = low
5. **Multiple Perspectives**: Same data, different analytical lenses reveal truth

### Why the Detailed COSTAR Prompts Matter:

**In the E-Commerce Example:**
- Path 1 uses risk scoring with weighted points
- Path 2 uses pattern matching against historical fraud data
- Path 3 uses economic cost-benefit expected value analysis
- **All analyze same data, reach same conclusion through different methods**
- Agreement = High confidence in decision

**In the Healthcare Example:**
- Path 1 uses pattern recognition (textbook presentations)
- Path 2 uses Bayesian probability (likelihood ratios)
- Path 3 uses differential diagnosis (systematic exclusion)
- **All analyze same patient, reach same diagnosis through different frameworks**
- Agreement = Safe to proceed with treatment

### Critical Difference from Simple Prompting:

**Simple Prompt (BAD):**
```
Is this order fraud? Analyze and decide.
```
→ One analysis, one answer, unknown reliability

**Self-Consistency Prompt (GOOD):**
```
Generate 3 independent analyses using:
1. Risk scoring method
2. Pattern matching method
3. Cost-benefit method

Each path reaches conclusion independently.
Tally results to find most consistent answer.
```
→ Three analyses, consensus answer, measured confidence

---

## How to Write Effective Self-Consistency Prompts

### Template Structure:

```
Context: [Why self-consistency is needed for this decision]

Objective: [What you need to determine with high confidence]

Style: Generate [N] completely independent reasoning paths, each using 
a different analytical framework. Each path analyzes the same data but 
approaches it from a different perspective without seeing other paths.

Tone: [Appropriate for domain - investigative, clinical, analytical]

Audience: [Decision makers who need confidence measurement]

Response Format:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
REASONING PATH 1: [Specific Methodology Name]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Approach: [Framework description]
[Independent analysis]
PATH 1 CONCLUSION: [Answer]
Confidence: [Level]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
REASONING PATH 2: [Different Methodology]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Approach: [Different framework]
[Independent analysis]
PATH 2 CONCLUSION: [Answer]
Confidence: [Level]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
REASONING PATH 3: [Third Methodology]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Approach: [Third framework]
[Independent analysis]
PATH 3 CONCLUSION: [Answer]
Confidence: [Level]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SELF-CONSISTENCY RESULTS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Agreement: [X/N paths] ([%]%)
Most Consistent: [Final Answer]
Overall Confidence: [Level]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FINAL DECISION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Decision: [Final Answer]
Actions: [What to do]

---

[All data for analysis]

Generate [N] independent paths using these methodologies:
Path 1: [Specific method name]
Path 2: [Different method name]
Path 3: [Third method name]

Each path must:
1. [Requirement]
2. [Requirement]
3. NOT reference other paths
```

### Critical Elements:

1. **Specify Methodologies**: Name the exact analytical frameworks to use
2. **Demand Independence**: Explicitly state paths cannot see each other
3. **Structured Format**: Use clear separators between paths
4. **Tally Section**: Force explicit counting of agreement
5. **Confidence Measurement**: Require confidence assessment based on agreement

---

## Common Mistakes Students Make

### Mistake 1: Non-Independent Paths
❌ **Bad:** "Path 2: As Path 1 concluded, I agree that..."
✓ **Good:** "Path 2: Using Bayesian analysis independently..."

### Mistake 2: Same Methodology 3 Times
❌ **Bad:** All 3 paths use risk scoring
✓ **Good:** Path 1 = scoring, Path 2 = patterns, Path 3 = economics

### Mistake 3: Vague Methodology Names
❌ **Bad:** "Path 1: Analysis", "Path 2: Different analysis"
✓ **Good:** "Path 1: Risk-Weighted Scoring", "Path 2: Pattern Recognition"

### Mistake 4: Ignoring Disagreement
❌ **Bad:** Paths disagree 2-1, pick majority and move on
✓ **Good:** Disagreement signals uncertainty, investigate more or get expert input

### Mistake 5: No Explicit Tally
❌ **Bad:** Reach conclusion without counting agreement
✓ **Good:** "PATH 1: DECLINE, PATH 2: DECLINE, PATH 3: DECLINE. Agreement: 3/3 (100%)"

---

## Practice Exercises

### Exercise 1: E-Commerce Customer Refund Decision

**Scenario:**
Customer requests refund for $890 camera bought 45 days ago (policy: 30 days).

**Data:**
- Customer claims: "Was defective from start, just been too busy"
- Product condition: Shows wear, clearly used
- Customer history: 4 returns in 6 months (high return rate)
- Customer threatening: "Will leave 1-star review if denied"
- Profit on this sale: $267
- Customer LTV if retained: ~$1,200

**Your Task:**
Write a self-consistency COSTAR prompt with 3 paths:
1. Policy Compliance Analysis
2. Customer Lifetime Value Analysis
3. Reputation Risk Analysis

Determine: APPROVE or DENY refund?

### Exercise 2: Healthcare Admission Decision

**Scenario:**
72-year-old with chest pain. Decide: Admit to hospital or discharge home?

**Data:**
- Vital signs: Stable (BP 142/88, HR 78, O2 98%)
- ECG: Shows old changes, unchanged from 6 months ago
- Troponin: Negative (rules out active heart attack)
- Patient reports: Pain now 2/10, feels much better
- Pain character: Dull, pressure-like
- Lives alone, 45 minutes from hospital
- Risk factors: Hypertension, prior MI 5 years ago

**Your Task:**
Write a self-consistency COSTAR prompt with 3 paths:
1. Risk Stratification Score (HEART score)
2. Clinical Guidelines-Based Analysis
3. Individual Patient Factors Analysis

Determine: ADMIT or DISCHARGE?

---

## Summary

### Key Takeaways:

1. ✓ **Self-Consistency = Multiple Independent Analyses**
   - Same problem, different analytical frameworks
   - Paths cannot see each other
   - Majority vote wins

2. ✓ **Proper COSTAR Prompts Must:**
   - Specify exact methodologies to use
   - Demand independence explicitly
   - Structure with clear separators
   - Require tally and confidence assessment
   - State "NOT reference other paths"

3. ✓ **Benefits:**
   - Higher accuracy than single analysis
   - Confidence measurement (agreement = confidence)
   - Bias reduction
   - Error detection

4. ✓ **Agreement Levels:**
   - 3/3 = Very high confidence → Proceed
   - 2/3 = Medium confidence → Caution
   - 1/3 = Low confidence → Need more analysis

5. ✓ **Critical in High-Stakes Decisions:**
   - E-commerce: Fraud detection, large refunds
   - Healthcare: Diagnoses, admission decisions
   - Anywhere error cost is high

### Remember:
**Simple prompts get simple answers.**
**Detailed self-consistency prompts with explicit methodologies get reliable, confident answers.**

In e-commerce, this prevents costly mistakes.
In healthcare, this saves lives.

---

## Next Steps

1. Practice writing detailed COSTAR prompts with methodology specifications
2. Try self-consistency on real decisions
3. Compare results with single-path analysis
4. Measure how agreement correlates with correctness
5. Move on to Maieutic Prompting (next technique)

Master the art of specifying independent reasoning paths! 🎯