# Maieutic Prompting - Complete Guide

## What is Maieutic Prompting?

Maieutic prompting is the Socratic method applied to AI. Named after Socrates' technique of teaching through questioning, you ask the AI to explain something, then systematically question each component of that explanation, drilling down through multiple levels until you uncover hidden assumptions, logical gaps, or inconsistencies.

### Think of it like this:

**Regular Prompting:**
```
Question → Answer → Done
```

**Maieutic Prompting (Socratic Method):**
```
Question → Initial Answer
  ↓
Question Part 1 of Answer → Explanation
  ↓
Question Assumptions in Explanation → Deeper Analysis
  ↓
Find Inconsistencies → Resolve Them
  ↓
Refined, Validated Answer
```

---

## Why Use Maieutic Prompting?

### Benefits:

1. **Uncovers Hidden Assumptions** - Reveals what the reasoning takes for granted
2. **Finds Logical Inconsistencies** - Discovers contradictions in the logic
3. **Deepens Understanding** - Forces thorough explanation at every level
4. **Tests Reasoning Quality** - Validates whether conclusions are sound
5. **Improves Recommendations** - Produces better final answers through iteration

### When to Use Maieutic Prompting:

✓ **Use when:**
- Validating complex recommendations
- Checking AI reasoning for flaws
- Need to understand "why" at a deep level
- Recommendations seem counterintuitive
- Stakes are high and reasoning must be sound

✗ **Don't use when:**
- Need quick factual answers
- Question is simple and straightforward
- Time is critical
- Answer doesn't require reasoning validation

---

## How It Works

### The Multi-Level Questioning Process:

**Level 1:** Get initial explanation
**Level 2:** Question each component of that explanation
**Level 3:** Question the assumptions underlying Level 2 explanations
**Level 4:** Identify inconsistencies revealed by questioning
**Level 5:** Resolve inconsistencies and produce refined answer

This creates a "question tree" that systematically validates reasoning.

---

## Example 1: E-Commerce - Validating Recommendation System Logic

### Business Problem:
Your recommendation system suggested a $1,200 high-end TV to a user who consistently browses "budget gaming" content. Marketing team asks: "Why did the system recommend this? It seems wrong."

### Why Maieutic Prompting Helps:
- Recommendation seems counterintuitive (budget user, premium product)
- Need to validate the AI's reasoning
- Must find where logic went wrong
- Improve system to prevent future mismatches

### COSTAR Prompt (Maieutic Structure):

