# Self-Refine Prompting - Complete Guide

## What is Self-Refine Prompting?

Self-Refine prompting creates an iterative improvement loop: generate initial solution → critique it to find specific flaws → refine based on critique → critique again → refine again → repeat until polished. Like editing a document through multiple drafts, each iteration catches and fixes issues the previous missed.

### Think of it like this:

**Regular Prompting:**
```
Problem → Solution → Done (accept whatever quality you get)
```

**Self-Refine Prompting:**
```
Problem → Draft 1 → Critique (find 10 flaws) → Draft 2 (fix flaws)
         ↓
Critique Draft 2 (find 5 remaining flaws) → Draft 3 (fix remaining)
         ↓
Critique Draft 3 (find 2 final issues) → Final Draft (polished)
```

---

## Why Use Self-Refine Prompting?

### Benefits:

1. **Improves Quality Through Iteration** - Each draft gets better
2. **Finds Specific Flaws** - Systematic critique reveals issues
3. **Fixes Exactly What's Wrong** - Targeted improvements
4. **Creates Professional Output** - Multiple refinements produce polish
5. **Self-Improvement Loop** - No human needed between iterations

### When to Use Self-Refine:

✓ **Use when:**
- Creating important documents/communications
- Need professional, polished output
- First draft likely has flaws
- Quality matters more than speed
- Stakes are high (contracts, patient materials, proposals)

✗ **Don't use when:**
- Quick draft is sufficient
- Time is extremely limited
- Content is simple and straightforward
- First attempt typically good enough

---

## How It Works

### The Iterative Refinement Process:

**Iteration 1:**
- Generate initial draft
- Critique it (identify 10+ specific flaws)
- Create improved draft addressing ALL critiques

**Iteration 2:**
- Critique improved draft (find remaining flaws)
- Create refined draft addressing new critiques
- Quality significantly improved

**Iteration 3:**
- Final critique (minor issues only at this point)
- Create polished final version
- Professional quality achieved

**Rule of Thumb:** Usually 2-3 iterations sufficient (diminishing returns after that)

---

## Example 1: E-Commerce - High-Stakes Sales Email

### Business Problem:
Write sales email to hospital administrators about AI patient coordination software. This is cold outreach to busy executives. Poor email = ignored. Good email = $15K/year contracts.

### Why Self-Refine Helps:
- First draft typically has generic language
- Multiple issues need fixing (length, value prop, CTA)
- Each iteration catches what previous missed
- Final draft converts 10-15% vs 1-2% for first draft

### COSTAR Prompt:

```
Context: We're writing a cold sales email to hospital administrators about 
AI patient coordination software. This email must be exceptional because 
recipients are extremely busy executives who delete most sales emails. Poor 
email = no response. Refined email = potential $15K/year customer.

Objective: Use Self-Refine approach to create a polished, high-converting 
sales email through iterative improvement. Generate initial draft, 
systematically critique it to find ALL flaws, refine based on critique, 
critique again, refine again, until we have professional-quality output.

Style: Iterative refinement showing: (1) initial draft, (2) detailed critique 
identifying specific numbered flaws, (3) refined draft fixing ALL flaws, 
(4) second critique finding remaining issues, (5) final polished version.

Tone: Each critique should be thorough and specific (not vague). Each 
refinement should address EVERY critique point. Like an editor working 
through multiple drafts with author.

Audience: Sales and marketing teams creating high-stakes communications.

Response Format:

═══════════════════════════════════════════════════════════════════════
ITERATION 1: INITIAL DRAFT
═══════════════════════════════════════════════════════════════════════

Initial Draft:
[Generate first attempt - will have flaws]

═══════════════════════════════════════════════════════════════════════
CRITIQUE 1: SYSTEMATIC FLAW IDENTIFICATION
═══════════════════════════════════════════════════════════════════════

Identify ALL flaws in initial draft (aim for 10-15 specific issues):

FLAW 1: [Specific problem]
├─ Location: [Where in draft]
├─ Why problematic: [Impact on effectiveness]
├─ Severity: [Critical/Major/Minor]
└─ Fix needed: [What to do instead]

FLAW 2: [Specific problem]
├─ Location: [Where in draft]
├─ Why problematic: [Impact]
├─ Severity: [Level]
└─ Fix needed: [Correction]

[Continue through ALL flaws - should be 10-15 items]

SUMMARY OF ISSUES:
• Critical flaws: [Count]
• Major flaws: [Count]
• Minor flaws: [Count]
• Total fixes needed: [Count]

═══════════════════════════════════════════════════════════════════════
ITERATION 2: REFINED DRAFT (Addressing Critique 1)
═══════════════════════════════════════════════════════════════════════

Improvements Made:
✓ Fixed Flaw 1: [How it was addressed]
✓ Fixed Flaw 2: [How it was addressed]
✓ Fixed Flaw 3: [How it was addressed]
[List ALL fixes applied]

Refined Draft:
[Complete revised version addressing ALL critiques]

═══════════════════════════════════════════════════════════════════════
CRITIQUE 2: REMAINING ISSUES
═══════════════════════════════════════════════════════════════════════

Improvements from Iteration 1: ✓
✓ [Confirmed fix 1]
✓ [Confirmed fix 2]
✓ [Confirmed fix 3]

Remaining Flaws (should be 3-5 issues):

REMAINING FLAW 1: [What still needs work]
├─ Why still problematic: [Issue]
└─ Final fix needed: [Correction]

REMAINING FLAW 2: [What still needs work]
├─ Why still problematic: [Issue]
└─ Final fix needed: [Correction]

[Continue for remaining issues]

═══════════════════════════════════════════════════════════════════════
ITERATION 3: FINAL POLISHED VERSION
═══════════════════════════════════════════════════════════════════════

Final Improvements Made:
✓ Fixed Remaining Flaw 1: [How addressed]
✓ Fixed Remaining Flaw 2: [How addressed]
[List all final fixes]

Final Polished Email:
[Complete professional version]

═══════════════════════════════════════════════════════════════════════
REFINEMENT IMPACT ANALYSIS
═══════════════════════════════════════════════════════════════════════

Iteration 1 Issues:
[List major problems with first draft]

Iteration 2 Improvements:
[What got better]

Iteration 3 Polish:
[Final refinements]

Quality Comparison:
• Draft 1: [Description of quality]
• Draft 2: [Description of improvement]
• Draft 3: [Description of final quality]

Expected Performance:
• Draft 1 response rate: 1-2%
• Draft 3 response rate: 10-15%
• Improvement: 5-7.5x better performance

Why Self-Refine Worked:
[Explain value of iterative improvement]

---

PRODUCT & TARGET DATA:

Product: MediConnect Pro
- AI-powered patient coordination platform
- Automates scheduling, reminders, care coordination
- Price: $15,000/year per hospital

Proven Results (from existing customers):
- 35% reduction in administrative workload
- 22% improvement in patient satisfaction scores
- 18% decrease in no-show rates
- Average ROI: 14.4x in year one

Target Audience:
- Hospital administrators (C-suite, VP Operations)
- Hospitals: 200-500 beds
- Pain points: High admin costs, patient satisfaction issues, no-shows
- Typical admin cost: $360K/year for patient coordination
- Extremely busy (receive 100+ sales emails daily)
- Delete/ignore 98% of sales emails
- Need immediate value proposition in subject line
- Want concrete ROI, not vague promises

Case Study Available:
- Mercy Hospital (425 beds, Ohio)
- Results achieved in 4 months
- $196K net benefit year one

Email Constraints:
- Subject line: Maximum 60 characters, must include specific value
- Body: Maximum 150 words (busy executives won't read more)
- Must have clear, easy CTA (not "let me know if interested")
- Must avoid: Generic phrases, feature lists, seller-focused language
- Must include: Specific dollar amounts, ROI, peer validation

Generate sales email using Self-Refine:
ITERATION 1: Generate initial draft (will have many flaws)
CRITIQUE 1: Identify 10-15 specific flaws comprehensively
ITERATION 2: Fix ALL flaws, create refined draft
CRITIQUE 2: Find 3-5 remaining issues
ITERATION 3: Create final polished version

For each critique, be SPECIFIC about location and exact problem, 
not vague like "improve tone" - say exactly what's wrong and how to fix.
```

