# Chain-of-Thought (CoT) Prompting - Complete Guide

## What is Chain-of-Thought Prompting?

Chain-of-Thought (CoT) prompting is a technique that improves AI reasoning by breaking down complex problems into step-by-step thought processes. Instead of jumping directly to an answer, the AI shows its "thinking" process, making the solution more accurate and explainable.

### Think of it like this:

**Without CoT (Bad):**
```
Question: What's 15% of $847.50?
Answer: $127.13
```
You get an answer, but no idea how it was calculated.

**With CoT (Good):**
```
Question: What's 15% of $847.50?
Thinking:
  Step 1: Convert 15% to decimal: 15% = 0.15
  Step 2: Multiply: $847.50 × 0.15
  Step 3: Calculate: $127.125
  Step 4: Round to cents: $127.13
Answer: $127.13
```
Now you can verify each step!

---

## Why Use Chain-of-Thought?

### Benefits:

1. **More Accurate Results** - Breaking problems into steps reduces errors
2. **Explainable Reasoning** - You can see HOW the AI reached its answer
3. **Error Detection** - Easy to spot where reasoning went wrong
4. **Complex Problem Solving** - Handles multi-step calculations and logic
5. **Builds Trust** - Transparent thinking process increases confidence

### When to Use CoT:

✓ **Use CoT when:**
- Problem involves multiple steps
- Calculations are required
- Logic needs to be verified
- Accuracy is critical
- You need to explain the answer to others

✗ **Don't use CoT when:**
- Simple, single-step questions
- Creative writing (kills creativity)
- Speed is more important than accuracy
- Problem is too simple for step-by-step

---

## Two Types of Chain-of-Thought

### 1. Zero-Shot CoT
Simply add "Let's think step-by-step" to your prompt.

**Example:**
```
Question: Calculate the total price for 3 items at $24.99 each with 8% tax.

Let's think step-by-step:
```

### 2. Few-Shot CoT
Show examples of step-by-step reasoning first, then ask your question.

**Example:**
```
Example 1:
Question: Price: $10, Tax: 5%, Total?
Solution:
  Step 1: Calculate tax: $10 × 0.05 = $0.50
  Step 2: Add tax: $10 + $0.50 = $10.50
  Answer: $10.50

Example 2:
Question: Price: $25, Discount: 20%, Total?
Solution:
  Step 1: Calculate discount: $25 × 0.20 = $5.00
  Step 2: Subtract discount: $25 - $5.00 = $20.00
  Answer: $20.00

Now solve:
Question: Price: $50, Tax: 7%, Discount: 15%, Total?
```

---

## Example 1: E-Commerce - Shipping Cost Calculator

### Business Problem:
Calculate complex shipping costs with multiple discounts and promotions.

### Why CoT Helps:
- Multiple discount rules can conflict
- Order of operations matters
- Need to explain charges to customers
- Calculations must be auditable

### COSTAR Prompt:

```
Context: We need to calculate shipping costs for an e-commerce order with 
complex discount rules.

Objective: Determine the final shipping cost after applying all available 
discounts and promotions.

Style: Think through the problem methodically, showing each calculation step.

Tone: Analytical and precise, like an accountant verifying calculations.

Audience: Internal operations team who needs to understand the calculation logic.

Response Format: Use <thinking></thinking> tags for your reasoning process, 
then provide the final answer with <answer></answer> tags.

---

Order Details:
- Subtotal: $245
- Items weight: 8.5 lbs
- Standard shipping base rate: $12
- Customer has Prime membership (free shipping on orders >$100)
- Active promotion: 20% off shipping for orders >$200
- Additional promotion: $5 off shipping for first-time buyers (customer is returning buyer)

Think step-by-step to calculate the final shipping cost.
```

### Expected AI Response:

```
<thinking>
Step 1: Identify the base shipping cost
- Items weight: 8.5 lbs
- Standard shipping rate: $12 (flat rate for orders under 10 lbs)
- Base shipping cost: $12

Step 2: Check Prime membership eligibility
- Customer has Prime membership: YES
- Prime benefit: Free shipping on orders >$100
- Order subtotal: $245
- Does $245 > $100? YES
- Prime discount applies: -$12
- Running total: $12 - $12 = $0

Step 3: Check 20% off promotion
- Promotion: 20% off shipping for orders >$200
- Order subtotal: $245
- Does $245 > $200? YES
- Current shipping cost: $0 (already free from Prime)
- 20% of $0 = $0
- Promotion applies but no additional benefit
- Running total: $0 - $0 = $0

Step 4: Check first-time buyer discount
- Promotion: $5 off shipping for first-time buyers
- Customer status: Returning buyer
- Does promotion apply? NO
- Running total: $0 (unchanged)

Step 5: Final calculation
- Base shipping: $12
- Prime discount: -$12
- 20% promotion: $0 (no effect)
- First-time discount: $0 (not applicable)
- Final shipping cost: $0

Step 6: Verification
- Start with $12 base rate
- Apply Prime (free shipping threshold met): $12 - $12 = $0
- Apply other promotions: No additional effect
- Result: $0 ✓
</thinking>

<answer>
Final Shipping Cost: $0.00

Breakdown:
- Standard shipping: $12.00
- Prime discount: -$12.00 (free shipping on orders >$100)
- Additional promotions: $0.00 (not applicable when shipping is already free)

Reason: Prime membership provides free shipping for orders over $100. 
Since the order total is $245, the shipping cost is $0. The 20% off 
promotion would apply, but there's no shipping cost to discount.
</answer>
```

### What Students Should Learn:

**Key Concepts:**
1. **Order of Operations**: Discounts are checked in priority order
2. **Conditional Logic**: Each promotion has eligibility criteria
3. **Edge Cases**: Multiple promotions can overlap
4. **Verification**: Always double-check the final calculation

**Common Mistakes Without CoT:**
- Applying 20% discount before checking Prime
- Forgetting to verify promotion eligibility
- Adding discounts that don't stack
- Missing edge cases (free shipping + percentage discount)

---

## Example 2: Healthcare - Pediatric Dosage Calculation

### Medical Problem:
Calculate precise medication dosages for children based on weight and protocol.

### Why CoT is CRITICAL Here:

⚠️ **SAFETY FIRST** ⚠️
- Wrong dosage can harm or kill a patient
- Calculations must be verifiable by multiple people
- Regulatory requirement to document reasoning
- Parent/caregiver needs to understand the dosage

### COSTAR Prompt:

```
Context: Healthcare dosage calculations require precise step-by-step reasoning 
to ensure patient safety.

Objective: Calculate pediatric medication dosages following standard protocols.

Style: Show complete mathematical reasoning like a clinical pharmacist would 
document for peer review.

Tone: Meticulous and safety-focused, with verification at each step.

Audience: Healthcare professionals who need to verify dosing calculations.

Response Format: Show problem → step-by-step calculation → verification → 
safety check → final answer

---

DOSING EXAMPLES:

Example 1:
Problem: Child weighs 15 kg. Medication: Amoxicillin 45 mg/kg/day divided into 
2 doses. Calculate single dose.

Solution:
Step 1: Calculate total daily dose
  Formula: Weight (kg) × Dosage (mg/kg/day)
  Calculation: 15 kg × 45 mg/kg/day = 675 mg/day

Step 2: Divide by number of doses
  Formula: Total daily dose ÷ Number of doses per day
  Calculation: 675 mg/day ÷ 2 doses = 337.5 mg per dose

Step 3: Verification
  Check: 337.5 mg × 2 doses = 675 mg/day ✓
  Verify: 675 mg/day ÷ 15 kg = 45 mg/kg/day ✓

Step 4: Safety check
  Standard pediatric range for Amoxicillin: 25-50 mg/kg/day
  Our dose: 45 mg/kg/day
  45 is between 25 and 50 ✓ SAFE

Final Answer: Administer 337.5 mg per dose, twice daily (morning and evening)

---

Example 2:
Problem: Child weighs 22 kg. Medication: Ibuprofen 10 mg/kg every 6 hours as needed. 
Calculate single dose and verify safety.

Solution:
Step 1: Calculate single dose
  Formula: Weight (kg) × Dosage (mg/kg)
  Calculation: 22 kg × 10 mg/kg = 220 mg

Step 2: Verify frequency is safe
  Dosing interval: Every 6 hours
  Maximum doses per day: 24 hours ÷ 6 hours = 4 doses
  Maximum daily dose: 220 mg × 4 = 880 mg/day

Step 3: Safety check against pediatric limits
  Maximum single dose for children: 400 mg
  Our dose: 220 mg
  220 mg < 400 mg ✓ SAFE
  
  Maximum daily dose for children: 40 mg/kg/day
  Our maximum: 880 mg/day ÷ 22 kg = 40 mg/kg/day
  40 mg/kg/day ≤ 40 mg/kg/day ✓ SAFE (at upper limit)

Step 4: Verification
  Single dose: 220 mg ✓
  Frequency: Every 6 hours ✓
  Max doses: 4 per day ✓
  Within safe range ✓

Final Answer: Administer 220 mg per dose, maximum every 6 hours as needed. 
Do not exceed 4 doses in 24 hours.

---

NOW SOLVE THIS:

Problem: Child weighs 18 kg. Medication: Ceftriaxone 50 mg/kg once daily. 
Available concentration: 100 mg/mL. Calculate dose in mg and volume in mL.
```

