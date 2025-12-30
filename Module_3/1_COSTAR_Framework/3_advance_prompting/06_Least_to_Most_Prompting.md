# Least-to-Most Prompting - Complete Guide

## What is Least-to-Most Prompting?

Least-to-Most prompting breaks complex problems into a sequence of sub-problems, solves them in order from simplest (least) to most complex (most), where each solution builds on and informs the next. Like climbing stairs—you can't skip steps because each step is the foundation for the next.

### Think of it like this:

**Regular Prompting:**
```
Complex Problem → Attempt to solve all at once → Overwhelmed or incomplete
```

**Least-to-Most Prompting:**
```
Complex Problem 
  ↓
Identify all sub-problems
  ↓
Order by dependency (what must be solved first?)
  ↓
Sub-problem 1 (foundation) → Solution 1
  ↓
Sub-problem 2 (uses Solution 1) → Solution 2
  ↓
Sub-problem 3 (uses Solutions 1&2) → Solution 3
  ↓
Integrate all solutions → Complete solution
```

---

## Why Use Least-to-Most Prompting?

### Benefits:

1. **Handles Complex Multi-Step Problems** - Makes impossible seem manageable
2. **Each Solution Builds on Previous** - Creates logical progression
3. **Shows Dependencies Clearly** - Reveals what must come first
4. **Prevents Overwhelm** - Breaks complexity into digestible pieces
5. **Creates Reusable Components** - Early solutions help later ones

### When to Use Least-to-Most:

✓ **Use when:**
- Problem has clear sequential dependencies
- Sub-problems must be solved in order
- Later decisions depend on earlier ones
- Complexity is overwhelming if tackled all at once
- Multi-stage optimization needed

✗ **Don't use when:**
- Problem is simple and single-step
- Sub-problems are independent (no dependencies)
- Can solve all aspects simultaneously
- Order doesn't matter

---

## How It Works

### The Sequential Decomposition Process:

**Phase 1 - Decomposition:**
- Break complex problem into sub-problems
- Identify what each sub-problem depends on
- Order sub-problems by dependency chain

**Phase 2 - Sequential Solving:**
- Solve Sub-problem 1 (foundation, no dependencies)
- Use Solution 1 to inform Sub-problem 2
- Use Solutions 1&2 to inform Sub-problem 3
- Continue building on previous solutions

**Phase 3 - Integration:**
- Combine all solutions
- Show how each enables the next
- Present complete solution

---

## Example 1: E-Commerce - Complete Checkout Optimization

### Business Problem:
Shopping cart abandonment is 68% (current conversion 2.3%). Target: Reduce to 32% (target conversion 3.5%). Need comprehensive checkout redesign.

### Why Least-to-Most Helps:
- Can't optimize shipping before simplifying form
- Can't add trust elements before streamlining flow
- Mobile optimization requires all previous improvements
- Each improvement enables the next one

### COSTAR Prompt:

```
Context: Our e-commerce checkout has 68% cart abandonment (conversion: 2.3%). 
We need to improve to 32% abandonment (conversion: 3.5%), but the problem 
is complex with multiple interrelated issues. We need to solve these issues 
sequentially because later optimizations depend on earlier ones being complete.

Objective: Use Least-to-Most approach to break down the checkout optimization 
into sequential sub-problems, solve each in dependency order where each 
solution informs and enables the next, then integrate into complete solution.

Style: Sequential problem-solving where you explicitly show: (1) how you 
identify and order sub-problems by dependency, (2) how you solve each 
sub-problem building on previous solutions, (3) how each solution enables 
the next one.

Tone: Strategic and systematic, like a product manager planning a phased 
optimization where each phase depends on the previous phase being complete.

Audience: Product and engineering teams implementing sequential improvements.

Response Format:

═══════════════════════════════════════════════════════════════════════
PHASE 1: PROBLEM DECOMPOSITION & DEPENDENCY ANALYSIS
═══════════════════════════════════════════════════════════════════════

Complex Problem: [State the overall problem]

Break into Sub-Problems:
1. [Sub-problem 1]
2. [Sub-problem 2]
3. [Sub-problem 3]
4. [Sub-problem 4]
5. [Sub-problem 5]

Dependency Analysis:
[For each sub-problem, identify what it depends on]

Sub-problem 1 depends on: [Nothing - this is the foundation]
Sub-problem 2 depends on: [Sub-problem 1 because...]
Sub-problem 3 depends on: [Sub-problems 1&2 because...]
Sub-problem 4 depends on: [Sub-problems 1,2,3 because...]
Sub-problem 5 depends on: [All previous because...]

Ordered Sequence (by dependency):
1. [Foundation sub-problem]
2. [Depends on #1]
3. [Depends on #1,2]
4. [Depends on #1,2,3]
5. [Final integration depends on all]

═══════════════════════════════════════════════════════════════════════
PHASE 2: SEQUENTIAL PROBLEM SOLVING
═══════════════════════════════════════════════════════════════════════

SUB-PROBLEM 1: [Foundation Issue - No Dependencies]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Current State:
[Describe current problem]

Analysis:
[Analyze the issue]

Solution:
[Detailed solution]

Expected Impact:
• Metric 1: [Current] → [Target]
• Metric 2: [Current] → [Target]
• Conversion: [Current %] → [New %]

Why This Enables Sub-Problem 2:
[Explain how this solution makes next step possible]

SUB-PROBLEM 2: [Second Issue - Depends on #1]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

How This Builds on Solution 1:
[Explicitly show dependency on previous solution]

Current State (with Solution 1 applied):
[Describe current state after #1]

Analysis:
[Analyze with context from Solution 1]

Solution:
[Detailed solution building on #1]

Expected Impact:
• Metric 1: [After #1] → [Target]
• Metric 2: [After #1] → [Target]  
• Conversion: [After #1 %] → [New %]

Why This Enables Sub-Problem 3:
[Explain how Solutions 1&2 together enable next step]

SUB-PROBLEM 3: [Third Issue - Depends on #1,2]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

How This Builds on Solutions 1&2:
[Explicitly show dependencies]

Current State (with Solutions 1&2 applied):
[Describe state after #1 and #2]

Analysis:
[Analyze with context from previous solutions]

Solution:
[Detailed solution leveraging #1 and #2]

Expected Impact:
• Metric 1: [After #1,2] → [Target]
• Conversion: [After #1,2 %] → [New %]

Why This Enables Sub-Problem 4:
[Explain enabling effect]

SUB-PROBLEM 4: [Fourth Issue - Depends on #1,2,3]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

How This Builds on Solutions 1,2,3:
[Show dependencies on all previous]

Current State (with Solutions 1,2,3 applied):
[Describe state]

Analysis:
[Analyze]

Solution:
[Detailed solution]

Expected Impact:
• Conversion: [After #1,2,3 %] → [New %]

Why This Enables Sub-Problem 5:
[Explain]

SUB-PROBLEM 5: [Final Issue - Depends on All Previous]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

How This Builds on All Previous Solutions:
[Show how all previous solutions make this possible]

Current State (with All Previous Applied):
[Describe state]

Solution:
[Final optimization]

Expected Impact:
• Final Conversion: [Target %]

═══════════════════════════════════════════════════════════════════════
PHASE 3: INTEGRATED SOLUTION & IMPLEMENTATION
═══════════════════════════════════════════════════════════════════════

Sequential Dependency Chain:
Solution 1 enables → Solution 2 enables → Solution 3 enables → 
Solution 4 enables → Solution 5 = Complete Solution

Complete Integrated Solution:
[How all solutions work together]

Implementation Sequence:
Week 1: [Sub-problem 1]
Week 2: [Sub-problem 2]
Week 3: [Sub-problem 3]
Week 4: [Sub-problem 4]
Week 5: [Sub-problem 5]

Projected Results:
• Current conversion: 2.3%
• After Sub-problem 1: [X%] (+[delta])
• After Sub-problem 2: [Y%] (+[delta])
• After Sub-problem 3: [Z%] (+[delta])
• After Sub-problem 4: [A%] (+[delta])
• After Sub-problem 5: 3.8% (+1.5% total, exceeds 3.5% goal)

Why Sequential Order Matters:
[Explain what would happen if you tried to skip steps]

---

PROBLEM DATA:

Current Checkout Performance:
- Cart abandonment: 68%
- Conversion rate: 2.3%
- Average cart value: $147
- Annual revenue lost to abandonment: $4.2M

Target Goals:
- Cart abandonment: 32%
- Conversion rate: 3.5%
- Revenue recovery: ~$1.5M annually

Customer Feedback (Top Complaints):
1. "Too many form fields" - 42%
2. "Unexpected shipping costs" - 38%
3. "Don't trust payment security" - 22%
4. "Checkout took too long" - 31%
5. "Had to create account" - 18%

Data Insights:
- 23 form fields currently (industry best practice: 8-12)
- Shipping cost shown only at final step
- 75% of traffic is mobile, but mobile abandonment is 85%
- Average checkout time: 4 minutes 35 seconds
- Competitor average: 2 minutes 15 seconds
- Account creation required before checkout

Technical Constraints:
- Payment gateway integration takes 2 weeks
- Mobile redesign requires desktop optimization first
- Guest checkout needs email capture strategy
- Trust badges need legal review (1 week)

Use Least-to-Most approach to:
1. Decompose into sub-problems with dependencies
2. Order by what must come first
3. Solve each sequentially, showing how each enables the next
4. Integrate into complete phased implementation plan

Sub-problems must be ordered so that:
- Form simplification comes FIRST (enables everything else)
- Shipping transparency comes SECOND (needs simpler form)
- Trust/payment comes THIRD (needs streamlined flow)
- Mobile optimization comes FOURTH (applies all previous to mobile)
- Account removal comes LAST (possible only after other fixes)
```