### Expected AI Response Structure:

The AI would generate:

**Iteration 1 - Initial Draft:**
```
Subject: Introducing MediConnect Pro

Dear Hospital Administrator,

We're excited to introduce MediConnect Pro, our new AI-powered patient 
coordination platform. It's designed to help your hospital run more 
efficiently.

MediConnect Pro uses artificial intelligence to automate patient scheduling, 
send reminders, and coordinate care between departments. We've seen great 
results from our early adopters.

Key features include:
- Automated scheduling
- Smart reminders  
- Department coordination
- Analytics dashboard

We think your hospital could benefit from this solution. The price is 
$15,000 per year.

If you're interested, please let us know and we can set up a demo.

Best regards,
Sales Team
```

**Critique 1 - Identify 10-15 Flaws:**
```
FLAW 1: Subject line generic
├─ Location: Subject line
├─ Why problematic: No value, looks like spam, will be deleted
├─ Severity: CRITICAL
└─ Fix needed: Include specific benefit and number

FLAW 2: Opens with "we're excited" 
├─ Location: First sentence
├─ Why problematic: Seller-focused, not buyer-focused, cliché
├─ Severity: MAJOR
└─ Fix needed: Open with recipient's pain point

FLAW 3: "Great results" is vague
├─ Location: Paragraph 2
├─ Why problematic: No credibility, no numbers, meaningless
├─ Severity: CRITICAL
└─ Fix needed: Specific metrics with percentages/dollars

FLAW 4: Lists features not benefits
├─ Location: Bullet points
├─ Why problematic: Doesn't translate to ROI, admin doesn't care about features
├─ Severity: MAJOR
└─ Fix needed: Convert each feature to dollar benefit

FLAW 5: Price without context
├─ Location: Paragraph 4
├─ Why problematic: $15K seems expensive without ROI justification
├─ Severity: CRITICAL
└─ Fix needed: Show $15K investment returns $196K (14.4x ROI)

[10 more specific flaws listed...]

TOTAL: 15 flaws (5 critical, 6 major, 4 minor)
```

**Iteration 2 - Refined Draft:**
(Shows all 15 fixes applied, much improved but still has 3-5 remaining issues)

**Critique 2 - Remaining Issues:**
(Finds 3-5 things still needing work)

**Iteration 3 - Final Polished:**
```
Subject: [Name], Cut Admin Costs 35% at [Hospital Name]?

Dear [Name],

Your 300-bed hospital likely spends $360K/year on patient scheduling. 
Mercy Hospital and St. Luke's Regional had the same challenge.

They reduced those costs by 35% with MediConnect Pro.

**The math:**
$15K platform + $5K implementation = $20K total cost
$127K admin savings + $89K recovered revenue = $216K benefit
**Net gain: $196K**

**Three proven outcomes** (validated across 47 hospitals):
- Cut admin workload 35% → redeploy 1.8 FTEs to patient care
- Boost satisfaction 22% → improve CAHPS ranking
- Reduce no-shows 18% → recover $85-95K annually

**One question:** Would saving $196K justify a 15-minute conversation?

If yes → [Calendar link]
If maybe → Reply for ROI calculator

[Name], Healthcare Solutions
```

**Impact Analysis:**
- Draft 1: 1-2% response rate (generic, will be ignored)
- Draft 3: 10-15% response rate (specific, valuable, professional)
- 5-7.5x improvement through refinement