```
Context: We need to validate the reasoning behind a recommendation system's 
decision that appears counterintuitive. A recommendation engine suggested a 
$1,200 TV to a budget-conscious gaming user, and we need to understand if 
this logic is sound or flawed.

Objective: Use Maieutic (Socratic) questioning to systematically examine 
the recommendation logic, question each assumption, and identify any 
inconsistencies or flaws in the reasoning.

Style: Socratic dialogue format - provide explanation, then question each 
component of that explanation, drilling down through multiple levels until 
we uncover the root logic and any flaws.

Tone: Analytical and questioning, like a teacher using Socratic method to 
help a student discover logical flaws in their own reasoning.

Audience: Product team validating recommendation algorithm logic.

Response Format:

═══════════════════════════════════════════════════════════════════════
LEVEL 1: INITIAL EXPLANATION
═══════════════════════════════════════════════════════════════════════

Question: Why did the system recommend Product X to User Y?

Initial Explanation:
[Provide the system's reasoning]

═══════════════════════════════════════════════════════════════════════
LEVEL 2: QUESTIONING EACH COMPONENT
═══════════════════════════════════════════════════════════════════════

For each part of the initial explanation, question it:

Component 1: [First part of explanation]
├─ Socratic Question: Why is this factor relevant?
├─ Deeper Explanation: [Explain the reasoning]
└─ Critical Question: What assumptions does this make?

Component 2: [Second part of explanation]
├─ Socratic Question: How does this connect to the recommendation?
├─ Deeper Explanation: [Explain the reasoning]
└─ Critical Question: Is this assumption valid for this user?

Component 3: [Third part of explanation]
├─ Socratic Question: What evidence supports this logic?
├─ Deeper Explanation: [Explain the reasoning]
└─ Critical Question: Does the data contradict this?

═══════════════════════════════════════════════════════════════════════
LEVEL 3: EXAMINING ASSUMPTIONS
═══════════════════════════════════════════════════════════════════════

For each assumption identified in Level 2, test it against evidence:

Assumption 1: [Stated or hidden assumption]
├─ Evidence For: [What supports this?]
├─ Evidence Against: [What contradicts this?]
└─ Validity: [Is assumption sound?]

Assumption 2: [Another assumption]
├─ Evidence For: [What supports this?]
├─ Evidence Against: [What contradicts this?]
└─ Validity: [Is assumption sound?]

═══════════════════════════════════════════════════════════════════════
LEVEL 4: IDENTIFYING INCONSISTENCIES
═══════════════════════════════════════════════════════════════════════

List all logical inconsistencies discovered:

INCONSISTENCY 1: [Description]
├─ Where it appears: [Which component]
├─ Why it's problematic: [Impact on recommendation]
└─ Severity: [Critical/Major/Minor]

INCONSISTENCY 2: [Description]
├─ Where it appears: [Which component]
├─ Why it's problematic: [Impact on recommendation]
└─ Severity: [Critical/Major/Minor]

═══════════════════════════════════════════════════════════════════════
LEVEL 5: REFINED UNDERSTANDING
═══════════════════════════════════════════════════════════════════════

Root Cause of Flawed Recommendation:
[What went wrong in the logic?]

Corrected Logic:
[How should the system reason instead?]

Better Recommendation:
[What should have been recommended?]

System Improvements Needed:
1. [Fix for inconsistency 1]
2. [Fix for inconsistency 2]
3. [Fix for inconsistency 3]

---

SCENARIO DATA:

Recommended Product:
- Samsung QLED 65" 4K TV
- Price: $1,199
- Features: 4K @ 120Hz, HDR, Gaming Mode, 1ms response time
- Target audience: Premium gaming enthusiasts

User Profile (User ID: 847392):
- Account age: 14 months
- Total orders: 23
- Average order value: $47
- Price range of past purchases: $15-$120
- Never purchased anything over $120

Recent Browsing History (Last 30 days):
- "Budget gaming setup under $500" (viewed 8x)
- "Best budget monitors under $200" (viewed 5x)
- "Cheap gaming accessories" (viewed 12x)
- "Is PS5 worth it Reddit discussion" (viewed 3x)
- "PS5 vs Xbox budget comparison" (viewed 2x)

Recent Purchase:
- PS5 console: $499 (financed over 4 months)
- Bought after price drop from $549
- Used promotional financing (0% APR)

Search Queries:
- "ps5 compatible tv under 400"
- "budget 4k tv for ps5"
- "cheapest tv with 120hz"
- "ps5 tv deals"

User Demographics:
- Age: 22
- Income bracket: $25K-$35K (estimated from zip code)
- Student status: College student (edu email)

Recommendation System's Stated Logic:
"User purchased PS5 which supports 4K @ 120Hz. System identified high-end 
displays that maximize PS5 capabilities. User shows interest in gaming 
performance (searched '120hz'). Premium TV recommended to enhance gaming 
experience."

Using Maieutic questioning, systematically examine this recommendation logic:
1. Question each component of the system's explanation
2. Drill down into assumptions
3. Test assumptions against user data
4. Identify all inconsistencies
5. Provide corrected logic and better recommendation
```

### Expected AI Response Structure:

```
═══════════════════════════════════════════════════════════════════════
LEVEL 1: INITIAL EXPLANATION
═══════════════════════════════════════════════════════════════════════

Question: Why did the system recommend a $1,199 TV to this budget-gaming user?

Initial Explanation from System:
"User purchased PS5 which supports 4K @ 120Hz. System identified high-end 
displays that maximize PS5 capabilities. User shows interest in gaming 
performance (searched '120hz'). Premium TV recommended to enhance gaming 
experience."

═══════════════════════════════════════════════════════════════════════
LEVEL 2: QUESTIONING EACH COMPONENT
═══════════════════════════════════════════════════════════════════════

Component 1: "User purchased PS5 which supports 4K @ 120Hz"
├─ Socratic Question: Why is PS5 capability relevant to TV recommendation?
├─ Deeper Explanation: "PS5 has advanced graphics capabilities, so system 
│  assumes user wants TV that can display those capabilities"
└─ Critical Question: Does owning a capable device mean user wants/can 
   afford premium accessories?
   
   🔍 ASSUMPTION UNCOVERED: "User who owns PS5 wants premium peripherals"

Component 2: "System identified high-end displays that maximize PS5 capabilities"
├─ Socratic Question: What makes "maximizing capabilities" the primary goal?
├─ Deeper Explanation: "Algorithm prioritizes technical feature matching - 
│  PS5 has 120Hz output, so recommend 120Hz displays"
└─ Critical Question: Should technical matching override price sensitivity 
   signals?
   
   🔍 ASSUMPTION UNCOVERED: "Technical feature matching is most important factor"

Component 3: "User shows interest in gaming performance (searched '120hz')"
├─ Socratic Question: What does searching "120hz" actually indicate?
├─ Deeper Explanation: "User searched for 120Hz, indicating they care about 
│  this feature"
└─ Critical Question: Did user search "120hz" alone or "budget 120hz"?
   
   🔍 Let's check: User's actual search was "cheapest tv with 120hz"
   🔍 ASSUMPTION UNCOVERED: "Interest in feature = willing to pay premium"

═══════════════════════════════════════════════════════════════════════
LEVEL 3: EXAMINING ASSUMPTIONS
═══════════════════════════════════════════════════════════════════════

Assumption 1: "User who owns PS5 wants premium peripherals"

├─ Evidence FOR:
│  • PS5 is $499 device (mid-to-high end)
│  • PS5 supports premium features (4K, 120Hz)
│  • Gaming enthusiasts often invest in setups
│
├─ Evidence AGAINST:
│  • User FINANCED the PS5 over 4 months (couldn't afford upfront)
│  • User bought PS5 only AFTER price drop ($549 → $499)
│  • User's average purchase: $47
│  • User's max purchase ever: $120
│  • $1,199 TV is 10x user's typical spend
│  • $1,199 TV is 24x average order value
│
└─ Validity: ❌ INVALID ASSUMPTION
   The PS5 purchase shows interest in gaming, but purchasing behavior 
   shows extreme price sensitivity. User saved $50 and needed financing.

Assumption 2: "Technical feature matching is most important factor"

├─ Evidence FOR:
│  • Feature compatibility ensures good user experience
│  • Technical match prevents buyer's remorse
│  • Many users do prioritize performance
│
├─ Evidence AGAINST:
│  • User's browsing: "budget" appears in 25/30 recent sessions
│  • User explicitly searched price-constrained queries
│  • Every single search had price qualifier ("under X", "cheap", "budget")
│  • User has NEVER purchased anything premium
│  • Price sensitivity shown consistently over 14 months
│
└─ Validity: ❌ INVALID ASSUMPTION
   While feature matching matters, it should be WITHIN user's price range.
   System completely ignored price constraints.

Assumption 3: "Interest in 120Hz = Willing to pay premium"

├─ Evidence FOR:
│  • User searched for 120Hz specifically
│  • Shows user understands technical specs
│  • Feature awareness suggests sophistication
│
├─ Evidence AGAINST:
│  • User's exact search: "cheapest tv with 120hz"
│  • Also searched: "ps5 compatible tv under 400"
│  • Also searched: "budget 4k tv for ps5"
│  • Price constraint in EVERY search
│  • User wants feature AT LOWEST PRICE POINT
│
└─ Validity: ❌ INVALID ASSUMPTION
   User wants 120Hz at budget price, not premium 120Hz at any cost.
   Critical misinterpretation of search intent.

═══════════════════════════════════════════════════════════════════════
LEVEL 4: IDENTIFYING INCONSISTENCIES
═══════════════════════════════════════════════════════════════════════

INCONSISTENCY 1: Price vs Purchase History
├─ Where it appears: Recommending $1,199 item to user with $47 AOV
├─ Why it's problematic: 
│  • Recommended price is 25.5x user's average order
│  • Recommended price is 10x user's historical maximum
│  • Zero probability of purchase at this price point
│  • Will frustrate user and damage trust
└─ Severity: CRITICAL

INCONSISTENCY 2: "Budget" Intent vs "Premium" Recommendation
├─ Where it appears: User searches "budget" but gets "premium" recommendation
├─ Why it's problematic:
│  • User explicitly stated price constraint 25+ times
│  • System completely ignored stated preferences  
│  • Recommendation contradicts user's clear intent
│  • Shows system doesn't understand context
└─ Severity: CRITICAL

INCONSISTENCY 3: Financing Behavior vs High-Price Recommendation
├─ Where it appears: User who needed 4-month financing recommended $1,199 item
├─ Why it's problematic:
│  • User couldn't afford $499 upfront (needed financing)
│  • Recommending $1,199 is 2.4x what they couldn't afford
│  • Demonstrates financial constraint, not affluence
│  • System misinterpreted financing as "willing to pay high prices"
└─ Severity: MAJOR

INCONSISTENCY 4: Feature Detection vs Context Ignorance
├─ Where it appears: System found "120Hz" search but ignored "cheapest" modifier
├─ Why it's problematic:
│  • Detected technical term but ignored price qualifier
│  • Shows system has no semantic understanding
│  • Treats "120Hz" and "cheapest 120Hz" identically
│  • Missing context completely changes intent
└─ Severity: MAJOR

═══════════════════════════════════════════════════════════════════════
LEVEL 5: REFINED UNDERSTANDING
═══════════════════════════════════════════════════════════════════════

Root Cause of Flawed Recommendation:

The recommendation system has a fundamental flaw: it performs FEATURE 
MATCHING without PRICE CONTEXT. The algorithm:

1. Detects user owns PS5 with 4K/120Hz capability
2. Searches inventory for TVs with 4K/120Hz features
3. Recommends based on feature match alone
4. IGNORES all price sensitivity signals

This is like recommending a Ferrari to someone who searched "reliable car 
for college student" - technically correct (Ferrari is reliable) but 
contextually absurd.

The system treats these as equivalent:
• "best tv for ps5" → Premium recommendation ✓
• "cheapest tv for ps5" → Premium recommendation ✗

Corrected Logic:

Step 1: Detect user purchase (PS5) ✓
Step 2: Identify compatible features needed (4K, 120Hz) ✓  
Step 3: **NEW** Analyze price sensitivity from:
   - Historical purchase range ($15-$120, avg $47)
   - Search qualifiers ("budget", "cheap", "under X")
   - Financing behavior (needed 4-month plan for $499)
   - Never purchased >$120 in 14 months
   
Step 4: **NEW** Calculate realistic price range:
   - Historical max: $120
   - Financed purchase: $499 (stretched)
   - Realistic range for TV: $300-$500 (3-5x historical, manageable stretch)
   
Step 5: Recommend WITHIN price range with desired features

Better Recommendation:

**TCL 55" 4-Series 4K TV - $380**

Why this is correct:
✓ Has required features: 4K @ 120Hz, Gaming Mode
✓ Within realistic budget: $380 (3x historical max, reasonable stretch)
✓ Matches search intent: "budget 4k tv for ps5"
✓ High conversion probability: 35-45% (vs <1% for $1,199 TV)
✓ Positive user experience: Feels understood, not pressured
✓ Alternative upsell: Offer $450 option as "premium budget" choice

Expected Outcome:
• User likely to purchase (affordable + meets needs)
• Positive brand perception (understands their constraints)
• Future purchases (trust built)
• Higher LTV (satisfied customer returns)

System Improvements Needed:

1. **Add Price Context Layer**
   - Calculate user's price range from history
   - Weight recent purchases more heavily
   - Detect financing as constraint signal
   - Build confidence bands (likely, stretch, unrealistic)

2. **Semantic Search Understanding**
   - Parse modifiers ("cheap", "budget", "under X")
   - Treat "cheapest 120hz" different from "120hz"
   - Context matters more than keyword match
   - Understand intent, not just terms

3. **Multi-Factor Ranking**
   Current: Feature match score only
   New: Feature match × Price appropriateness × Historical behavior
   
   Example:
   - $1,199 TV: Feature match = 100%, Price fit = 5%, Final = 5%
   - $380 TV: Feature match = 95%, Price fit = 90%, Final = 85.5%

4. **Constraint Respect**
   - If user searches "under $400", NEVER recommend >$400
   - Hard constraints must be absolute filters
   - Only show in-range options
   
5. **A/B Test Validation**
   - Test current vs corrected algorithm
   - Measure: Click-through rate, conversion rate, user satisfaction
   - Expected improvement: 500-1000% increase in conversion

═══════════════════════════════════════════════════════════════════════
MAIEUTIC PROMPTING SUCCESS
═══════════════════════════════════════════════════════════════════════

What Socratic questioning revealed:
✓ Found 3 invalid assumptions system made
✓ Identified 4 critical inconsistencies
✓ Discovered root cause (feature matching without price context)
✓ Developed corrected logic
✓ Proposed better recommendation ($380 vs $1,199)
✓ Defined 5 system improvements

Without Maieutic questioning, we would have accepted the system's 
explanation: "User wants 120Hz, so recommend 120Hz TV."

With Maieutic questioning, we discovered: "User wants 120Hz AT BUDGET 
PRICE, feature matching must include price context."

Conversion rate impact:
• Original recommendation: <1% conversion (wrong)
• Refined recommendation: 35-45% conversion (right)
```