### Expected AI Response Structure:

The AI would show:

**Phase 1 - Decomposition:**
```
Sub-problem 1: Form field reduction (FOUNDATION)
  Depends on: Nothing
  Why first: Simpler form enables all other optimizations

Sub-problem 2: Shipping transparency
  Depends on: #1 (needs simplified form to add shipping calculator)
  Why second: Creates space in UI, sets pricing expectations

Sub-problem 3: Payment trust
  Depends on: #1,2 (needs streamlined flow for trust signals)
  Why third: Shorter form + clear pricing = trust opportunity

Sub-problem 4: Mobile optimization
  Depends on: #1,2,3 (applies all improvements to mobile)
  Why fourth: Must optimize desktop before mobile

Sub-problem 5: Remove account requirement
  Depends on: #1,2,3,4 (viable only with guest experience optimized)
  Why last: Final friction removal
```

**Phase 2 - Sequential Solving:**
Each sub-problem solved with explicit reference to how previous solutions enable it.

**Phase 3 - Integration:**
Shows complete solution with phased rollout:
- Week 1: Forms (2.3% → 2.7%)
- Week 2: Shipping (2.7% → 3.0%)
- Week 3: Trust + Guest (3.0% → 3.4%)
- Week 4: Mobile (3.4% → 3.8%)
- Final: 3.8% conversion (exceeds 3.5% goal)

---

## Example 2: Healthcare - Post-Surgical Complication Management

### Medical Problem:
Patient 3 days post-appendectomy presents with fever (101.8°F) and abdominal pain. Must systematically determine cause and treatment, where each diagnostic step depends on previous findings.

### Why Least-to-Most is CRITICAL:

⚠️ **PATIENT SAFETY REQUIRES SYSTEMATIC APPROACH** ⚠️
- Can't evaluate surgical site before ruling out life threats
- Can't plan treatment before completing diagnostic workup
- Each finding changes what you look for next
- Skipping steps could miss critical diagnoses

### COSTAR Prompt:

```
Context: Emergency evaluation of post-surgical patient with fever and pain. 
This requires systematic sequential assessment where each diagnostic and 
treatment decision depends on findings from previous steps. Cannot skip 
steps or rush to conclusions without proper sequential evaluation.

Objective: Use Least-to-Most approach to break down post-operative 
complication assessment into sequential sub-problems ordered by medical 
priority and dependency, where each evaluation step builds on previous 
findings to reach diagnosis and treatment plan.

Style: Clinical systematic approach showing: (1) how you decompose into 
sequential diagnostic steps, (2) how each step's findings inform the next 
step, (3) how you build from life-threat exclusion to specific diagnosis 
to treatment plan.

Tone: Clinical and methodical, like an attending physician teaching 
residents systematic post-operative evaluation where each step logically 
follows from the previous.

Audience: Clinical team performing sequential post-operative assessment.

Response Format:

═══════════════════════════════════════════════════════════════════════
PHASE 1: PROBLEM DECOMPOSITION & DIAGNOSTIC SEQUENCE
═══════════════════════════════════════════════════════════════════════

Complex Clinical Problem: [State overall problem]

Break into Sequential Diagnostic Sub-Problems:
1. [Most urgent - life threat evaluation]
2. [Depends on #1 - surgical site assessment]
3. [Depends on #1,2 - deeper investigation]
4. [Depends on #1,2,3 - systemic causes]
5. [Depends on all - treatment plan]

Clinical Dependency Chain:
[Explain why order matters from safety perspective]

Why Sub-problem 1 Must Come First:
[Life-threatening conditions must be ruled out before anything else]

Why Sub-problem 2 Depends on #1:
[Can only proceed to site evaluation if patient is stable]

Why Sub-problem 3 Depends on #1,2:
[Surface findings inform need for deeper investigation]

Why Sub-problem 4 Depends on #1,2,3:
[If local causes unclear, consider systemic]

Why Sub-problem 5 Depends on All:
[Treatment plan requires complete diagnostic picture]

═══════════════════════════════════════════════════════════════════════
PHASE 2: SEQUENTIAL CLINICAL EVALUATION
═══════════════════════════════════════════════════════════════════════

SUB-PROBLEM 1: Rule Out Life-Threatening Complications (FOUNDATION)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Why This Must Be First:
[Patient safety - cannot proceed without ruling out immediate threats]

Clinical Assessment:
[Systematic evaluation for emergent conditions]

Findings:
[What assessment reveals]

Decision Point:
[Is patient stable enough to proceed? Yes/No and why]

If Unstable:
[Emergency interventions required]

If Stable:
[Safe to proceed to Sub-problem 2]

Why This Enables Sub-problem 2:
[Now that life threats are ruled out, can systematically evaluate site]

SUB-PROBLEM 2: Evaluate Surgical Site (Depends on #1 Stable)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

How This Builds on Sub-problem 1:
[Patient is stable, now safe to examine surgical site in detail]

Clinical Examination:
[Detailed site evaluation]

Findings:
[What examination reveals]

Interpretation:
[What findings suggest]

Decision Point:
[Does this explain fever/pain? Fully/Partially/Not at all]

If Fully Explains:
[Can proceed to treatment]

If Partially/Not:
[Need Sub-problem 3 - deeper investigation]

Why This Enables Sub-problem 3:
[Surface findings inform what to look for internally]

SUB-PROBLEM 3: Intra-Abdominal Assessment (Depends on #1,2)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

How This Builds on Sub-problems 1&2:
[Patient stable (#1), site findings (#2) suggest need for imaging]

Diagnostic Plan:
[What imaging/tests needed based on previous findings]

Findings:
[What tests reveal]

Clinical Reasoning:
[Integration of all findings so far]

Decision Point:
[Does this explain presentation? Yes/No]

Why This Enables Sub-problem 4:
[If local causes identified, great. If not, consider systemic]

SUB-PROBLEM 4: Systemic Causes (Depends on #1,2,3)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

How This Builds on Sub-problems 1,2,3:
[If surgical causes don't fully explain, consider non-surgical]

Differential Diagnosis:
[Systemic causes to consider given previous findings]

Evaluation:
[How to assess for each]

Findings:
[Results]

Clinical Synthesis:
[Integrate all findings from #1,2,3,4]

Why This Enables Sub-problem 5:
[Complete diagnostic picture now available for treatment planning]

SUB-PROBLEM 5: Treatment Plan (Depends on All Previous)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

How This Integrates All Previous Findings:
[Synthesize findings from #1,2,3,4 into diagnosis]

Working Diagnosis:
[Most likely diagnosis based on sequential evaluation]

Treatment Plan - Immediate Actions:
[Based on complete diagnostic picture]

Treatment Plan - If Condition A (from imaging):
[Specific intervention]

Treatment Plan - If Condition B:
[Alternative intervention]

Monitoring Plan:
[Based on all previous findings]

═══════════════════════════════════════════════════════════════════════
PHASE 3: INTEGRATED CLINICAL DECISION TREE
═══════════════════════════════════════════════════════════════════════

Sequential Decision Tree:
Step 1 (Life threats) → Stable → Proceed
  ↓
Step 2 (Surgical site) → Findings → Inform imaging needs
  ↓
Step 3 (Imaging) → Results → Guide treatment type
  ↓
Step 4 (Systemic) → Ruled out → Confirm surgical cause
  ↓
Step 5 (Treatment) → Complete plan based on all findings

Why Sequential Order Saved the Patient:
[Explain what could have been missed if steps were skipped]

Complete Treatment Plan:
[Integration of all sequential findings]

Critical Teaching Point:
[Why Least-to-Most approach is essential in post-op management]

---

PATIENT CASE DATA:

Patient Profile:
- 45-year-old male
- Post-appendectomy (3 days ago)
- Uncomplicated laparoscopic procedure
- Discharged POD #1 (standard protocol)

Current Presentation:
- Temperature: 101.8°F (38.8°C)
- Heart rate: 98 bpm
- Blood pressure: 128/82 mmHg
- Respiratory rate: 18/min
- O2 saturation: 97% room air

Chief Complaint:
- Abdominal pain: 6/10 at incision, 4/10 diffuse
- Fever started this morning
- Nausea (no vomiting)
- Decreased appetite

Physical Examination:
- General: Uncomfortable, not toxic-appearing
- Surgical incisions: 3 laparoscopic sites
  * Mildly erythematous (red)
  * No purulent drainage
  * Tender to palpation
  * No crepitus (air in tissues)
- Abdomen: 
  * Soft
  * Mild diffuse tenderness
  * Bowel sounds: Present but decreased
  * No rebound or guarding
  * No palpable masses

Laboratory:
- WBC: 15,000 (elevated, normal: 4,000-11,000)
- Left shift: Present (suggests infection)
- Other labs: Within normal limits

Clinical Context:
- Post-operative fever DDx: "5 W's"
  * Wind (pneumonia): POD 1-2
  * Water (UTI): POD 3-5
  * Wound (SSI): POD 5-7
  * Walking (DVT): POD 5-10
  * Wonder drugs (drug fever): Anytime
- But also consider:
  * Intra-abdominal abscess
  * Retained surgical material
  * Anastomotic leak (if bowel work done)
  * Ileus vs obstruction

This is POD #3, which makes timing ambiguous for standard DDx.

Use Least-to-Most approach to:
1. Decompose into sequential diagnostic steps by medical priority
2. Show how each evaluation depends on previous findings
3. Build from life-threat exclusion → site evaluation → 
   imaging → systemic causes → treatment plan
4. Demonstrate why skipping steps could harm patient
```

