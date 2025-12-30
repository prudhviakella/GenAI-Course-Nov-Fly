# Tree-of-Thought (ToT) Prompting - Complete Guide

## What is Tree-of-Thought Prompting?

Tree-of-Thought (ToT) prompting breaks complex problems into a hierarchical structure, like branches of a tree. Each main question branches into sub-questions, which may branch further, creating a complete decision tree.

### Visual Representation:

```
Main Problem (Root)
├── Branch 1: First Major Factor
│   ├── Sub-branch 1.1: Specific aspect
│   ├── Sub-branch 1.2: Another aspect
│   └── Sub-branch 1.3: Third aspect
├── Branch 2: Second Major Factor
│   ├── Sub-branch 2.1: Specific aspect
│   └── Sub-branch 2.2: Another aspect
└── Branch 3: Third Major Factor
    └── Sub-branch 3.1: Specific aspect
```

### Think of it like this:

**Regular thinking (linear):**
```
Problem → Solution
```

**Chain-of-Thought (sequential):**
```
Problem → Step 1 → Step 2 → Step 3 → Solution
```

**Tree-of-Thought (hierarchical):**
```
                Problem
               /    |    \
          Factor1  Factor2  Factor3
           / \      /  \      |
        1.1 1.2   2.1 2.2    3.1
                   ↓
              Synthesize all branches → Solution
```

---

## Why Use Tree-of-Thought?

### Benefits:

1. **Handles Complex Problems** - Multiple interrelated factors
2. **Systematic Exploration** - No aspect gets overlooked
3. **Shows Relationships** - How factors connect and influence each other
4. **Better Decision Making** - All angles considered before conclusion
5. **Collaborative Analysis** - Team can examine different branches

### When to Use ToT:

✓ **Use ToT when:**
- Problem has multiple causes
- Factors are interrelated
- Need comprehensive analysis
- Strategic decision required
- Root cause analysis needed
- Multiple stakeholders involved

✗ **Don't use ToT when:**
- Problem is simple or linear
- Single-factor issue
- Quick decision needed
- Chain-of-Thought is sufficient
- Problem doesn't have sub-components

---

## Difference from Chain-of-Thought

| Aspect | Chain-of-Thought | Tree-of-Thought |
|--------|------------------|-----------------|
| **Structure** | Linear, sequential | Hierarchical, branching |
| **Best for** | Step-by-step calculations | Multi-factor analysis |
| **Example** | Math problem | Root cause analysis |
| **Output** | Step 1 → Step 2 → Step 3 | Branch 1, Branch 2, Branch 3 → Synthesis |
| **Complexity** | Simple to moderate | Moderate to complex |

**Simple rule:** If problem goes "step-by-step" use CoT. If problem has "multiple aspects" use ToT.

---

## Example 1: E-Commerce - Customer Churn Analysis

### Business Problem:
Premium subscription customers are canceling at 15% per month (up from 8%). Need to understand why and recommend fixes.

### Why ToT Helps:
- Multiple potential causes (price, quality, competition)
- Factors interact (price + quality decline = worse than either alone)
- Need comprehensive solution addressing all causes
- Stakeholders need to see complete analysis

### COSTAR Prompt:

```
Context: Analyzing a complex e-commerce customer churn problem requiring 
multi-factor consideration.

Objective: Determine why premium customers are canceling subscriptions and 
recommend retention strategies.

Style: Use tree-of-thought analysis to systematically explore each contributing 
factor and their interrelationships.

Tone: Strategic and analytical, like a management consultant presenting findings.

Audience: Executive leadership team making strategic decisions.

Response Format: Structure as a decision tree with main question → sub-questions → 
analysis → synthesis → final recommendations.

---

Main Question: Why are premium customers churning at 15% monthly (up from 8%)?

Use tree-of-thought technique to analyze:

Available Data:
- Churn increased after price change (from $29 to $39/month)
- Customer support wait times increased from 2 to 7 minutes
- Competitor launched similar service at $25/month
- App rating dropped from 4.6 to 4.2 stars
- 60% of churned customers cited "cost" as primary reason
- 40% mentioned "service quality concerns"
- Exit survey themes: "Not worth it anymore", "Better alternatives exist"

Break this down into a tree structure and provide recommendations.
```