### What Students Should Learn:

**Key Concepts:**

1. **Question Every Component**: Break explanation into parts, question each
2. **Multi-Level Drilling**: Don't stop at first answer, drill 3-4 levels deep
3. **Uncover Assumptions**: Find what the reasoning takes for granted
4. **Test Against Evidence**: Check if assumptions match reality
5. **Identify Inconsistencies**: Find contradictions between logic and data
6. **Resolve and Refine**: Fix the flaws to get better answer

**Why Maieutic Prompting Matters in E-Commerce:**

Without it: Accept AI's recommendation logic at face value
With it: Uncover that system ignores price sensitivity, improve by 500-1000%

---

## Example 2: Healthcare - Validating Treatment Recommendation

### Medical Problem:
AI clinical decision support system recommends immediate surgery for 58-year-old patient with knee meniscus tear. Orthopedic surgeon questions: "Why surgery now? This seems aggressive."

### Why Maieutic Prompting is CRITICAL:

⚠️ **PATIENT SAFETY DEPENDS ON REASONING VALIDATION** ⚠️
- Surgery has risks (infection, anesthesia complications, slow recovery)
- Conservative treatment often succeeds
- Need to validate AI's logic before cutting patient open
- Unjustified surgery harms patient and increases costs

### COSTAR Prompt:

```
Context: Clinical decision support AI recommended immediate surgical intervention 
for knee meniscus tear. Before proceeding with surgery, we must validate the AI's 
reasoning using Socratic questioning to ensure recommendation is sound and 
patient-appropriate.

Objective: Use Maieutic (Socratic) method to systematically examine the surgery 
recommendation, question each component of the clinical reasoning, and identify 
any flaws or gaps in the logic that could lead to unnecessary surgery.

Style: Medical Socratic dialogue - provide clinical reasoning, then question 
each element, drilling down through multiple levels of clinical decision-making 
until we validate or refute the recommendation.

Tone: Clinical and questioning, like an attending physician teaching a resident 
through Socratic method to identify flaws in clinical reasoning.

Audience: Orthopedic surgery team reviewing AI recommendation before proceeding.

Response Format:

═══════════════════════════════════════════════════════════════════════
LEVEL 1: INITIAL CLINICAL REASONING
═══════════════════════════════════════════════════════════════════════

Question: Why does the AI recommend immediate surgery for this patient?

AI's Initial Recommendation:
[State the AI's reasoning]

═══════════════════════════════════════════════════════════════════════
LEVEL 2: QUESTIONING EACH CLINICAL COMPONENT
═══════════════════════════════════════════════════════════════════════

Clinical Factor 1: [First element of reasoning]
├─ Socratic Question: What clinical principle supports this?
├─ Deeper Explanation: [Explain the medical reasoning]
└─ Critical Question: Does this apply to THIS patient?

Clinical Factor 2: [Second element]
├─ Socratic Question: What evidence supports this approach?
├─ Deeper Explanation: [Explain the evidence base]
└─ Critical Question: Are we following treatment guidelines?

Clinical Factor 3: [Third element]
├─ Socratic Question: What alternatives exist?
├─ Deeper Explanation: [Explain other options]
└─ Critical Question: Why not try conservative management first?

═══════════════════════════════════════════════════════════════════════
LEVEL 3: EXAMINING CLINICAL ASSUMPTIONS
═══════════════════════════════════════════════════════════════════════

Assumption 1: [Clinical assumption]
├─ Clinical Evidence For: [Supporting data]
├─ Clinical Evidence Against: [Contradicting data]
├─ Patient-Specific Factors: [How does THIS patient differ?]
└─ Validity: [Is assumption sound for THIS patient?]

Assumption 2: [Another assumption]
├─ Clinical Evidence For: [Supporting data]
├─ Clinical Evidence Against: [Contradicting data]
├─ Patient-Specific Factors: [Individual considerations]
└─ Validity: [Sound or flawed?]

═══════════════════════════════════════════════════════════════════════
LEVEL 4: IDENTIFYING CLINICAL INCONSISTENCIES
═══════════════════════════════════════════════════════════════════════

INCONSISTENCY 1: [Description]
├─ Clinical Impact: [Effect on patient]
├─ Guideline Deviation: [Does this violate standard care?]
└─ Risk Level: [Patient safety concern?]

INCONSISTENCY 2: [Description]
├─ Clinical Impact: [Effect on patient]
├─ Guideline Deviation: [Protocol violation?]
└─ Risk Level: [Safety issue?]

═══════════════════════════════════════════════════════════════════════
LEVEL 5: REFINED CLINICAL RECOMMENDATION
═══════════════════════════════════════════════════════════════════════

Root Cause of Flawed Recommendation:
[What went wrong in clinical reasoning?]

Corrected Clinical Approach:
[What should treatment plan be?]

Evidence-Based Recommendation:
[Proper first-line treatment]

Patient-Specific Adjustments:
1. [Individual factor 1]
2. [Individual factor 2]
3. [Individual factor 3]

---

PATIENT CASE DATA:

Demographics:
- Age: 58 years old
- Sex: Male
- BMI: 29 (overweight but not obese)
- Occupation: Office manager (desk job, low physical demands)

Chief Complaint:
- Right knee pain × 6 weeks
- Gradual onset (no acute injury)
- Pain: 5/10 at rest, 7/10 with stairs
- Occasional "catching" sensation
- No locking episodes
- No giving way

Medical History:
- Hypertension (controlled on medication)
- Hyperlipidemia
- No prior knee problems
- No prior surgeries

Physical Examination:
- Mild effusion (joint swelling)
- Full range of motion
- Stable ligaments (ACL, PCL, MCL, LCL intact)
- Positive McMurray test (suggests meniscus tear)
- No significant muscle atrophy
- Able to bear weight fully

Imaging:
- MRI Right Knee: "Horizontal tear of medial meniscus posterior horn, 8mm in length"
- No other significant pathology
- Cartilage intact
- No bone marrow edema

Current Function:
- Walking: Normal gait, no limp
- Stairs: Slower than normal, uses handrail
- Work: Can perform job without limitation
- Sports: Not athletic, walks for exercise only
- ADLs: Independent in all activities

Treatment to Date:
- Over-the-counter ibuprofen PRN
- No formal physical therapy
- No activity modification attempted
- No structured conservative management

AI System Recommendation:
"MRI confirms medial meniscus tear. Surgical intervention recommended: 
arthroscopic partial meniscectomy. Patient has structural pathology 
requiring surgical repair. Tear size (8mm) and location (posterior horn) 
indicate good surgical candidate. Procedure will remove damaged tissue 
and alleviate symptoms."

Clinical Guidelines Context:
- AAOS (American Academy of Orthopedic Surgeons) guidelines state:
  "For degenerative meniscus tears without mechanical symptoms, 
  conservative management should be attempted before surgery"
- Multiple RCTs show physical therapy equally effective as surgery 
  for degenerative tears at 1 year
- Surgery has risks: infection (1-2%), DVT (0.5%), anesthesia risks
- Post-op recovery: 4-6 weeks limited activity

Using Maieutic questioning:
1. Question each component of AI's surgical recommendation
2. Drill into assumptions about "requiring surgery"
3. Test assumptions against patient-specific factors
4. Identify inconsistencies with guidelines
5. Provide evidence-based corrected recommendation
```

