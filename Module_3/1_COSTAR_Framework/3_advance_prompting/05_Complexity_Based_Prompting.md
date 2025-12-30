# Complexity-Based Prompting - Complete Guide

## What is Complexity-Based Prompting?

Complexity-Based prompting generates multiple solutions at increasing levels of complexity (simple, moderate, complex), then compares them to select the most appropriate level of thoroughness for the problem at hand. More complex approaches consider more variables, edge cases, and interactions.

### Think of it like this:

**Regular Prompting:**
```
Problem → Single solution approach → Done
```

**Complexity-Based Prompting:**
```
Problem → Simple solution (quick, basic)
        → Moderate solution (more factors)
        → Complex solution (comprehensive)
        → Compare and select best fit
```

---

## Why Use Complexity-Based Prompting?

### Benefits:

1. **Appropriate Thoroughness** - Match solution depth to problem importance
2. **Catches Edge Cases** - Complex approaches find what simple ones miss
3. **Reveals Trade-offs** - See cost/benefit of additional complexity
4. **Prevents Under-thinking** - Ensures important problems get deep analysis
5. **Prevents Over-thinking** - Shows when simple solution is sufficient

### When to Use Complexity-Based:

✓ **Use when:**
- Uncertain how thorough analysis needs to be
- Problem complexity is unclear upfront
- Want to see what additional depth reveals
- High-stakes decisions (use complex)
- Need to justify level of analysis

✗ **Don't use when:**
- Clearly simple problem (just solve it)
- Time is extremely critical
- Complexity level is obvious
- Generating 3 solutions is wasteful

---

## How It Works

### The Multi-Level Generation Process:

**Level 1 - Simple Approach:**
- Quick analysis
- Obvious factors only
- Basic solution
- Fast but may miss important details

**Level 2 - Moderate Approach:**
- More factors considered
- Some interaction between factors
- Deeper analysis
- Balance of speed and thoroughness

**Level 3 - Complex Approach:**
- Comprehensive analysis
- All factors and interactions
- Edge cases considered
- Thorough but time-intensive

**Level 4 - Comparison:**
- What does each level catch/miss?
- Cost/benefit of complexity
- Select appropriate level

---

## Example 1: E-Commerce - Inventory Allocation Strategy

### Business Problem:
Allocate 110,000 units of holiday inventory across 3 warehouses to maximize profit and customer satisfaction while minimizing costs.

### Why Complexity-Based Helps:
- Simple approach may miss cost interactions
- Moderate adds shipping optimization
- Complex considers all variables and constraints
- Compare to see what each complexity level reveals

### COSTAR Prompt:

```
Context: We need to allocate 110,000 units of holiday inventory across 3 
warehouses. The allocation significantly impacts shipping costs, delivery 
times, return processing, and customer satisfaction. We need to determine 
the appropriate level of analysis complexity.

Objective: Generate three allocation strategies at increasing complexity 
levels, then compare them to determine which level of analysis is appropriate 
and what value additional complexity provides.

Style: Generate three complete solutions - Simple (basic proportional), 
Moderate (adds shipping optimization), Complex (comprehensive multi-variable 
optimization). For each, show methodology, allocation, and expected outcomes.

Tone: Analytical and strategic, like a supply chain analyst presenting 
options at different depth levels to executives.

Audience: Supply chain leadership deciding on allocation strategy and 
justifying level of analysis effort.

Response Format:

═══════════════════════════════════════════════════════════════════════
APPROACH 1: SIMPLE COMPLEXITY
═══════════════════════════════════════════════════════════════════════

Methodology: [Basic approach description]
Factors Considered: [List - should be 2-3 obvious factors]
Factors Ignored: [What this approach doesn't consider]

Allocation:
[Show warehouse allocations]

Expected Outcomes:
• Shipping cost: $[amount]
• Delivery time: [metric]
• Customer satisfaction: [estimate]
• Total cost: $[amount]

Pros:
✓ [Advantage 1]
✓ [Advantage 2]

Cons:
✗ [What this misses]
✗ [What this misses]

═══════════════════════════════════════════════════════════════════════
APPROACH 2: MODERATE COMPLEXITY
═══════════════════════════════════════════════════════════════════════

Methodology: [More sophisticated approach]
Factors Considered: [List - should be 5-7 factors]
Factors Ignored: [What this still doesn't consider]

Allocation:
[Show warehouse allocations with reasoning]

Expected Outcomes:
• Shipping cost: $[amount]
• Delivery time: [metric]
• Customer satisfaction: [estimate]
• Return processing: [metric]
• Total cost: $[amount]

Comparison to Simple:
• Cost difference: $[amount] ([better/worse])
• What this catches that Simple missed: [Key insights]

Pros:
✓ [Advantage 1]
✓ [Advantage 2]

Cons:
✗ [What this still misses]

═══════════════════════════════════════════════════════════════════════
APPROACH 3: COMPLEX COMPREHENSIVE
═══════════════════════════════════════════════════════════════════════

Methodology: [Comprehensive multi-variable optimization]
Factors Considered: [List - should be 10+ factors with interactions]
Edge Cases Addressed: [List edge cases]

Detailed Analysis:
[Step-by-step breakdown showing all considerations]

Allocation:
[Show warehouse allocations with full cost modeling]

Expected Outcomes:
• Shipping cost: $[amount] (detailed breakdown)
• Delivery time: [metric] (by customer segment)
• Customer satisfaction: [estimate] (with reasoning)
• Return processing: [metric] (with geographic factors)
• Holding costs: [metric]
• Transfer costs: [metric]
• Total cost: $[amount]

Comparison to Moderate:
• Cost difference: $[amount] ([better/worse])
• What this catches that Moderate missed: [Key insights]

Pros:
✓ [Advantage 1]
✓ [Advantage 2]
✓ [Advantage 3]

Cons:
✗ [Time/effort required]

═══════════════════════════════════════════════════════════════════════
COMPLEXITY COMPARISON & RECOMMENDATION
═══════════════════════════════════════════════════════════════════════

Financial Impact Analysis:
• Simple approach total cost: $[amount]
• Moderate approach total cost: $[amount] (saves $[X] vs Simple)
• Complex approach total cost: $[amount] (saves $[Y] vs Moderate)

Incremental Value:
• Simple → Moderate: $[X] savings for [hours] additional effort
  ROI: $[X] / [hours] = $[amount]/hour
  
• Moderate → Complex: $[Y] savings for [hours] additional effort
  ROI: $[Y] / [hours] = $[amount]/hour

What Each Level Catches:
Simple:
✓ [Basic insight 1]
✓ [Basic insight 2]
✗ Misses: [Critical thing]

Moderate:
✓ All of Simple
✓ [Additional insight 1]
✓ [Additional insight 2]
✗ Misses: [Edge case]

Complex:
✓ All of Moderate
✓ [Additional insight 1]
✓ [Edge case handling]
✓ [Interaction effect]

RECOMMENDATION: [Which approach to use]

Rationale:
[Why this complexity level is appropriate for this problem]

---

SCENARIO DATA:

Warehouses:
1. East Coast (New Jersey)
   - Capacity: 40,000 units
   - Serves: 40% of customer base
   - Coverage: 2-day shipping to 60% of US population
   - Average shipping cost: $7 (2-day), $4 (standard)
   - Return processing time: 2 days (near major facilities)

2. West Coast (California)
   - Capacity: 35,000 units
   - Serves: 30% of customer base
   - Coverage: 2-day shipping to West Coast only (30% of US)
   - Average shipping cost: $8 (2-day to West), $6 (standard to East)
   - Return processing time: 3 days

3. Midwest (Ohio)
   - Capacity: 35,000 units (can stretch to 40,000)
   - Serves: 30% of customer base
   - Coverage: 2-3 day shipping to most of US
   - Average shipping cost: $6 (2-day), $3.50 (standard)
   - Return processing time: 2 days (central location)

Products to Allocate (Total: 110,000 units):

1. Electronics (High-Value)
   - Demand: 45,000 units
   - Average price: $200
   - Return rate: 15%
   - Customer expectation: Premium shipping (2-day preferred)
   - Margin: 18%
   - Weight: 3 lbs average

2. Apparel (High-Return)
   - Demand: 35,000 units
   - Average price: $50
   - Return rate: 25% (fit issues)
   - Customer expectation: Standard shipping acceptable
   - Margin: 40%
   - Weight: 1 lb average

3. Home Goods (Heavy)
   - Demand: 30,000 units
   - Average price: $150
   - Return rate: 10%
   - Customer expectation: Standard shipping acceptable
   - Margin: 25%
   - Weight: 8 lbs average

Cost Factors:
- Holding cost: $2/unit/month
- Transfer cost between warehouses: $5/unit
- Return shipping: $10 + distance factor
- Processing cost per return: $15
- Premium 2-day shipping: $8
- Standard shipping: $4
- Customer satisfaction score impacts repeat rate:
  * 2-day delivery: 85% repeat rate
  * 3-day delivery: 75% repeat rate
  * 4-5 day delivery: 65% repeat rate

Constraints:
- Total units = 110,000 (must allocate all)
- East warehouse: 40,000 capacity (hard limit)
- West warehouse: 35,000 capacity (hard limit)
- Midwest warehouse: 35,000 normal, 40,000 maximum
- Cannot split product types across warehouses (operational constraint)
- Holiday season: 60% of orders need 2-day shipping

Generate three allocation strategies:
SIMPLE: Basic proportional allocation by customer base
MODERATE: Add shipping cost optimization by product type
COMPLEX: Comprehensive optimization with all costs, returns, 
         satisfaction, and constraint handling
```