### Expected AI Response:

```
TREE-OF-THOUGHT ANALYSIS: Premium Customer Churn

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ROOT QUESTION: Why Did Churn Increase from 8% to 15%?
(7 percentage point increase = 87.5% increase in churn rate)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

┌─────────────────────────────────────────────────────────────┐
│ BRANCH 1: PRICING FACTORS                                   │
└─────────────────────────────────────────────────────────────┘

├── Sub-question 1.1: Is $39 price point competitive?
│   │
│   ├── Analysis:
│   │   • Our price: $39/month
│   │   • Competitor price: $25/month
│   │   • Price difference: $14/month = 36% cheaper competitor
│   │   • Annual difference: $168/year
│   │
│   ├── Customer Perspective:
│   │   • 60% cited "cost" as primary reason
│   │   • Exit survey: "Not worth it anymore"
│   │   • Price sensitivity confirmed
│   │
│   └── FINDING: Price is 36% higher than main competitor
│       Impact Level: HIGH (directly cited by 60% of churners)
│
└── Sub-question 1.2: Did value perception justify the increase?
    │
    ├── Analysis:
    │   • Price increased 34% ($29 → $39)
    │   • But app quality DECREASED (4.6 → 4.2 stars)
    │   • Timing: Price up + Quality down = worst combination
    │
    ├── Value Equation:
    │   • Before: $29 for 4.6-star experience = $6.30 per star
    │   • After: $39 for 4.2-star experience = $9.29 per star
    │   • Value per dollar: DECREASED by 47%
    │
    └── FINDING: Value proposition weakened significantly
        Impact Level: CRITICAL (price + quality moved wrong direction)


┌─────────────────────────────────────────────────────────────┐
│ BRANCH 2: SERVICE QUALITY FACTORS                           │
└─────────────────────────────────────────────────────────────┘

├── Sub-question 2.1: What caused support wait time increase?
│   │
│   ├── Analysis:
│   │   • Wait time: 2 min → 7 min (250% increase)
│   │   • 40% mentioned "service quality concerns"
│   │   • Customer base likely grew, but support didn't scale
│   │
│   ├── Impact Assessment:
│   │   • Industry standard: <3 minutes for premium service
│   │   • Our performance: 7 minutes (2.3x worse than standard)
│   │   • Premium customers expect fast support
│   │
│   ├── Root Cause:
│   │   • Support team capacity didn't grow with user base
│   │   • Under-resourced department
│   │
│   └── FINDING: Support team under-resourced for current scale
│       Impact Level: HIGH (premium customers expect premium support)
│
└── Sub-question 2.2: What caused app rating drop?
    │
    ├── Analysis:
    │   • Rating drop: 4.6 → 4.2 (0.4 point decrease)
    │   • In app store terms, this is significant
    │   • Likely related to recent update
    │
    ├── User Feedback Themes:
    │   • "App crashes more now"
    │   • "Slower than before"
    │   • "Features don't work as well"
    │
    ├── Technical Assessment:
    │   • Recent major update had performance issues
    │   • Technical debt accumulated
    │   • Testing insufficient before release
    │
    └── FINDING: Technical quality declined, UX degraded
        Impact Level: MEDIUM-HIGH (affects daily usage)


┌─────────────────────────────────────────────────────────────┐
│ BRANCH 3: COMPETITIVE FACTORS                               │
└─────────────────────────────────────────────────────────────┘

└── Sub-question 3.1: How differentiated is our offering?
    │
    ├── Analysis:
    │   • Competitor launched at $25/month (36% cheaper)
    │   • Feature comparison: ~90% feature parity
    │   • Our advantages: Longer track record, larger user base
    │   • Their advantages: Price, newer technology
    │
    ├── Differentiation Assessment:
    │   • Weak competitive moat
    │   • Features can be replicated
    │   • Price is main differentiator (and we're losing)
    │   • Quality was our differentiator (but we're losing that too)
    │
    ├── Market Position:
    │   • Before: Premium option with premium quality
    │   • After: Premium price WITHOUT premium quality
    │   • Competitor: Good quality at value price
    │
    └── FINDING: Lost differentiation advantage
        Impact Level: HIGH (customers have viable alternative)


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SYNTHESIS: How Branches Interact
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

The 15% churn is NOT caused by a single factor, but by a PERFECT STORM:

1. Timing Disaster:
   Branch 1 + Branch 2 = Raised price WHILE quality declined
   
2. Competitive Pressure:
   Branch 3 = Competitor offered alternative at exact wrong moment
   
3. Value Destruction:
   All branches combined = Customers paying MORE for LESS
   
4. Trust Erosion:
   Customers feel betrayed: "Paid more, got worse service"

OVERALL ROOT CAUSE:
Poor strategic timing + operational execution failures + competitive threat
= 87.5% increase in churn rate

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
RECOMMENDATIONS (Priority Order)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

IMMEDIATE (Week 1):
1. Pricing Decision (addresses Branch 1)
   Options:
   a) Roll back to $35 (compromise position)
   b) Keep $39 BUT add 3+ premium features to justify
   c) Offer $29 "loyalty price" to at-risk customers
   
   RECOMMENDATION: Option (a) - Roll back to $35
   Rationale: Quick fix, admits error, shows customer focus

2. Support Capacity (addresses Branch 2.1)
   Action: 3x support team size immediately
   Cost: ~$180K/year
   Benefit: Reduce wait time from 7 min → 2.5 min
   ROI: Save 5% churn = ~$500K/year revenue retained

WEEK 2-4:
3. App Performance (addresses Branch 2.2)
   Action: Emergency sprint to fix critical performance issues
   Focus: Top 10 crashes, slowest screens
   Goal: Improve rating from 4.2 → 4.4 within 30 days

MONTH 2:
4. Differentiation Features (addresses Branch 3)
   Action: Launch 2-3 features competitor doesn't have
   Examples: 
   - Advanced analytics dashboard
   - API integrations
   - White-label options
   Goal: Create switching costs

MONTH 3:
5. Win-Back Campaign
   Target: Customers who churned in last 60 days
   Offer: $29/month for 6 months + apology
   Expected: 15-25% return rate

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PROJECTED IMPACT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Current State:
- Monthly churn: 15%
- Monthly cost of churn: ~$450K (3,000 customers × $150 LTV lost)

After Recommendations:
- Expected churn: 9% (below original 8%, momentum effect)
- Monthly cost of churn: ~$270K
- Monthly savings: $180K
- Annual savings: $2.16M

Investment Required:
- Support team: $180K/year
- Development sprint: $50K one-time
- Win-back campaign: $75K one-time
- Total Year 1: $305K

Net Benefit Year 1: $2.16M - $305K = $1.86M

ROI: 609%
```