### What Students Should Learn:

**Critical Medical Concepts:**

1. **Question AI in Healthcare**: AI recommendations need validation, not blind acceptance
2. **Socratic Method Prevents Harm**: Questioning reveals flaws that could hurt patients
3. **Guidelines Matter**: Check if AI follows evidence-based protocols
4. **Patient-Specific**: Generic AI reasoning must be individualized
5. **Conservative First**: Question why AI skips less invasive options

**Real-World Impact:**
- Without Maieutic: Patient gets unnecessary surgery (risks, costs, recovery)
- With Maieutic: Discover AI recommends surgery for ALL meniscus tears (flawed), patient tries PT first (succeeds 60% of time, avoids surgery)

---

## How to Write Effective Maieutic Prompts

### Template Structure:

```
Context: [Why you need to validate reasoning through questioning]

Objective: Use Maieutic (Socratic) questioning to systematically examine 
[explanation/recommendation], question each component, and identify flaws.

Style: Socratic dialogue format - provide explanation, then question each 
component, drilling down through multiple levels.

Tone: [Analytical and questioning / Clinical and teaching]

Audience: [Who needs validated reasoning]

Response Format:

═══════════════════════════════════════════════════════════════════════
LEVEL 1: INITIAL EXPLANATION
═══════════════════════════════════════════════════════════════════════

Question: [Your initial question]

Initial Explanation:
[Get the first explanation]

═══════════════════════════════════════════════════════════════════════
LEVEL 2: QUESTIONING EACH COMPONENT
═══════════════════════════════════════════════════════════════════════

Component 1: [First part]
├─ Socratic Question: [Question the component]
├─ Deeper Explanation: [Get deeper reasoning]
└─ Critical Question: [Challenge assumptions]

[Repeat for each component]

═══════════════════════════════════════════════════════════════════════
LEVEL 3: EXAMINING ASSUMPTIONS
═══════════════════════════════════════════════════════════════════════

Assumption 1: [Identified assumption]
├─ Evidence For: [What supports it]
├─ Evidence Against: [What contradicts it]
└─ Validity: [Is it sound?]

[Repeat for each assumption]

═══════════════════════════════════════════════════════════════════════
LEVEL 4: IDENTIFYING INCONSISTENCIES
═══════════════════════════════════════════════════════════════════════

INCONSISTENCY 1: [What contradicts what]
├─ Where/Why: [Location and impact]
└─ Severity: [How problematic]

[Repeat for each inconsistency]

═══════════════════════════════════════════════════════════════════════
LEVEL 5: REFINED UNDERSTANDING
═══════════════════════════════════════════════════════════════════════

Root Cause: [What actually went wrong]
Corrected Logic: [How it should work]
Better Recommendation: [Improved answer]

---

[Provide all data for analysis]

Using Maieutic questioning:
1. Question each component
2. Drill into assumptions  
3. Test against evidence
4. Identify inconsistencies
5. Provide corrected version
```