### Expected AI Response Structure:

The AI would generate three complete allocation strategies showing:

**Simple Approach:**
- Allocate 40% to East (44K units), 30% to West (33K), 30% to Midwest (33K)
- Basic logic only
- Total cost: ~$1,200,000
- Misses: Shipping optimization, return handling, product characteristics

**Moderate Approach:**
- Consider product types and shipping needs
- Electronics to East/West (premium shipping), Apparel to Midwest (returns)
- Warehouse capacity adjustments
- Total cost: ~$1,150,000 (saves $50K)
- Catches: Product-specific needs, basic shipping optimization
- Misses: Detailed cost modeling, interaction effects

**Complex Approach:**
- Full cost modeling per product per warehouse
- Return processing optimization
- Customer satisfaction impacts
- Constraint handling with transfers
- Total cost: ~$1,097,000 (saves additional $53K)
- Catches: All edge cases, interaction effects, optimal transfers

**Comparison Shows:**
- Simple → Moderate: $50K savings for ~4 hours work = $12,500/hour ROI
- Moderate → Complex: $53K savings for ~6 hours work = $8,833/hour ROI
- Recommendation: Use Complex approach (high ROI justifies effort for $110M inventory)

---

## Example 2: Healthcare - Post-Surgical Care Protocol Design

### Medical Problem:
Design a post-operative care protocol for knee replacement surgery patients. Need to determine appropriate complexity level for protocol.

### Why Complexity-Based is CRITICAL:

⚠️ **PATIENT OUTCOMES DEPEND ON PROTOCOL THOROUGHNESS** ⚠️
- Simple protocol may miss complications
- Moderate adds key monitoring
- Complex captures all patient-specific factors
- Must justify protocol complexity to hospital administration

### COSTAR Prompt:

```
Context: We're designing a post-operative care protocol for total knee 
replacement patients. The protocol impacts patient outcomes, complication 
rates, hospital readmissions, and healthcare costs. We need to determine 
the appropriate level of protocol complexity.

Objective: Generate three post-op care protocols at increasing complexity 
levels, then compare them to determine which provides optimal patient 
outcomes while justifying the required resources.

Style: Generate three complete protocols - Simple (basic recovery steps), 
Moderate (adds monitoring and risk stratification), Complex (comprehensive 
individualized care). For each, show protocol elements and expected outcomes.

Tone: Clinical and evidence-based, like a clinical protocol committee 
presenting options at different complexity levels with outcomes data.

Audience: Hospital clinical leadership and protocol committee deciding on 
care protocol and resource allocation.

Response Format:

═══════════════════════════════════════════════════════════════════════
PROTOCOL 1: SIMPLE APPROACH
═══════════════════════════════════════════════════════════════════════

Protocol Elements:
[List 3-5 basic components]

Monitoring Plan:
[Basic monitoring schedule]

Follow-up Schedule:
[Simple appointment timeline]

Patient Education:
[Basic education provided]

Expected Outcomes:
• Complication rate: [%]
• Readmission rate: [%]
• Patient satisfaction: [score]
• Functional recovery: [metric]
• Cost per patient: $[amount]

Pros:
✓ [Advantage]
✓ [Advantage]

Cons:
✗ [What this misses]
✗ [What this misses]

Patients at Risk:
[Which patient populations this doesn't serve well]

═══════════════════════════════════════════════════════════════════════
PROTOCOL 2: MODERATE COMPLEXITY
═══════════════════════════════════════════════════════════════════════

Protocol Elements:
[List 8-12 components with risk stratification]

Risk Stratification:
[How patients are categorized]

Monitoring Plan:
[Differentiated by risk level]

Follow-up Schedule:
[Tailored to patient needs]

Patient Education:
[Comprehensive education plan]

Expected Outcomes:
• Complication rate: [%]
• Readmission rate: [%]
• Patient satisfaction: [score]
• Functional recovery: [metric]
• Cost per patient: $[amount]

Comparison to Simple:
• Complication reduction: [%]
• Readmission reduction: [%]
• Cost per complication avoided: $[amount]

Pros:
✓ [Advantage]
✓ [Advantage]

Cons:
✗ [What this still misses]

Patients at Risk:
[Which edge cases still need more]

═══════════════════════════════════════════════════════════════════════
PROTOCOL 3: COMPREHENSIVE COMPLEXITY
═══════════════════════════════════════════════════════════════════════

Protocol Elements:
[List 15-20+ components, fully individualized]

Risk Stratification:
[Multi-factor risk scoring]

Individualization Factors:
[All patient-specific considerations]

Monitoring Plan:
[Intensive, individualized monitoring]

Intervention Triggers:
[When to escalate care]

Support Systems:
[All support resources]

Expected Outcomes:
• Complication rate: [%]
• Readmission rate: [%]
• Patient satisfaction: [score]
• Functional recovery: [metric]
• Cost per patient: $[amount]

Comparison to Moderate:
• Complication reduction: [%]
• Readmission reduction: [%]
• Quality-adjusted life years gained: [metric]

Pros:
✓ [Advantage]
✓ [Advantage]
✓ [Advantage]

Cons:
✗ [Resource requirements]

═══════════════════════════════════════════════════════════════════════
PROTOCOL COMPARISON & RECOMMENDATION
═══════════════════════════════════════════════════════════════════════

Clinical Outcome Analysis:
[Compare complication rates, readmissions, recovery times]

Cost-Effectiveness Analysis:
[Cost per complication avoided, cost per quality-adjusted life year]

What Each Level Catches:
Simple: [Basic care elements]
  ✗ Misses: [Critical issue]
  
Moderate: [Adds important elements]
  ✗ Misses: [Edge cases]
  
Complex: [Comprehensive coverage]
  ✓ Catches: [All scenarios]

Resource Requirements:
Simple: [Minimal resources]
Moderate: [Moderate resources]
Complex: [Significant resources but justified by outcomes]

RECOMMENDATION: [Which protocol to implement]

Rationale:
[Why this complexity level balances outcomes and resources]

Implementation Plan:
[How to roll out recommended protocol]

---

PATIENT POPULATION DATA:

Total Knee Replacements Per Year: 450 patients

Patient Demographics:
- Age range: 45-85 years
- 60% female, 40% male
- 40% have 2+ comorbidities
- 25% live alone
- 15% have limited English proficiency

Common Comorbidities:
- Diabetes: 35%
- Hypertension: 60%
- Obesity (BMI >30): 45%
- Heart disease: 20%
- Chronic pain conditions: 30%
- Depression/anxiety: 25%

Current Outcomes (with basic protocol):
- Complication rate: 12%
- 90-day readmission: 8%
- DVT/PE: 2%
- Infection: 3%
- Falls: 4%
- Pain management failure: 5%
- Patient satisfaction: 72%

Cost Data:
- Surgical cost: $25,000
- Uncomplicated recovery: $5,000
- Complication cost: $15,000-$50,000 per incident
- Readmission cost: $12,000 average
- PT/OT: $150 per session
- Home health visit: $200
- Monitoring technology: $500 per patient

Evidence Base:
- Enhanced recovery protocols reduce complications by 30-40%
- Risk-stratified care reduces readmissions by 25-35%
- Comprehensive protocols improve satisfaction by 15-20 points
- Early intervention prevents 60% of complications

Generate three protocols:
SIMPLE: Basic post-op care with standard follow-up
MODERATE: Risk-stratified with enhanced recovery elements
COMPLEX: Fully individualized comprehensive care protocol
```