### What Students Should Learn:

**Key Concepts:**

1. **Hierarchical Thinking**: Break main question into major branches
2. **Sub-Analysis**: Each branch has sub-questions
3. **Interaction Effects**: How branches combine matters
4. **Synthesis**: Bring all branches together for complete picture
5. **Prioritization**: Not all branches are equally important

**Why ToT is Better Than Linear Analysis:**

Linear thinking might conclude: "Price increased, customers left"
ToT reveals: "Price + quality decline + competition + bad timing = perfect storm"

The second analysis leads to much better solutions!

---

## Example 2: Healthcare - Diagnostic Differential

### Medical Problem:
Patient with severe headache - need to determine most likely diagnosis among multiple possibilities.

### Why ToT is CRITICAL Here:

⚠️ **LIFE-THREATENING CONDITIONS MUST BE RULED OUT** ⚠️
- Missing a serious diagnosis can be fatal
- Must systematically evaluate all possibilities
- Different conditions require different urgent actions
- Multiple symptoms can point to different diagnoses

### COSTAR Prompt:

```
Context: Emergency department diagnostic decision-making where multiple serious 
conditions must be systematically evaluated.

Objective: Arrive at the most likely diagnosis by systematically exploring all 
possibilities in a tree structure.

Style: Reason like an emergency physician considering a complete differential 
diagnosis.

Tone: Methodical and evidence-based, prioritizing life-threatening conditions.

Audience: Healthcare team in emergency department.

Response Format: Build diagnostic tree → evaluate each branch with clinical 
reasoning → synthesize to most likely diagnosis → recommend immediate actions.

---

PATIENT PRESENTATION:

Chief Complaint: "Worst headache of my life"

Vital Signs & Physical:
- 45-year-old male
- BP: 165/95 (baseline usually 130/80)
- HR: 88 bpm
- Temp: 98.6°F (37°C)
- Alert and oriented (GCS 15)
- No focal neurological deficits

History:
- Acute onset 2 hours ago (sudden, reached peak in seconds)
- No prior history of migraines or severe headaches
- Mild neck stiffness
- Photophobia (light sensitivity)
- Nausea (vomited once)

Use tree-of-thought to build differential diagnosis and determine most likely cause.
```