---

## Example 2: Healthcare - Patient Diabetes Education Material

### Medical Problem:
Create patient education handout about diabetes medication adherence. Poor materials = patients don't understand = don't take meds = complications. Good materials = comprehension = adherence = outcomes.

### Why Self-Refine is CRITICAL:

⚠️ **PATIENT SAFETY DEPENDS ON MATERIAL QUALITY** ⚠️
- Confusing materials = medication errors
- Missing information = preventable complications
- Poor readability = low health literacy patients can't understand
- Each refinement catches patient safety issues

### COSTAR Prompt:

```
Context: We're creating a patient education handout about diabetes medication 
adherence. This material directly impacts patient health outcomes - confusing 
or incomplete materials lead to medication non-adherence, which causes 
preventable complications and deaths. We need professional, patient-appropriate 
materials through iterative refinement.

Objective: Use Self-Refine approach to create a clear, complete, 
patient-appropriate diabetes medication adherence handout. Generate initial 
draft, systematically critique for medical completeness and health literacy 
issues, refine, critique again, refine again until we have materials that 
actually improve patient outcomes.

Style: Iterative refinement showing: (1) initial draft, (2) detailed critique 
identifying medical gaps and health literacy issues, (3) refined draft fixing 
ALL issues, (4) second critique for remaining problems, (5) final 
patient-ready version.

Tone: Each critique should identify both medical content gaps and health 
literacy barriers. Each refinement must address patient safety and 
comprehension. Like a clinical educator reviewing materials with health 
literacy expert.

Audience: Clinical education team creating patient-facing materials.

Response Format:

═══════════════════════════════════════════════════════════════════════
ITERATION 1: INITIAL DRAFT
═══════════════════════════════════════════════════════════════════════

Initial Draft:
[First attempt - will have medical gaps and literacy issues]

═══════════════════════════════════════════════════════════════════════
CRITIQUE 1: MEDICAL & LITERACY ANALYSIS
═══════════════════════════════════════════════════════════════════════

Identify ALL issues (medical completeness + health literacy):

ISSUE 1: [Specific problem]
├─ Category: [Medical gap / Health literacy / Safety]
├─ Location: [Where in draft]
├─ Patient impact: [How this harms patient]
├─ Severity: [Critical/Major/Minor]
└─ Fix needed: [Specific correction]

ISSUE 2: [Specific problem]
├─ Category: [Type]
├─ Location: [Where]
├─ Patient impact: [Consequence]
├─ Severity: [Level]
└─ Fix needed: [Correction]

[Continue through all issues - aim for 12-15]

CATEGORIZED SUMMARY:
• Medical content gaps: [Count]
• Health literacy barriers: [Count]
• Patient safety concerns: [Count]
• Total fixes needed: [Count]

═══════════════════════════════════════════════════════════════════════
ITERATION 2: REFINED DRAFT (Addressing Critique 1)
═══════════════════════════════════════════════════════════════════════

Medical Improvements Made:
✓ Fixed Issue 1: [How addressed]
✓ Fixed Issue 2: [How addressed]
[List all medical fixes]

Health Literacy Improvements Made:
✓ Fixed Issue X: [How addressed]
✓ Fixed Issue Y: [How addressed]
[List all literacy fixes]

Refined Draft:
[Complete improved version addressing ALL critiques]

═══════════════════════════════════════════════════════════════════════
CRITIQUE 2: REMAINING ISSUES
═══════════════════════════════════════════════════════════════════════

Confirmed Improvements: ✓
✓ [Medical gap fixed]
✓ [Literacy barrier fixed]
[List confirmed fixes]

Remaining Issues (should be 3-5):

REMAINING ISSUE 1: [What still needs work]
├─ Why still problematic: [Issue]
├─ Patient impact: [Consequence]
└─ Final fix needed: [Correction]

[Continue for remaining issues]

═══════════════════════════════════════════════════════════════════════
ITERATION 3: FINAL PATIENT-READY VERSION
═══════════════════════════════════════════════════════════════════════

Final Improvements Made:
✓ [Final fix 1]
✓ [Final fix 2]
[List all final refinements]

Final Patient Education Handout:
[Complete professional, patient-appropriate version]

═══════════════════════════════════════════════════════════════════════
REFINEMENT IMPACT ON PATIENT OUTCOMES
═══════════════════════════════════════════════════════════════════════

Iteration 1 Problems:
[Medical gaps and literacy barriers]

Iteration 2 Improvements:
[Medical completeness and clarity gains]

Iteration 3 Polish:
[Final patient safety enhancements]

Expected Patient Outcomes:

Draft 1:
• Comprehension: 40-50% (many patients won't understand)
• Adherence: Low (confusion leads to non-adherence)
• Safety: Moderate risk (missing critical information)

Draft 3:
• Comprehension: 85-90% (clear for low health literacy)
• Adherence: High (understands why and how)
• Safety: Strong (addresses all safety concerns)

Clinical Impact:
Draft 1 → 50% adherence → More complications
Draft 3 → 80% adherence → Better outcomes, fewer hospitalizations

Why Self-Refine Saved Lives:
[Explain how iteration prevented medication errors]

---

CLINICAL & PATIENT DATA:

Medical Topic: Diabetes Medication Adherence

Clinical Facts:
- 50% of diabetes patients don't take medications as prescribed
- Proper adherence reduces HbA1c by 0.5-1.5 points
- Each 1% HbA1c reduction = 37% fewer complications
- Good adherence: 16% less heart attack, 15% less stroke
- Non-adherence causes 125,000 preventable deaths/year in US

Common Non-Adherence Reasons:
- Forgetting (32%)
- Cost concerns (28%)
- Side effects (22%)
- Don't understand why medication is important (18%)

Patient Population:
- Average reading level: 8th grade (health materials should be 6th grade)
- 40% have limited health literacy
- Many are visual learners
- Need concrete examples, not abstract concepts
- Often don't understand HbA1c or medical terms

Key Information to Include:
- Why medication matters (prevent complications, not just numbers)
- Specific benefits (reduce heart attack 16%, stroke 15%)
- How to remember (strategies that work)
- Cost solutions (generics, assistance programs)
- Side effect management (most improve in 2 weeks)
- When to call doctor
- What complications cost vs what medication costs

Materials Must Avoid:
- Medical jargon without explanation
- Abstract concepts without concrete examples
- Passive voice ("medications should be taken")
- Long paragraphs (break into short sections)
- Missing "why" (just telling what to do without rationale)
- Scare tactics (focus on benefits, not just risks)

Reading Level Test:
- Use Flesch-Kincaid grade level
- Target: 6th grade or lower
- Short sentences (15 words or less)
- Simple words (use "help" not "facilitate")

Generate patient handout using Self-Refine:
ITERATION 1: Generate initial draft (will have gaps)
CRITIQUE 1: Identify 12-15 medical and literacy issues
ITERATION 2: Fix ALL issues, create refined draft
CRITIQUE 2: Find 3-5 remaining problems
ITERATION 3: Create final patient-ready version

Critique must identify: medical completeness, health literacy barriers, 
patient safety concerns, reading level issues, missing practical advice.
```