### What Students Should Learn:

**Key Concepts:**

1. **Complexity Has Value**: More complex approaches catch what simple ones miss
2. **Diminishing Returns**: Each complexity level adds less value than previous
3. **Cost-Benefit Analysis**: Justify complexity with outcomes/savings
4. **Match to Stakes**: High-stakes problems deserve complex analysis
5. **Resource Trade-offs**: Complex approaches require more time/effort

**In E-Commerce Example:**
- Simple: Misses $103K in savings (ignores interactions)
- Moderate: Captures $50K (good improvement)
- Complex: Captures additional $53K (full optimization)
- Decision: Use Complex (ROI justifies 10 hours of effort for $110M inventory)

**In Healthcare Example:**
- Simple: 12% complication rate (baseline)
- Moderate: 8% complication rate (risk stratification helps)
- Complex: 5% complication rate (individualized care optimal)
- Decision: Use Complex (saving lives and $450K annually justifies resources)

---

## How to Write Effective Complexity-Based Prompts

### Template Structure:

```
Context: [Problem requiring complexity determination]

Objective: Generate three solutions at increasing complexity levels, 
then compare to determine which provides best value.

Style: Generate three complete solutions - Simple ([approach]), 
Moderate ([approach]), Complex ([approach]). Show full methodology 
and outcomes for each.

Tone: Analytical, like a consultant presenting options at different 
depth levels.

Audience: [Decision makers who need to justify analysis level]

Response Format:

═══════════════════════════════════════════════════════════════════════
APPROACH 1: SIMPLE COMPLEXITY
═══════════════════════════════════════════════════════════════════════

Methodology: [Basic approach]
Factors: [2-3 obvious factors]
Solution: [Basic solution]
Outcomes: [Expected results]
Pros/Cons: [What it catches/misses]

═══════════════════════════════════════════════════════════════════════
APPROACH 2: MODERATE COMPLEXITY
═══════════════════════════════════════════════════════════════════════

Methodology: [More sophisticated]
Factors: [5-7 factors]
Solution: [Enhanced solution]
Outcomes: [Improved results]
Comparison: [vs Simple]
Pros/Cons: [What it adds/still misses]

═══════════════════════════════════════════════════════════════════════
APPROACH 3: COMPLEX COMPREHENSIVE
═══════════════════════════════════════════════════════════════════════

Methodology: [Comprehensive]
Factors: [10+ factors with interactions]
Solution: [Optimal solution]
Outcomes: [Best results]
Comparison: [vs Moderate]
Pros/Cons: [Complete coverage/effort required]

═══════════════════════════════════════════════════════════════════════
COMPARISON & RECOMMENDATION
═══════════════════════════════════════════════════════════════════════

Value Analysis: [What each level provides]
Incremental ROI: [Cost/benefit of complexity]
Recommendation: [Which to use and why]

---

[Provide all scenario data]

Generate three approaches:
SIMPLE: [Description]
MODERATE: [Description]
COMPLEX: [Description]
```

### Critical Elements:

1. **Three Distinct Levels**: Simple (2-3 factors) → Moderate (5-7 factors) → Complex (10+ factors)
2. **Full Solutions**: Each level must be complete, not just partial
3. **Explicit Comparison**: Show what each catches that previous missed
4. **Outcome Metrics**: Quantify results at each level
5. **Recommendation**: State which level to use and justify with ROI

---

## Common Mistakes Students Make

### Mistake 1: Levels Not Distinct Enough
❌ **Bad:** Simple uses 5 factors, Moderate uses 6 factors
✓ **Good:** Simple 2-3 factors, Moderate 5-7 factors, Complex 10+ factors

### Mistake 2: No Real Comparison
❌ **Bad:** Generate three approaches, pick one without comparing
✓ **Good:** "Moderate catches X that Simple missed, saves $Y, worth Z hours effort"

### Mistake 3: Always Picking Complex
❌ **Bad:** "Complex is most thorough, always use it"
✓ **Good:** "For $100 decision use Simple, for $100M decision use Complex"

### Mistake 4: Incomplete Solutions
❌ **Bad:** Simple = "do basic allocation", no details
✓ **Good:** Simple = full allocation with numbers, logic, outcomes

### Mistake 5: No ROI Analysis
❌ **Bad:** "Complex is better" (no justification)
✓ **Good:** "Complex saves $53K for 6 hours work = $8,833/hour ROI"

---

## Practice Exercises

### Exercise 1: E-Commerce Pricing Strategy

**Scenario:**
New product launch. Need pricing strategy. Product cost: $40, competitors: $79-$129.

**Your Task:**
Write a Complexity-Based COSTAR prompt that generates:

**Simple:** Cost-plus pricing (2x markup = $80)
**Moderate:** Competitive pricing analysis (5-7 factors: competitor prices, positioning, perceived value)
**Complex:** Dynamic pricing with market segmentation (10+ factors: segment willingness to pay, competitor response modeling, demand elasticity, seasonal factors, inventory optimization)

Compare and recommend with ROI analysis.

### Exercise 2: Healthcare Diabetes Management

**Scenario:**
Design diabetes management program for 500 patients. Current HbA1c average: 8.2%, target: <7.0%.

**Your Task:**
Write a Complexity-Based COSTAR prompt that generates:

**Simple:** Medication adjustment + quarterly follow-up
**Moderate:** Medication + lifestyle counseling + monthly monitoring + risk stratification
**Complex:** Fully individualized (continuous glucose monitoring, personalized nutrition, mental health support, social determinants, family involvement, technology integration)

Compare outcomes and cost-effectiveness.

---

## Summary

### Key Takeaways:

1. ✓ **Three Distinct Complexity Levels**
   - Simple: Quick, 2-3 factors, basic solution
   - Moderate: Balanced, 5-7 factors, optimized solution
   - Complex: Comprehensive, 10+ factors, optimal solution

2. ✓ **Each Level Reveals More**
   - Simple catches obvious issues
   - Moderate adds important optimizations
   - Complex captures edge cases and interactions

3. ✓ **Compare with ROI**
   - What does each level cost (time/effort)?
   - What does each level save (money/outcomes)?
   - Which provides best value?

4. ✓ **Match to Stakes**
   - Low stakes → Simple sufficient
   - Medium stakes → Moderate appropriate
   - High stakes → Complex justified

5. ✓ **Proper COSTAR Prompts Must:**
   - Generate three complete solutions
   - Show full methodology for each
   - Explicitly compare outcomes
   - Provide ROI analysis
   - Recommend with justification

### Remember:
**Not all problems need complex solutions.**
**But complex problems need complex analysis to avoid costly mistakes.**

In e-commerce, complexity-based saves $103K on $110M inventory.
In healthcare, complexity-based reduces complications by 58% (12% → 5%).

---

## Next Steps

1. Practice generating three distinct complexity levels
2. Try complexity-based on real decisions
3. Calculate ROI for each complexity jump
4. Learn when simple is sufficient vs when complex is essential
5. Move on to Self-Refine Prompting (next technique)

Master matching solution complexity to problem importance! 📊