### Expected AI Response:

```
EMERGENCY DIAGNOSTIC TREE-OF-THOUGHT ANALYSIS

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ROOT QUESTION: What is causing "worst headache of life"?
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

CRITICAL CONTEXT: "Worst headache of life" = MUST RULE OUT LIFE-THREATS FIRST

┌─────────────────────────────────────────────────────────────┐
│ BRANCH 1: VASCULAR CAUSES (LIFE-THREATENING)               │
│ Priority: HIGHEST - Must rule out immediately              │
└─────────────────────────────────────────────────────────────┘

├── Sub-branch 1.1: Subarachnoid Hemorrhage (SAH)
│   │
│   ├── Supporting Evidence:
│   │   • "Worst headache of life" (classic SAH descriptor) ✓✓✓
│   │   • Sudden onset, peaked instantly (thunderclap) ✓✓✓
│   │   • Neck stiffness (meningeal irritation) ✓✓
│   │   • Photophobia (meningeal irritation) ✓✓
│   │   • Nausea/vomiting ✓
│   │   • No prior migraine history ✓
│   │
│   ├── Against Evidence:
│   │   • Normal temperature (no fever)
│   │   • Alert and oriented (no decreased consciousness)
│   │   • No focal deficits (no stroke symptoms)
│   │   BUT: SAH can present this way in early stages
│   │
│   ├── Clinical Reasoning:
│   │   • SAH from ruptured aneurysm presents exactly like this
│   │   • "Thunderclap headache" = SAH until proven otherwise
│   │   • Neck stiffness + photophobia = blood in CSF irritating meninges
│   │   • Can have normal neuro exam initially
│   │
│   ├── Risk Stratification:
│   │   • If SAH and missed: FATAL (patient dies or severe disability)
│   │   • If SAH and caught: Treatable (neurosurgery can repair)
│   │   • CANNOT AFFORD TO MISS THIS
│   │
│   └── FINDING: SAH is MOST LIKELY diagnosis
│       Probability: 70-80%
│       Urgency: STAT workup required
│
└── Sub-branch 1.2: Hypertensive Crisis
    │
    ├── Supporting Evidence:
    │   • BP elevated: 165/95 (vs baseline 130/80) ✓
    │   • Severe headache ✓
    │
    ├── Against Evidence:
    │   • BP not severely elevated (not >180/120)
    │   • No other end-organ damage signs
    │   • Pattern more consistent with SAH
    │   • BP elevation could be SECONDARY to SAH pain
    │
    ├── Clinical Reasoning:
    │   • Elevated BP common with severe pain
    │   • Would expect BP >180/120 for primary hypertensive headache
    │   • Lack of other hypertensive emergency signs
    │
    └── FINDING: Hypertensive crisis UNLIKELY as primary cause
        Probability: 10-15%
        More likely: BP elevated due to pain from SAH


┌─────────────────────────────────────────────────────────────┐
│ BRANCH 2: INFECTIOUS CAUSES                                 │
│ Priority: HIGH - Also life-threatening if present           │
└─────────────────────────────────────────────────────────────┘

├── Sub-branch 2.1: Bacterial Meningitis
│   │
│   ├── Supporting Evidence:
│   │   • Neck stiffness ✓
│   │   • Photophobia ✓
│   │   • Severe headache ✓
│   │
│   ├── Against Evidence:
│   │   • NO fever (temp 98.6°F) ✗✗✗
│   │   • Alert and oriented (usually altered in meningitis) ✗
│   │   • Acute onset in seconds (meningitis develops over hours) ✗
│   │   • No classic meningitis triad (fever, neck stiffness, altered mental status)
│   │
│   ├── Clinical Reasoning:
│   │   • Bacterial meningitis almost always has fever
│   │   • Usually progressive onset, not sudden
│   │   • Would expect more systemic signs
│   │
│   └── FINDING: Bacterial meningitis UNLIKELY
│       Probability: <5%
│       Note: Still need to rule out with LP if CT negative for SAH
│
└── Sub-branch 2.2: Viral Meningitis
    │
    ├── Analysis:
    │   • Same reasoning as bacterial, but less severe
    │   • Still would expect fever
    │   • Gradual onset more typical
    │
    └── FINDING: Viral meningitis UNLIKELY
        Probability: <5%


┌─────────────────────────────────────────────────────────────┐
│ BRANCH 3: PRIMARY HEADACHE DISORDERS                        │
│ Priority: LOWER - Not immediately life-threatening          │
└─────────────────────────────────────────────────────────────┘

└── Sub-branch 3.1: Migraine (First Episode)
    │
    ├── Supporting Evidence:
    │   • Photophobia ✓
    │   • Nausea/vomiting ✓
    │   • Severe pain ✓
    │
    ├── Against Evidence:
    │   • "Worst headache of life" (too severe for typical first migraine) ✗✗
    │   • Thunderclap onset (migraines build gradually) ✗✗
    │   • Age 45 with no prior migraines (unusual for first episode) ✗
    │   • Neck stiffness (not typical for migraine) ✗
    │
    ├── Clinical Reasoning:
    │   • First migraine at 45 is possible but unusual
    │   • Instant onset is NOT characteristic of migraine
    │   • "Thunderclap" pattern rules out migraine
    │   • Cannot diagnose migraine without ruling out SAH first
    │
    └── FINDING: Migraine UNLIKELY
        Probability: <10%
        Action: Cannot assume benign headache without imaging


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SYNTHESIS: Integration of All Branches
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

COMPARING ALL POSSIBILITIES:

| Diagnosis | Probability | Evidence Strength | Risk if Missed |
|-----------|-------------|-------------------|----------------|
| SAH | 70-80% | Very Strong | FATAL |
| Hypertensive Crisis | 10-15% | Weak | Serious |
| Meningitis | <5% | Weak | FATAL |
| Migraine | <10% | Very Weak | Low |

CLINICAL DECISION RULE:
"Thunderclap headache" + "worst headache of life" = SAH until proven otherwise

SUPPORTING SYNTHESIS:
- Branch 1 (Vascular): STRONG evidence for SAH
- Branch 2 (Infectious): Unlikely due to lack of fever
- Branch 3 (Primary): Cannot diagnose without ruling out SAH

INTERACTION OF FINDINGS:
- Neck stiffness + Photophobia = Meningeal irritation
  → Could be meningitis OR blood in CSF (SAH)
  → NO fever makes SAH much more likely
  
- Elevated BP + Severe pain = 
  → Primary hypertensive crisis OR
  → Secondary BP elevation from SAH pain
  → Pattern favors secondary elevation

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FINAL DIAGNOSIS (WORKING)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

PRIMARY DIAGNOSIS: Subarachnoid Hemorrhage (SAH)

CONFIDENCE LEVEL: HIGH (70-80% probability)

REASONING:
1. Classic presentation of "thunderclap headache"
2. "Worst headache of life" is specific for SAH
3. Neck stiffness + photophobia = meningeal irritation from blood
4. No fever makes infection unlikely
5. Sudden onset rules out migraine
6. Cannot afford to miss this diagnosis

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
IMMEDIATE ACTIONS (PRIORITY ORDER)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚠️  STAT ORDERS (DO NOT DELAY):

1. NON-CONTRAST HEAD CT (Priority: STAT - within 15 minutes)
   Purpose: Detect blood in subarachnoid space
   Sensitivity: 95-98% within first 6 hours
   
2. NPO STATUS (Nothing by mouth)
   Reason: May need emergency surgery
   
3. NEUROSURGERY CONSULTATION (Call now, before imaging)
   Reason: Need immediate availability if SAH confirmed
   
4. IV ACCESS × 2 (Two large-bore IVs)
   Reason: Prepare for emergency interventions
   
5. BLOOD PRESSURE MANAGEMENT
   Goal: 140-160 systolic (prevent rebleed but maintain cerebral perfusion)
   Avoid: Aggressive BP lowering (can worsen brain injury)
   
6. CONTINUOUS MONITORING
   Neuro checks: Every 15 minutes
   Watch for: Decreased consciousness, new deficits

IF CT IS NEGATIVE:
7. LUMBAR PUNCTURE (LP)
   Timing: If CT at >6 hours, LP may be needed
   Purpose: Detect xanthochromia (blood breakdown products)
   
IF CT IS POSITIVE (SAH confirmed):
8. CT ANGIOGRAPHY or CONVENTIONAL ANGIOGRAPHY
   Purpose: Identify aneurysm location
   
9. IMMEDIATE NEUROSURGICAL INTERVENTION
   Options: Surgical clipping vs endovascular coiling
   
10. ICU ADMISSION
    For: Close monitoring, prevent complications

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CRITICAL TEACHING POINTS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. "Worst headache of life" is SAH until proven otherwise
2. Cannot diagnose benign headache without imaging first
3. Tree-of-Thought ensures you don't miss life threats
4. Systematic evaluation of ALL branches prevents errors
5. Time is brain - SAH can rebleed at any moment
```