### What Students Should Learn:

**Critical Concepts:**

1. **Iteration Improves Quality**: First draft always has flaws, refinement catches them
2. **Specific Critique Required**: "Make it better" doesn't work - need specific numbered flaws
3. **Address ALL Critiques**: Each refinement must fix EVERY identified issue
4. **Diminishing Returns**: 2-3 iterations usually sufficient, more doesn't help much
5. **Stakes Determine Effort**: High-stakes documents need refinement, quick drafts don't

**Real-World Impact:**

**E-Commerce Example:**
- Draft 1: Generic sales email (1-2% response rate, ignored)
- Draft 2: Improved with ROI (5-7% response rate)
- Draft 3: Polished professional (10-15% response rate)
- Result: 5-7.5x better performance through refinement

**Healthcare Example:**
- Draft 1: Incomplete, jargon-filled (50% comprehension, low adherence)
- Draft 2: Complete medical info but still complex (70% comprehension)
- Draft 3: Complete + patient-appropriate (85-90% comprehension, high adherence)
- Result: Adherence improves from 50% to 80%, prevents complications

---

## How to Write Effective Self-Refine Prompts

### Template Structure:

```
Context: [Why quality matters and stakes are high]

Objective: Use Self-Refine approach to create [output] through iterative 
improvement. Generate initial draft, systematically critique it, refine 
based on critique, critique again, refine again until polished.

Style: Iterative refinement showing: (1) initial draft, (2) detailed 
critique with specific numbered flaws, (3) refined draft fixing ALL flaws, 
(4) second critique, (5) final polished version.

Tone: Critiques should be thorough and specific. Refinements should 
address EVERY critique point. Like professional editor.

Audience: [Who creates and uses the output]

Response Format:

═══════════════════════════════════════════════════════════════════════
ITERATION 1: INITIAL DRAFT
═══════════════════════════════════════════════════════════════════════
[First attempt]

═══════════════════════════════════════════════════════════════════════
CRITIQUE 1: SYSTEMATIC FLAW IDENTIFICATION
═══════════════════════════════════════════════════════════════════════

FLAW 1: [Specific problem]
├─ Location: [Where]
├─ Why problematic: [Impact]
├─ Severity: [Critical/Major/Minor]
└─ Fix needed: [Specific correction]

[Continue for 10-15 flaws]

═══════════════════════════════════════════════════════════════════════
ITERATION 2: REFINED DRAFT
═══════════════════════════════════════════════════════════════════════

Improvements Made:
✓ [Fix 1]
✓ [Fix 2]
[All fixes listed]

Refined Draft:
[Improved version]

═══════════════════════════════════════════════════════════════════════
CRITIQUE 2: REMAINING ISSUES
═══════════════════════════════════════════════════════════════════════

[Find 3-5 remaining problems]

═══════════════════════════════════════════════════════════════════════
ITERATION 3: FINAL POLISHED VERSION
═══════════════════════════════════════════════════════════════════════

[Professional final draft]

═══════════════════════════════════════════════════════════════════════
REFINEMENT IMPACT ANALYSIS
═══════════════════════════════════════════════════════════════════════

Quality Comparison:
Draft 1: [Issues]
Draft 3: [Improvements]
Performance: [Metrics]

---

[Provide all requirements and constraints]

Generate using Self-Refine:
ITERATION 1: Initial draft
CRITIQUE 1: Identify 10-15 specific flaws
ITERATION 2: Fix ALL flaws
CRITIQUE 2: Find remaining issues
ITERATION 3: Final polished version
```