### Critical Elements:

1. **Multi-Level Structure**: Must have 5 levels (Initial → Components → Assumptions → Inconsistencies → Refined)
2. **Explicit Questioning**: State actual Socratic questions to ask
3. **Tree Format**: Use ├─ and └─ to show questioning hierarchy
4. **Test Against Evidence**: Always require evidence for/against
5. **Demand Refinement**: Must produce improved answer at end

---

## Common Mistakes Students Make

### Mistake 1: Accepting First Explanation
❌ **Bad:** "System recommends X because Y. That makes sense."
✓ **Good:** "System recommends X because Y. But WHY does Y lead to X? What assumes this connection?"

### Mistake 2: Not Drilling Deep Enough
❌ **Bad:** Only question Level 1, stop there
✓ **Good:** Question Level 1 → Level 2 → Level 3 (minimum 3 levels)

### Mistake 3: Vague Questioning
❌ **Bad:** "Is this right?" "Can you explain more?"
✓ **Good:** "What evidence supports using 120Hz as primary ranking factor? Does user data contradict this?"

### Mistake 4: Ignoring Inconsistencies
❌ **Bad:** Find inconsistency, don't flag it, continue
✓ **Good:** "INCONSISTENCY FOUND: Logic says X but data shows Y. This is problematic because..."