### What Students Should Learn:

**Critical Medical Concepts:**

1. **Life-Threat Priority**: Always rule out deadly conditions first
2. **Systematic Thinking**: Tree structure ensures nothing is missed
3. **Evidence Weighing**: Some findings are more important than others
4. **Cannot Assume**: "Probably just a headache" kills patients
5. **Time Sensitivity**: Some diagnoses need immediate action

**Why ToT is Essential in Emergency Medicine:**

- ❌ **Without ToT**: Might jump to "migraine" and send patient home → Patient dies
- ✓ **With ToT**: Systematically rule out SAH, meningitis, etc. → Catch SAH, save life

**Real-World Impact:**
- Missing SAH has 40-50% mortality
- Tree-of-Thought prevents these misses
- Every branch must be evaluated
- Cannot skip "unlikely" possibilities when they're deadly

---

## Comparison: E-Commerce vs Healthcare ToT

| Aspect | E-Commerce Example | Healthcare Example |
|--------|-------------------|-------------------|
| **Main Question** | Why is churn increasing? | What's causing the headache? |
| **Branches** | Pricing, Quality, Competition | Vascular, Infectious, Primary |
| **Stakes** | Revenue loss | Life or death |
| **Synthesis** | Business recommendation | Medical diagnosis |
| **Timeline** | Days to weeks | Minutes to hours |
| **Error Cost** | Lost customers | Lost lives |