### Critical Elements:

1. **Numbered Specific Flaws**: Not "improve tone" but "Flaw 3: Subject line has no value (location: line 1, fix: add specific benefit)"
2. **All Fixes Listed**: Show exactly what was corrected
3. **Severity Ratings**: Critical/Major/Minor helps prioritize
4. **Impact Analysis**: Compare Draft 1 vs Draft 3 performance
5. **2-3 Iterations**: Standard refinement cycle

---

## Common Mistakes Students Make

### Mistake 1: Vague Critique
❌ **Bad:** "Make it better, improve the tone"
✓ **Good:** "FLAW 5: Opens with 'we're excited' (seller-focused, cliché, severity: MAJOR) → Fix: Open with recipient's pain point"

### Mistake 2: Not Fixing All Critiques
❌ **Bad:** Critique finds 15 flaws, refinement fixes 8
✓ **Good:** Critique finds 15 flaws, refinement addresses ALL 15

### Mistake 3: Stopping After One Iteration
❌ **Bad:** Generate → Critique → Refine → Done
✓ **Good:** Generate → Critique → Refine → Critique → Refine → Done (2-3 cycles)

### Mistake 4: No Specific Location
❌ **Bad:** "Email is too long"
✓ **Good:** "FLAW 7: Body is 287 words (location: entire body, target: 150 words max)"