### What Students Should Learn:

**Critical Medical Concepts:**

1. **Sequential Diagnosis**: Can't jump to treatment without systematic evaluation
2. **Dependency Chain**: Each finding determines what to investigate next
3. **Safety First**: Rule out life threats before detailed evaluation
4. **Build Progressive Picture**: Each test adds to diagnostic clarity
5. **Skip Steps = Miss Diagnoses**: Systematic approach prevents errors

**Real-World Impact:**

**Without Least-to-Most (Jumping to Conclusions):**
- See fever + surgical site redness → Assume surgical site infection
- Start antibiotics + local wound care
- Miss intra-abdominal abscess
- Patient deteriorates → Sepsis → ICU → Bad outcome

**With Least-to-Most (Systematic):**
- Step 1: Rule out sepsis/life threats → Patient stable
- Step 2: Evaluate site → Mild inflammation, not classic SSI
- Step 3: CT imaging (informed by Step 2) → Find small abscess
- Step 4: Systemic causes evaluated → Ruled out
- Step 5: Treat abscess appropriately → Good outcome

---

## How to Write Effective Least-to-Most Prompts

### Template Structure:

```
Context: [Complex problem with sequential dependencies]

Objective: Use Least-to-Most approach to break down [problem] into 
sequential sub-problems, solve each in dependency order where each 
solution builds on and enables the next.

Style: Sequential problem-solving showing: (1) decomposition and 
dependency analysis, (2) solving each sub-problem building on previous, 
(3) integration into complete solution.

Tone: [Systematic and strategic]

Audience: [Who needs to implement sequentially]

Response Format:

═══════════════════════════════════════════════════════════════════════
PHASE 1: PROBLEM DECOMPOSITION & DEPENDENCY ANALYSIS
═══════════════════════════════════════════════════════════════════════

Complex Problem: [State problem]

Sub-Problems:
1. [Foundation - no dependencies]
2. [Depends on #1]
3. [Depends on #1,2]
4. [Depends on #1,2,3]
5. [Depends on all previous]

Dependency Explanation:
[Why this order is required]

═══════════════════════════════════════════════════════════════════════
PHASE 2: SEQUENTIAL PROBLEM SOLVING
═══════════════════════════════════════════════════════════════════════

SUB-PROBLEM 1: [Foundation]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[Analysis and solution]
Why This Enables #2: [Explanation]

SUB-PROBLEM 2: [Depends on #1]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
How This Builds on #1: [Explicit dependency]
[Analysis and solution using #1]
Why This Enables #3: [Explanation]

[Continue for all sub-problems]

═══════════════════════════════════════════════════════════════════════
PHASE 3: INTEGRATED SOLUTION
═══════════════════════════════════════════════════════════════════════

Dependency Chain: 
#1 enables → #2 enables → #3 enables → #4 enables → #5

Complete Solution:
[How all solutions work together]

Why Sequential Order Matters:
[What happens if you skip steps]

---

[Provide all problem data]

Use Least-to-Most to:
1. Decompose with dependencies
2. Order by what must come first
3. Solve sequentially, each building on previous
4. Integrate into complete solution
```