**Both use same ToT structure, but medical has zero margin for error.**

---

## How to Build a Tree-of-Thought Prompt

### Template:

```
Context: [Why this needs multi-factor analysis]

Objective: [What complete picture you need]

Style: Tree-of-thought analysis exploring all major factors

Tone: [Analytical, strategic, clinical, etc.]

Audience: [Who needs this comprehensive analysis]

Response Format: Main question → Branch 1 (sub-branches) → Branch 2 
(sub-branches) → Branch 3 (sub-branches) → Synthesis → Recommendations

---

Main Question: [Your complex problem]

Data Available:
[All relevant information]

Use tree-of-thought to systematically analyze.
```

### Building Your Tree:

**Step 1: Identify Main Branches**
What are the 3-5 major factors?

**Step 2: Create Sub-Branches**
What specific aspects exist under each main branch?

**Step 3: Analyze Each Branch**
What does evidence say about each factor?

**Step 4: Synthesize**
How do all branches interact?

**Step 5: Recommend**
What actions follow from complete analysis?

---

## Common Mistakes Students Make

### Mistake 1: Too Many Branches
❌ **Bad:** 10 main branches with 5 sub-branches each = 50 factors
✓ **Good:** 3-5 main branches with 2-4 sub-branches each

### Mistake 2: Not Synthesizing
❌ **Bad:** Analyze each branch separately, then stop
✓ **Good:** Show how branches interact and combine