### Expected AI Response:

```
SOLUTION:

Step 1: Calculate dose in milligrams
  Formula: Weight (kg) × Dosage (mg/kg/day)
  Calculation: 18 kg × 50 mg/kg/day = 900 mg per day
  
Step 2: Convert mg to mL using concentration
  Available concentration: 100 mg/mL
  Formula: Dose (mg) ÷ Concentration (mg/mL) = Volume (mL)
  Calculation: 900 mg ÷ 100 mg/mL = 9 mL

Step 3: Verification
  Check volume → mg: 9 mL × 100 mg/mL = 900 mg ✓
  Check mg → kg: 900 mg ÷ 18 kg = 50 mg/kg/day ✓

Step 4: Safety check
  Standard Ceftriaxone dosing range: 50-75 mg/kg/day for common infections
  Our dose: 50 mg/kg/day
  50 is at lower end of range ✓ SAFE
  
  Maximum single dose: 2,000 mg (2 grams)
  Our dose: 900 mg
  900 mg < 2,000 mg ✓ SAFE

Step 5: Volume reasonableness check
  9 mL is reasonable for IM/IV injection ✓
  Volume is not excessive for single dose ✓

FINAL ANSWER:
Dose: 900 mg
Volume: 9 mL
Frequency: Once daily
Route: [To be specified by prescriber - typically IV or IM]

DOUBLE-CHECK REQUIRED:
✓ Calculation verified by second clinician
✓ Within safe dosing range
✓ Appropriate volume for administration
✓ Patient allergies checked
✓ Renal function assessed (if applicable)
```

### What Students Should Learn:

**Critical Safety Concepts:**
1. **Always Verify**: Every calculation must be double-checked
2. **Safety Ranges**: Compare final dose to established safe ranges
3. **Reasonableness**: Does the answer make practical sense?
4. **Documentation**: Show all steps for legal/medical records
5. **Units Matter**: mg vs mL vs mg/kg - getting units wrong kills patients

**Why Chain-of-Thought is NON-NEGOTIABLE in Healthcare:**
- ✓ Multiple people can verify the reasoning
- ✓ Catches unit conversion errors
- ✓ Identifies calculation mistakes early
- ✓ Documents decision-making process
- ✓ Enables learning from errors

---

## Comparison: E-Commerce vs Healthcare CoT

| Aspect | E-Commerce Example | Healthcare Example |
|--------|-------------------|-------------------|
| **Stakes** | Money (refundable) | Lives (not refundable) |
| **Error Cost** | Customer complaint | Patient harm/death |
| **Verification** | Nice to have | REQUIRED by law |
| **Precision** | Nearest cent | Exact dosage |
| **Reasoning** | Business logic | Medical protocol |
| **Audience** | Internal team | Multiple healthcare professionals |