### Critical Elements:

1. **Explicit Dependency Analysis**: Must show WHY order matters
2. **"Builds On" Statements**: Each sub-problem explicitly references previous
3. **"Enables Next" Statements**: Show how solution makes next step possible
4. **Sequential Progress Metrics**: Track improvement at each stage
5. **Integration Section**: Show complete solution with dependency chain

---

## Common Mistakes Students Make

### Mistake 1: Sub-Problems Not Truly Sequential
❌ **Bad:** Five independent problems that could be solved in any order
✓ **Good:** Each problem DEPENDS on previous solution being complete

### Mistake 2: No Explicit Dependencies
❌ **Bad:** "Do Step 1, then Step 2, then Step 3" (no explanation why)
✓ **Good:** "Step 2 depends on Step 1 because we need simplified form before adding shipping calculator"

### Mistake 3: Skipping Integration
❌ **Bad:** Solve 5 sub-problems, then stop
✓ **Good:** Show how all 5 solutions work together as complete solution

### Mistake 4: Wrong Ordering
❌ **Bad:** Try to optimize mobile before fixing desktop
✓ **Good:** Fix desktop first (foundation), then apply to mobile

### Mistake 5: No "Why Order Matters" Explanation
❌ **Bad:** Just present sequence without justification
✓ **Good:** "If you try to add trust badges before simplifying form, there's no space and it adds clutter"