### Mistake 5: No Refinement
❌ **Bad:** Identify flaws, then stop
✓ **Good:** Identify flaws, then provide corrected logic and better recommendation

---

## Practice Exercises

### Exercise 1: E-Commerce Dynamic Pricing

**Scenario:**
Your AI pricing system automatically raised the price of bottled water from $8/case to $45/case during a hurricane warning. System explanation: "Demand increased 500%, price adjusted to match demand curve."

**Your Task:**
Write a Maieutic COSTAR prompt that:
1. Questions each component of the pricing logic
2. Uncovers assumptions about "demand-based pricing"
3. Tests assumptions against ethics and brand reputation
4. Identifies inconsistencies with company values
5. Provides corrected pricing strategy

### Exercise 2: Healthcare Antibiotic Prescription

**Scenario:**
Clinical AI recommends broad-spectrum antibiotic (ceftriaxone) for patient with mild viral URI symptoms (runny nose, cough, 99.5°F temp × 2 days). System explanation: "Antibiotic will prevent bacterial superinfection."

**Your Task:**
Write a Maieutic COSTAR prompt that:
1. Questions the antibiotic recommendation logic
2. Drills into "prevent superinfection" assumption
3. Tests against antibiotic stewardship guidelines
4. Identifies inconsistencies with evidence-based medicine
5. Provides appropriate treatment plan

---

## Summary

### Key Takeaways:

1. ✓ **Maieutic = Systematic Socratic Questioning**
   - Question initial explanation
   - Question each component
   - Question assumptions
   - Find inconsistencies
   - Refine to better answer

2. ✓ **5-Level Structure:**
   - Level 1: Initial explanation
   - Level 2: Question components
   - Level 3: Examine assumptions
   - Level 4: Identify inconsistencies
   - Level 5: Refined understanding

3. ✓ **Critical for Validation:**
   - Don't accept AI reasoning at face value
   - Especially important for complex recommendations
   - Essential in healthcare (patient safety)
   - Valuable in business (costly decisions)

4. ✓ **Benefits:**
   - Uncovers hidden assumptions
   - Finds logical flaws
   - Tests reasoning quality
   - Produces better final answers
   - Prevents costly mistakes

5. ✓ **Proper COSTAR Prompts:**
   - Multi-level structure with explicit levels
   - Actual Socratic questions stated
   - Tree format (├─ └─) showing hierarchy
   - Evidence testing required
   - Refinement demanded

### Remember:
**Simple prompts accept answers at face value.**
**Maieutic prompts question until truth emerges.**

In e-commerce, this prevents bad recommendations.
In healthcare, this prevents patient harm.

---

## Next Steps

1. Practice writing 5-level Maieutic prompts
2. Try questioning AI explanations systematically
3. Count how many assumptions you uncover
4. Measure how much recommendations improve
5. Move on to Generated Knowledge Prompting (next technique)

Master the art of Socratic questioning! 🎓