**Both require CoT, but healthcare is LIFE-CRITICAL.**

---

## How to Write Effective CoT Prompts

### Template:

```
Context: [Why this problem needs step-by-step thinking]

Objective: [What you're trying to calculate/solve]

Style: [How to show the thinking - like an accountant, scientist, doctor, etc.]

Tone: [Analytical, precise, safety-focused, etc.]

Audience: [Who needs to understand this reasoning]

Response Format: [How to structure the output - tags, numbered steps, etc.]

---

[Problem details]

[Explicit instruction to think step-by-step]
```

### Key Elements:

1. **Explicit Instruction**: Tell AI to "think step-by-step" or "show your work"
2. **Format Tags**: Use `<thinking>` and `<answer>` to separate reasoning from result
3. **Verification Steps**: Always include "check your work" step
4. **Safety Checks**: For critical applications, require safety verification
5. **Examples**: For Few-Shot CoT, provide 2-3 examples first

---

## Common Mistakes Students Make

### Mistake 1: Not Being Specific Enough
❌ **Bad:** "Calculate the shipping cost"
✓ **Good:** "Calculate the shipping cost step-by-step, showing each discount calculation"

### Mistake 2: Forgetting Verification
❌ **Bad:** Just get the final answer
✓ **Good:** Include "Step X: Verify by working backwards"

### Mistake 3: Skipping Safety Checks
❌ **Bad:** Calculate dosage and stop
✓ **Good:** Calculate, verify, check against safe ranges, confirm reasonableness

### Mistake 4: No Clear Format
❌ **Bad:** Let AI structure however it wants
✓ **Good:** Use `<thinking>` and `<answer>` tags for clarity

### Mistake 5: Using CoT for Wrong Problems
❌ **Bad:** "Write a creative story about dragons. Think step-by-step."
✓ **Good:** Use CoT only for logical/mathematical problems

---

## Practice Exercises

### Exercise 1: E-Commerce Returns Refund

**Problem:**
Customer bought 3 items:
- Item A: $45 (non-refundable processing fee: $5)
- Item B: $30 (15% restocking fee)
- Item C: $60 (free returns)

Original shipping: $12
Return shipping (customer paid): $8

Calculate total refund using Chain-of-Thought.

### Exercise 2: Healthcare Dosing

**Problem:**
Adult patient weighs 165 lbs. Medication: Vancomycin 15 mg/kg every 12 hours.
Available concentration: 50 mg/mL.

Convert weight to kg, calculate dose in mg, determine volume in mL, verify safety.

---

## Summary

### Key Takeaways:

1. ✓ **Chain-of-Thought = Showing Your Work**
   - Breaks complex problems into steps
   - Makes reasoning visible and verifiable
   
2. ✓ **Use CoT for:**
   - Multi-step calculations
   - Complex business logic
   - Safety-critical decisions (especially healthcare)
   - Auditable processes

3. ✓ **Always Include:**
   - Step-by-step reasoning
   - Verification steps
   - Safety checks (when applicable)
   - Clear final answer

4. ✓ **Two Methods:**
   - Zero-Shot: "Let's think step-by-step"
   - Few-Shot: Show examples first

5. ✓ **Critical in Healthcare:**
   - Lives depend on accurate calculations
   - Must be verifiable by multiple professionals
   - Regulatory requirement
   - Documents decision-making

### Remember:
**In e-commerce, CoT saves money and improves customer trust.**
**In healthcare, CoT saves lives.**

Both are important, but always treat medical calculations with extra care!

---

## Next Steps

1. Practice with the exercises above
2. Try both Zero-Shot and Few-Shot CoT
3. Compare results with and without CoT
4. See which gives more accurate answers
5. Move on to Tree-of-Thought prompting (next technique)

---

**Questions for Self-Assessment:**

1. When should you use Chain-of-Thought prompting?
2. What's the difference between Zero-Shot and Few-Shot CoT?
3. Why is verification especially important in healthcare?
4. What are the key elements of a good CoT prompt?
5. How do you structure CoT output for clarity?

If you can answer these, you understand Chain-of-Thought prompting! 🎉