---

## Practice Exercises

### Exercise 1: E-Commerce Return Processing System

**Scenario:**
Your return process takes 14 days and costs $45 per return (processing + shipping). Industry average: 7 days, $28. You lose customers due to slow returns.

**Issues:**
- Manual return approval (delays 3 days)
- Customers ship to wrong facility (delays 4 days)
- No automated refund triggers (delays 2 days)
- Customer service overload (delays 2-3 days)
- No return analytics to prevent returns

**Your Task:**
Write a Least-to-Most COSTAR prompt that:
1. Decomposes into 5 sequential sub-problems
2. Shows dependencies (e.g., can't automate refunds before fixing routing)
3. Solves each building on previous
4. Achieves target: 7 days, $28 cost

### Exercise 2: Healthcare Sepsis Protocol Implementation

**Scenario:**
Hospital needs to implement sepsis early recognition and treatment protocol. Current mortality: 25%, target: <10% (with proper protocol).

**Components Needed:**
- Screening criteria (identify at-risk patients)
- Alert system (notify team)
- Treatment bundles (what to do)
- Monitoring protocol (track response)
- Quality metrics (measure improvement)

**Your Task:**
Write a Least-to-Most COSTAR prompt that:
1. Decomposes into sequential implementation steps
2. Shows dependencies (e.g., can't have alerts without screening criteria)
3. Each step enables next step
4. Complete protocol that saves lives

---

## Summary

### Key Takeaways:

1. ✓ **Least-to-Most = Sequential Decomposition**
   - Break complex problem into sub-problems
   - Order by dependency (what must come first)
   - Solve sequentially, each building on previous
   - Integrate into complete solution

2. ✓ **Three-Phase Structure:**
   - Phase 1: Decomposition & dependency analysis
   - Phase 2: Sequential solving (each sub-problem)
   - Phase 3: Integration (complete solution)

3. ✓ **Dependencies Are Critical:**
   - Must explicitly show WHY order matters
   - Each solution enables the next one
   - Cannot skip steps
   - Wrong order = failure

4. ✓ **Proper COSTAR Prompts Must:**
   - Show explicit dependency analysis
   - Use "Builds On" and "Enables" statements
   - Track progress metrics at each stage
   - Explain what happens if steps are skipped
   - Present integrated final solution

5. ✓ **Essential for Sequential Problems:**
   - E-commerce: Multi-stage optimizations
   - Healthcare: Diagnostic workups, protocol implementation
   - Anywhere later steps depend on earlier steps

### Remember:
**You can't skip steps in a staircase.**
**Each solution is the foundation for the next.**

In e-commerce, Least-to-Most prevents wasted effort optimizing wrong things first.
In healthcare, Least-to-Most prevents missing critical diagnoses by ensuring systematic evaluation.

---

## Next Steps

1. Practice identifying dependencies in complex problems
2. Try decomposing a problem into proper sequence
3. Explicitly state how each solution enables next
4. See what happens when you try wrong order
5. Move on to Generated Knowledge Prompting (next technique)

Master the art of sequential problem-solving! 📈