### Mistake 3: Ignoring Branch Priority
❌ **Bad:** Treat all branches equally
✓ **Good:** In medical, life-threats first. In business, highest impact first.

### Mistake 4: Linear Thinking
❌ **Bad:** Force sequential analysis into tree format
✓ **Good:** Use true hierarchical thinking - factors at same level

### Mistake 5: Incomplete Branches
❌ **Bad:** Develop only the branches that seem important
✓ **Good:** Systematically evaluate ALL branches before concluding

---

## Practice Exercises

### Exercise 1: E-Commerce Product Launch Failure

**Problem:**
New product launched 3 months ago. Sales are 40% below projection.

**Data:**
- Marketing spend on target
- Product reviews: 3.8 stars (expected 4.5+)
- Competitor launched similar product 2 weeks before us
- Our price: $89, Competitor: $79
- Customer complaints: "Doesn't work as advertised", "Confusing to use"

**Task:** Build tree-of-thought analysis with branches for:
- Product Quality
- Pricing/Competition
- Marketing Effectiveness
- Customer Experience

### Exercise 2: Healthcare Post-Surgical Complication

**Problem:**
Patient 2 days post-appendectomy. Now has fever and abdominal pain.

**Data:**
- Temp: 101.5°F
- Wound looks clean
- Pain at incision site: 7/10
- WBC: 14,000 (elevated)
- Patient ate breakfast this morning

**Task:** Build diagnostic tree with branches for:
- Surgical Site Infection
- Intra-Abdominal Abscess
- Pneumonia (post-op)
- Other Post-Op Complications

---

## Summary

### Key Takeaways:

1. ✓ **Tree-of-Thought = Hierarchical Analysis**
   - Main question branches into major factors
   - Each factor branches into specific aspects
   - All branches synthesized for complete picture

2. ✓ **Use ToT for:**
   - Multi-factor problems
   - Root cause analysis
   - Complex decision making
   - Strategic planning
   - Differential diagnosis

3. ✓ **Structure:**
   - Main Question (root)
   - Branch 1, 2, 3... (major factors)
   - Sub-branches (specific aspects)
   - Synthesis (how factors interact)
   - Recommendations (what to do)

4. ✓ **Critical in Healthcare:**
   - Prevents missing life-threatening diagnoses
   - Ensures systematic evaluation
   - Documents clinical reasoning
   - Team can review all branches

5. ✓ **Difference from CoT:**
   - CoT: Linear, step-by-step
   - ToT: Hierarchical, multi-factor
   - Use CoT for calculations, ToT for analysis

### Remember:
**In e-commerce, ToT prevents incomplete analysis leading to wrong strategy.**
**In healthcare, ToT prevents missed diagnoses leading to patient death.**

---

## Next Steps

1. Practice with the exercises above
2. Try building your own trees for complex problems
3. Compare ToT analysis to linear thinking
4. See which catches more factors
5. Move on to Self-Consistency prompting (next technique)

---

**Self-Assessment Questions:**

1. When should you use Tree-of-Thought vs Chain-of-Thought?
2. How many main branches should a good tree have?
3. What's the difference between a branch and sub-branch?
4. Why is synthesis critical in ToT?
5. In medical diagnosis, which branches get priority?

Master these concepts before moving to the next technique! 🌳