### Mistake 5: Not Comparing Versions
❌ **Bad:** Just create Draft 3, don't show improvement
✓ **Good:** Show Draft 1 performance (2% response) vs Draft 3 (15% response) = 7.5x better

---

## Practice Exercises

### Exercise 1: E-Commerce Product Description

**Scenario:**
Write product description for $399 ergonomic office chair for Amazon listing. Competitors have better reviews because descriptions are clearer.

**Requirements:**
- Highlight back pain reduction (40% in clinical study)
- 12-way adjustability features
- Address common objections (price, assembly, warranty)
- Reading level: 8th grade
- Maximum: 200 words

**Your Task:**
Write a Self-Refine COSTAR prompt that:
1. Generates initial description
2. Critiques for 10+ specific flaws (features vs benefits, missing objection handling, reading level, length)
3. Refines addressing all critiques
4. Final critique and polish
5. Shows conversion improvement (clicks, add-to-cart rate)

### Exercise 2: Healthcare Discharge Instructions

**Scenario:**
Create discharge instructions for post-surgical patient (knee replacement). Poor instructions = readmissions. Good instructions = successful recovery at home.

**Requirements:**
- Pain management (when to take meds, what's normal)
- Activity restrictions (what NOT to do)
- Wound care (signs of infection)
- PT exercises (when to start, how often)
- Emergency signs (when to call doctor vs 911)
- Reading level: 6th grade (health literacy)

**Your Task:**
Write a Self-Refine COSTAR prompt that:
1. Generates initial instructions
2. Critiques for medical completeness, safety gaps, health literacy barriers
3. Refines addressing all safety concerns
4. Final critique and polish
5. Shows readmission reduction (20% to 8%)

---

## Summary

### Key Takeaways:

1. ✓ **Self-Refine = Iterative Improvement Loop**
   - Generate initial draft
   - Critique with specific numbered flaws
   - Refine addressing ALL critiques
   - Critique again (find remaining issues)
   - Final polish
   - Usually 2-3 iterations

2. ✓ **Critique Must Be Specific:**
   - Not: "Improve tone"
   - Yes: "FLAW 3: Opens with 'we're excited' (seller-focused, line 1) → Fix: Open with pain point"

3. ✓ **Address ALL Critiques:**
   - If critique finds 15 flaws, refinement must fix all 15
   - Show exactly what was corrected
   - Confirm fixes in next critique

4. ✓ **Proper COSTAR Prompts Must:**
   - Demand specific numbered critiques (10-15 first round, 3-5 second round)
   - Require severity ratings (Critical/Major/Minor)
   - Show fixes applied
   - Compare Draft 1 vs Final performance
   - Prove value of iteration

5. ✓ **Stakes Determine Effort:**
   - Quick email to colleague: 1 draft sufficient
   - Sales email to executives: 3 iterations essential
   - Patient safety materials: 3 iterations mandatory
   - Legal contract: 3-4 iterations required

### Remember:
**First drafts are always flawed.**
**Systematic refinement produces professional quality.**

In e-commerce, Self-Refine improves response rates 5-7.5x.
In healthcare, Self-Refine improves patient comprehension from 50% to 85-90%.

---

## Next Steps

1. Practice writing specific numbered critiques (not vague feedback)
2. Try 2-3 iteration cycle on important document
3. Compare your Draft 1 vs Draft 3 quality
4. Measure performance improvement (metrics matter)
5. Apply Self-Refine to all high-stakes communications

Master the art of iterative improvement! ✨
