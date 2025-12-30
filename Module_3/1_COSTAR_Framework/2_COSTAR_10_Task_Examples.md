# 10 COSTAR Framework Examples
## Complete Prompt Templates for Different Tasks

---

## Quick Reference Guide

This guide covers 10 essential prompt engineering tasks. Each task includes:
- ✅ Clear explanation of what the task does
- ✅ Real-world use cases  
- ✅ E-commerce example with COSTAR framework
- ✅ Healthcare example with COSTAR framework

**The 10 Tasks:**
1. Classification - Categorizing text into groups
2. Entity Extraction - Pulling specific data from text
3. RAG - Answering from documents with citations
4. Summarization - Condensing long text
5. Code Generation - Creating code from descriptions
6. Chain-of-Thought - Step-by-step reasoning
7. Few-Shot Learning - Teaching by examples
8. Data Transformation - Converting between formats
9. Conversational AI - Multi-turn dialogue
10. Hybrid Multi-Task - Combining multiple tasks

---

---

## TASK 1: Classification 📊

### What is Classification?

**Classification** is the task of categorizing text into predefined groups or labels. Think of it like sorting mail into different boxes - each piece goes into exactly one category.

**How it works:**
The AI reads the input text and assigns it to one of several predefined categories based on its content, sentiment, tone, or other characteristics you define.

**Real-World Examples:**
- **Email filtering:** Spam vs Not Spam vs Important
- **Customer reviews:** Positive, Negative, Neutral, or Mixed
- **Support tickets:** Bug, Feature Request, Question, Complaint
- **Medical triage:** Emergency, Urgent, Routine, Non-Urgent
- **Content moderation:** Safe, Inappropriate, Needs Review

**Simple Example:**
```
Input: "This product is amazing! Best purchase ever!"
Your Categories: POSITIVE | NEGATIVE | NEUTRAL
AI Output: POSITIVE
```

**When to Use Classification:**
✅ You have clear, predefined categories  
✅ You need consistent labeling across many items  
✅ You want to route items to different teams/workflows  
✅ You're organizing large amounts of data  
✅ You need automated decision-making  

**When NOT to Use Classification:**
❌ Categories aren't well-defined  
❌ You need to extract specific data (use Entity Extraction instead)  
❌ You need explanations, not just labels (combine with reasoning)  

---

## Example 1A: Classification - E-commerce Product Review Sentiment

### Task Type: **Text Classification**

```
Context: You are a sentiment analysis system for "ShopEasy," an e-commerce platform 
with 50,000+ daily reviews. The marketing team uses sentiment scores to identify 
product issues and highlight positive feedback.

Objective: Classify customer reviews into sentiment categories to help the team 
prioritize responses and identify trends.

Style: Data analyst providing clear, consistent classifications with brief reasoning

Tone: Objective and analytical, no emotional bias in classification

Audience: Marketing and customer service teams who act on sentiment data

Response Format:
{
  "sentiment": "POSITIVE | NEGATIVE | MIXED | NEUTRAL",
  "confidence": 0.0-1.0,
  "key_reason": "one sentence explanation"
}

---

Review: "I ordered this laptop for my daughter's online classes. The delivery was 
delayed by 2 weeks which was frustrating. However, once it arrived, the product 
quality exceeded expectations. The screen is crystal clear, battery lasts all day, 
and setup was incredibly easy. Despite the shipping issues, I'm happy with the purchase."

Classify this review.
```

**Expected Output:**
```json
{
  "sentiment": "MIXED",
  "confidence": 0.85,
  "key_reason": "Positive product experience offset by negative shipping experience"
}
```

---

## Example 1B: Classification - Healthcare Triage Urgency

### Task Type: **Medical Triage Classification**

```
Context: You are an AI triage system for "CareNow Urgent Care" helping nurses 
prioritize patients in the waiting room. Your classifications determine wait time 
and resource allocation. Patient safety depends on accurate urgency assessment.

Objective: Classify patient presentations into urgency categories based on symptoms 
and vital signs to ensure appropriate prioritization and resource allocation.

Style: Clinical triage nurse - systematic assessment following ESI (Emergency Severity 
Index) guidelines

Tone: Objective and safety-focused, erring on the side of caution for ambiguous cases

Audience: Triage nurses and emergency department staff

Response Format:
{
  "urgency_level": "IMMEDIATE | EMERGENT | URGENT | LESS_URGENT | NON_URGENT",
  "acuity_score": 1-5,
  "recommended_wait": "time in minutes",
  "clinical_reasoning": "brief justification",
  "red_flags": ["list any concerning symptoms"]
}

ESI Levels:
- Level 1 (IMMEDIATE): Life-threatening, requires immediate intervention
- Level 2 (EMERGENT): High risk, confused/lethargic/severe pain, 10 min wait
- Level 3 (URGENT): Stable but needs multiple resources, 30-60 min wait
- Level 4 (LESS_URGENT): One simple intervention needed, 60-120 min wait
- Level 5 (NON_URGENT): No resources needed, could be clinic visit, 120+ min wait

---

Patient Presentation:
Chief Complaint: "Severe headache for 2 hours"

Patient: 42-year-old female
Vital Signs:
- BP: 210/118 mmHg
- HR: 98 bpm
- Temp: 98.6°F (37°C)
- RR: 18 breaths/min
- SpO2: 98% on room air

Additional Information:
- Describes headache as "worst of my life, came on suddenly"
- No history of migraines
- Mild neck stiffness noted
- Photophobia present
- Alert and oriented x4
- No focal neurological deficits observed
- No recent head trauma

Classify this patient's urgency level.
```

**Expected Output:**
```json
{
  "urgency_level": "EMERGENT",
  "acuity_score": 2,
  "recommended_wait": "0-10 minutes",
  "clinical_reasoning": "Hypertensive emergency (BP 210/118) with severe headache and 
  meningeal signs (neck stiffness, photophobia). 'Worst headache of life' + sudden 
  onset raises concern for subarachnoid hemorrhage. Requires immediate evaluation 
  despite stable vital signs.",
  "red_flags": [
    "Severely elevated blood pressure (210/118)",
    "Worst headache of life - concerning for SAH",
    "Sudden onset with neck stiffness and photophobia",
    "No prior history of similar headaches"
  ],
  "immediate_actions": [
    "Place on cardiac monitor",
    "Obtain IV access",
    "Notify physician immediately",
    "Prepare for STAT head CT",
    "NPO (nothing by mouth) - potential for procedures"
  ]
}
```

---

---

## TASK 2: Entity Extraction (Named Entity Recognition) 🏷️

### What is Entity Extraction?

**Entity Extraction** (also called Named Entity Recognition or NER) is the task of identifying and pulling out specific pieces of information from unstructured text. It's like highlighting important information in a document.

**How it works:**
The AI scans through text and identifies entities - specific types of information you're looking for - then extracts them in a structured format.

**Common Entity Types:**
- **People:** Names, job titles, roles → "Dr. Sarah Johnson, Cardiologist"
- **Organizations:** Companies, institutions → "Microsoft", "Harvard Medical School"
- **Locations:** Cities, addresses, countries → "123 Main St, Boston, MA"
- **Dates & Times:** Specific dates, ranges → "December 15, 2024", "last week"
- **Products:** Product names, SKUs, models → "iPhone 15 Pro", "#SKU-12345"
- **Medical:** Medications, diagnoses, procedures → "Lisinopril 20mg", "Type 2 Diabetes"
- **Financial:** Amounts, account numbers → "$1,500", "Invoice #INV-2024-001"

**Simple Example:**
```
Input: "John Smith ordered laptop #LT-5567 on December 15, 2024"

Entities Extracted:
- Customer Name: John Smith
- Product ID: LT-5567
- Product Type: laptop  
- Order Date: December 15, 2024
```

**When to Use Entity Extraction:**
✅ You need to pull specific data fields from unstructured text  
✅ You're populating a database from documents  
✅ You want to route information based on extracted data  
✅ You're automating form filling or data entry  
✅ You need to structure messy text data  

**When NOT to Use Entity Extraction:**
❌ You just need to categorize (use Classification)  
❌ You need full document understanding (use RAG or Summarization)  
❌ Entities aren't clearly definable  

**Key Difference from Classification:**
- **Classification:** "What category does this belong to?" → URGENT  
- **Entity Extraction:** "What specific information is in this?" → Order #12345, December 15, Product: Laptop

---

## Example 2A: Entity Extraction - E-commerce Customer Support

### Task Type: **Named Entity Recognition (NER)**

```
Context: You are processing customer support tickets for "TechGadgets" e-commerce 
platform. The system needs to automatically extract key information to route tickets 
to the right team and prioritize urgent issues.

Objective: Extract structured information from unstructured customer messages to 
enable automated ticket routing and SLA tracking.

Style: Information extraction system - precise and consistent, following defined 
entity schemas

Tone: Neutral and factual, no interpretation beyond extraction

Audience: Support ticket management system (automated processing)

Response Format: Extract entities and return as XML:
<entities>
  <order_number>ORD-XXXXX or NOT_FOUND</order_number>
  <product_name>specific product mentioned</product_name>
  <issue_type>DELIVERY_DELAY|DAMAGED_ITEM|WRONG_ITEM|REFUND_REQUEST|TECHNICAL_ISSUE|GENERAL_INQUIRY</issue_type>
  <urgency>LOW|MEDIUM|HIGH|CRITICAL</urgency>
  <dates>YYYY-MM-DD format, comma-separated if multiple</dates>
</entities>

---

Customer Message: "Hi, I need help with order ORD-558832. I ordered the Samsung 
Galaxy Buds Pro on December 10th and was supposed to receive them by December 15th, 
but they still haven't arrived. The tracking shows the package is stuck at the 
Memphis facility since December 12th. I need these for a trip on December 20th!"

Extract the entities.
```

**Expected Output:**
```xml
<entities>
  <order_number>ORD-558832</order_number>
  <product_name>Samsung Galaxy Buds Pro</product_name>
  <issue_type>DELIVERY_DELAY</issue_type>
  <urgency>HIGH</urgency>
  <dates>2024-12-10, 2024-12-15, 2024-12-12, 2024-12-20</dates>
</entities>
```

---

## Example 2B: Entity Extraction - Healthcare Clinical Notes

### Task Type: **Medical Named Entity Recognition**

```
Context: You are a clinical NLP system for "Memorial Hospital" extracting structured 
data from physician notes for quality reporting, billing, and clinical decision support. 
Accurate extraction is critical for patient safety and regulatory compliance.

Objective: Extract and normalize clinical entities from unstructured physician 
documentation including diagnoses, medications, procedures, vital signs, and lab values.

Style: Medical informatics system - follows standardized medical terminologies 
(ICD-10, RxNorm, LOINC)

Tone: Precise and clinical, no interpretation - extract only what is explicitly stated

Audience: Electronic Health Record (EHR) system, quality reporting databases, billing 
systems

Response Format: Extract entities in structured XML with standard medical codes where applicable:
<clinical_entities>
  <patient_demographics>
    <age></age>
    <gender></gender>
  </patient_demographics>
  <vital_signs>
    <blood_pressure></blood_pressure>
    <heart_rate></heart_rate>
    <temperature></temperature>
    <respiratory_rate></respiratory_rate>
    <oxygen_saturation></oxygen_saturation>
  </vital_signs>
  <medications>
    <medication>
      <name></name>
      <dose></dose>
      <route></route>
      <frequency></frequency>
    </medication>
  </medications>
  <diagnoses>
    <diagnosis>
      <condition></condition>
      <icd10_code></icd10_code>
      <status>PRIMARY|SECONDARY|RULE_OUT</status>
    </diagnosis>
  </diagnoses>
  <laboratory_values>
    <lab_test>
      <test_name></test_name>
      <value></value>
      <units></units>
      <reference_range></reference_range>
      <abnormal_flag>HIGH|LOW|NORMAL</abnormal_flag>
    </lab_test>
  </laboratory_values>
  <procedures_planned></procedures_planned>
  <allergies></allergies>
</clinical_entities>

---

Clinical Note:
Patient: John Smith, 58-year-old male

Chief Complaint: Chest pain

HPI: Patient presents to ED with acute onset substernal chest pressure started 2 hours 
ago, radiating to left arm. Associated with diaphoresis and nausea. Pain 8/10. Denies 
SOB. No relief with rest.

PMH: Hypertension, Type 2 Diabetes, Hyperlipidemia

Current Medications:
- Lisinopril 20mg PO daily
- Metformin 1000mg PO BID
- Atorvastatin 40mg PO QHS

Allergies: Penicillin (rash)

Vital Signs:
BP: 145/92 mmHg
HR: 102 bpm
Temp: 98.4°F
RR: 20 breaths/min
SpO2: 97% on room air

Labs:
Troponin I: 1.8 ng/mL (reference: <0.04 ng/mL) - ELEVATED
BNP: 180 pg/mL (reference: <100 pg/mL) - ELEVATED
Creatinine: 1.2 mg/dL (reference: 0.7-1.3 mg/dL) - NORMAL

EKG: ST-segment elevation in leads II, III, aVF

Assessment:
1. Acute ST-Elevation Myocardial Infarction (STEMI) - INFERIOR WALL
2. Type 2 Diabetes Mellitus - controlled
3. Hypertension - uncontrolled
4. Hyperlipidemia - on treatment

Plan:
- STAT cardiology consult
- Activate cath lab for emergent PCI
- Aspirin 324mg PO given
- Heparin bolus 5000 units IV given
- Transfer to CCU

Extract all clinical entities from this note.
```

**Expected Output:**
```xml
<clinical_entities>
  <patient_demographics>
    <age>58</age>
    <gender>Male</gender>
  </patient_demographics>
  
  <chief_complaint>Chest pain</chief_complaint>
  
  <vital_signs>
    <blood_pressure>145/92 mmHg</blood_pressure>
    <heart_rate>102 bpm</heart_rate>
    <temperature>98.4°F</temperature>
    <respiratory_rate>20 breaths/min</respiratory_rate>
    <oxygen_saturation>97% on room air</oxygen_saturation>
  </vital_signs>
  
  <medications>
    <medication>
      <name>Lisinopril</name>
      <dose>20mg</dose>
      <route>PO</route>
      <frequency>daily</frequency>
    </medication>
    <medication>
      <name>Metformin</name>
      <dose>1000mg</dose>
      <route>PO</route>
      <frequency>BID (twice daily)</frequency>
    </medication>
    <medication>
      <name>Atorvastatin</name>
      <dose>40mg</dose>
      <route>PO</route>
      <frequency>QHS (at bedtime)</frequency>
    </medication>
    <medication>
      <name>Aspirin</name>
      <dose>324mg</dose>
      <route>PO</route>
      <frequency>STAT (one-time dose given)</frequency>
    </medication>
    <medication>
      <name>Heparin</name>
      <dose>5000 units</dose>
      <route>IV</route>
      <frequency>bolus (one-time dose given)</frequency>
    </medication>
  </medications>
  
  <diagnoses>
    <diagnosis>
      <condition>Acute ST-Elevation Myocardial Infarction (STEMI), Inferior Wall</condition>
      <icd10_code>I21.19</icd10_code>
      <status>PRIMARY</status>
    </diagnosis>
    <diagnosis>
      <condition>Type 2 Diabetes Mellitus, controlled</condition>
      <icd10_code>E11.9</icd10_code>
      <status>SECONDARY</status>
    </diagnosis>
    <diagnosis>
      <condition>Hypertension, uncontrolled</condition>
      <icd10_code>I10</icd10_code>
      <status>SECONDARY</status>
    </diagnosis>
    <diagnosis>
      <condition>Hyperlipidemia</condition>
      <icd10_code>E78.5</icd10_code>
      <status>SECONDARY</status>
    </diagnosis>
  </diagnoses>
  
  <laboratory_values>
    <lab_test>
      <test_name>Troponin I</test_name>
      <value>1.8</value>
      <units>ng/mL</units>
      <reference_range>&lt;0.04 ng/mL</reference_range>
      <abnormal_flag>HIGH</abnormal_flag>
    </lab_test>
    <lab_test>
      <test_name>BNP (B-type Natriuretic Peptide)</test_name>
      <value>180</value>
      <units>pg/mL</units>
      <reference_range>&lt;100 pg/mL</reference_range>
      <abnormal_flag>HIGH</abnormal_flag>
    </lab_test>
    <lab_test>
      <test_name>Creatinine</test_name>
      <value>1.2</value>
      <units>mg/dL</units>
      <reference_range>0.7-1.3 mg/dL</reference_range>
      <abnormal_flag>NORMAL</abnormal_flag>
    </lab_test>
  </laboratory_values>
  
  <diagnostic_findings>
    <finding>
      <test>EKG</test>
      <result>ST-segment elevation in leads II, III, aVF</result>
      <interpretation>Consistent with inferior wall STEMI</interpretation>
    </finding>
  </diagnostic_findings>
  
  <procedures_planned>
    <procedure>Emergent PCI (Percutaneous Coronary Intervention)</procedure>
    <procedure>Cardiac Catheterization</procedure>
    <urgency>EMERGENT</urgency>
    <status>Cath lab activated</status>
  </procedures_planned>
  
  <consultations>
    <consult>
      <specialty>Cardiology</specialty>
      <urgency>STAT</urgency>
    </consult>
  </consultations>
  
  <allergies>
    <allergy>
      <allergen>Penicillin</allergen>
      <reaction>Rash</reaction>
      <severity>MODERATE</severity>
    </allergy>
  </allergies>
  
  <disposition>
    <destination>CCU (Cardiac Care Unit)</destination>
    <status>Transfer pending after emergent PCI</status>
  </disposition>
</clinical_entities>
```

---

---

## TASK 3: RAG (Retrieval Augmented Generation) 📚

### What is RAG?

**RAG** stands for Retrieval Augmented Generation. It's the task of answering questions using specific documents you provide, rather than relying on the AI's built-in knowledge. Think of it as giving the AI a textbook and asking it to answer questions based ONLY on what's in that textbook.

**How it works:**
1. **Retrieval:** You provide relevant documents (product manuals, medical guidelines, company policies)
2. **Augmentation:** AI searches these documents for relevant information
3. **Generation:** AI generates an answer based ONLY on what it found in the documents
4. **Citation:** AI tells you which document/section the answer came from

**Why RAG is Important:**

The problem with regular AI Q&A:
```
Question: "What's the return policy for your store?"
Regular AI: [Makes up a generic answer based on training data - might be wrong!]
```

The solution with RAG:
```
Documents Provided: Your actual return policy document
Question: "What's the return policy for your store?"
RAG AI: "According to the Return Policy document (Section 2), items can be 
returned within 30 days with receipt for full refund. [Source: Return_Policy.pdf]"
```

**Key Benefits:**
- ✅ **Accuracy:** Answers come from your actual documents
- ✅ **Currency:** Always up-to-date (you control the documents)
- ✅ **Trust:** Provides source citations
- ✅ **No Hallucination:** AI can't make stuff up - it must cite sources
- ✅ **Verifiable:** You can check the source document

**Real-World Examples:**
- **Customer Support:** Answer questions using product manuals
- **Medical Practice:** Clinical decisions using medical guidelines
- **Legal Research:** Case analysis using case law documents
- **HR Chatbots:** Answer employee questions using company policies
- **Technical Support:** Troubleshooting using technical documentation

**Simple Example:**

*Documents Provided:*
```
Product Manual - SmartWatch Pro:
- Battery Life: Up to 48 hours with normal use
- Water Resistance: IP68 rated, safe up to 1.5 meters for 30 minutes
- Compatibility: iOS 14+ and Android 10+
```

*Question:* "Can I swim with this watch?"

*RAG Answer:* "Yes, you can swim with the SmartWatch Pro. According to the product 
manual, it has an IP68 water resistance rating and is safe to use up to 1.5 meters 
depth for 30 minutes. [Source: Product Manual, Specifications section]"

*Without RAG (risky):* "Most smartwatches are water-resistant..." [AI might guess wrong!]

**When to Use RAG:**
✅ You have authoritative source documents  
✅ Accuracy is absolutely critical (medical, legal, financial)  
✅ Information changes frequently (product specs, policies)  
✅ You need to cite sources for transparency  
✅ You want to prevent AI from "hallucinating" answers  
✅ Regulatory compliance requires source attribution  

**When NOT to Use RAG:**
❌ General knowledge questions (normal Q&A is fine)  
❌ You don't have source documents  
❌ Creative tasks where hallucination is okay  

**Key Differences:**

| Regular Q&A | RAG |
|-------------|-----|
| Uses AI's training data | Uses YOUR documents |
| May be outdated | Always current (you update docs) |
| No citations | Always cites sources |
| Can hallucinate | Must cite or say "not found" |
| General knowledge | Specific to your documents |

**Important RAG Rule:**
If the answer isn't in the provided documents, the AI must explicitly say so. For example: "This information is not covered in the provided product manual. Please contact support for assistance."

---

## Example 3A: RAG - E-commerce Multi-Document Product Decision

### Task Type: **Complex Multi-Document RAG with Source Attribution**

```
Context: You are an AI shopping assistant for "TechMart," a major electronics retailer. 
You help customers make informed purchase decisions by analyzing multiple product 
specifications, customer reviews, and policy documents. You must synthesize information 
from multiple sources and cite each source when making claims.

Objective: Answer complex customer questions by retrieving relevant information from 
multiple documents, synthesizing insights, and providing source-attributed recommendations. 
Never hallucinate - if information isn't in the provided documents, explicitly state this.

Style: Expert tech consultant who cross-references multiple sources, like a researcher 
writing a well-cited report

Tone: Knowledgeable and trustworthy, balanced (presents both pros and cons), helpful 
in decision-making

Audience: Tech-savvy customer researching a significant purchase ($1000+), wants 
detailed comparison before buying

Response Format:
1. Direct answer to question (2-3 sentences)
2. Supporting evidence with citations [Doc#, Section]
3. Relevant tradeoffs or considerations
4. Final recommendation with confidence level
5. List of cited sources at end

---

Retrieved Documents:

[Doc1: Product Specification - UltraBook Pro 15]
Section A - Performance:
- Processor: Intel Core i7-13700H (14 cores, up to 5.0 GHz)
- RAM: 32GB DDR5 (expandable to 64GB)
- Storage: 1TB NVMe SSD (2x M.2 slots, second slot empty)
- Graphics: NVIDIA RTX 4060 (8GB VRAM)
- Battery: 90Wh, claimed 8-10 hours mixed use

Section B - Display & Build:
- Screen: 15.6" OLED, 2880x1620, 120Hz, 100% DCI-P3
- Weight: 4.2 lbs (1.9 kg)
- Ports: 2x Thunderbolt 4, 2x USB-A 3.2, HDMI 2.1, SD card reader
- Build: Aluminum unibody, MIL-STD-810H tested

Section C - Thermal & Noise:
- Cooling: Dual-fan vapor chamber design
- Noise levels: 32dB idle, 45dB under load
- Thermal throttling: Rare, maintains boost clocks well

[Doc2: Customer Reviews - UltraBook Pro 15, Average 4.3/5 stars, 847 reviews]
Top Positive Themes (362 mentions):
- "Excellent build quality and premium feel"
- "Display is stunning, best I've seen for content creation"
- "Performance handles video editing smoothly (4K timelines)"
- "Thunderbolt 4 ports make docking station setup seamless"

Top Negative Themes (127 mentions):
- "Battery life disappoints - getting 5-6 hours max, not 8-10"
- "Runs hot during sustained workloads (chassis gets warm)"
- "Webcam quality is mediocre (720p, grainy in low light)"
- "Price is steep compared to competitors with similar specs"

Mixed Feedback (89 mentions):
- "Fans are audible under load but not annoying"
- "Heavier than expected but feels sturdy"

[Doc3: Competitor Comparison - TechInsights Report]
UltraBook Pro 15 vs. CreativeBook X1 vs. WorkStation Elite:

Performance Benchmarks:
- Video Rendering (4K): UltraBook Pro 15: 8.2 min | CreativeBook X1: 9.1 min | WorkStation Elite: 7.8 min
- Battery Life (real-world): UltraBook Pro 15: 5.5 hrs | CreativeBook X1: 7.2 hrs | WorkStation Elite: 4.8 hrs
- Display Color Accuracy: UltraBook Pro 15: ΔE < 1.0 | CreativeBook X1: ΔE < 1.5 | WorkStation Elite: ΔE < 2.0

Price Comparison (similar configs):
- UltraBook Pro 15: $1,899
- CreativeBook X1: $1,699
- WorkStation Elite: $2,199

[Doc4: Warranty & Return Policy]
- Standard warranty: 1 year parts and labor
- Extended warranty available: 3-year for $299
- Return policy: 30 days, must be in original condition, 15% restocking fee if opened
- Price match: Within 14 days of purchase if competitor advertises lower price

[Doc5: Technical Support FAQ]
Q: Can I upgrade RAM myself?
A: Yes, RAM is user-accessible. Two SO-DIMM slots support up to 64GB total (2x32GB).

Q: Does it support external GPU?
A: Yes, via Thunderbolt 4 ports. Tested with most eGPU enclosures.

Q: What's the charging requirement?
A: 180W USB-C PD charger included. Can slow-charge with 65W+ USB-C chargers but won't charge under load.

---

Customer Question:
"I'm a video editor working with 4K footage in DaVinci Resolve. I need something 
portable for on-location work but powerful enough to handle color grading. I'm 
deciding between the UltraBook Pro 15 and CreativeBook X1. My main concerns are: 
(1) Will the battery actually last through a 6-hour shoot day? (2) Is the display 
good enough for color-critical work? (3) Can I add more storage later? Should I 
get the UltraBook Pro or save $200 with the CreativeBook X1?"

Provide comprehensive answer with source citations.
```

**Expected Output:**
```
RECOMMENDATION: UltraBook Pro 15, but with realistic expectations on battery life.

BATTERY REALITY CHECK:
The claimed 8-10 hours will NOT meet your needs for a 6-hour shoot day under real-world 
video editing workload. Customer reviews consistently report 5-6 hours maximum [Doc2, 
Negative Themes], and competitive testing shows 5.5 hours actual usage [Doc3, Battery 
Life]. For DaVinci Resolve color grading, expect closer to 4-5 hours due to GPU usage. 
You'll need to bring the 180W charger or use slower USB-C charging during breaks [Doc5, 
Charging].

DISPLAY FOR COLOR WORK:
The display is EXCELLENT for color-critical work. The 15.6" OLED covers 100% DCI-P3 
color space [Doc1, Section B] with industry-leading color accuracy of ΔE < 1.0 [Doc3, 
Display Accuracy]. This is better than the CreativeBook X1 (ΔE < 1.5) and professional-grade 
for color grading. Customer reviews specifically praise it for content creation [Doc2, 
Positive Themes: "best I've seen for content creation"].

STORAGE EXPANSION:
Yes, storage is expandable. The laptop has 2x M.2 slots; one is populated with the 
1TB SSD, and the second slot is empty [Doc1, Section A]. You can add another NVMe 
SSD (up to 2TB or 4TB) yourself without voiding warranty.

PERFORMANCE COMPARISON:
Video rendering performance is nearly identical - UltraBook Pro (8.2 min) vs CreativeBook 
X1 (9.1 min) for 4K renders [Doc3, Benchmarks]. The 11% difference won't significantly 
impact your workflow. However, the UltraBook Pro has better color accuracy and thermal 
management [Doc1, Section C: maintains boost clocks well].

TRADEOFFS TO CONSIDER:
Pros of UltraBook Pro:
- Superior display color accuracy (critical for your work)
- Better sustained performance (thermal management)
- More I/O flexibility (Thunderbolt 4, SD card reader) [Doc1, Section B]

Cons of UltraBook Pro:
- $200 more expensive than CreativeBook X1 [Doc3, Pricing]
- Shorter battery life (5.5 hrs vs 7.2 hrs) [Doc3, Battery]
- Runs warm under load [Doc2, Negative Themes]

FINAL VERDICT:
Choose the UltraBook Pro 15. For color-critical work, the superior display accuracy 
(ΔE < 1.0) justifies the $200 premium. The CreativeBook X1's longer battery life 
(7.2 hrs) is appealing, but even that won't cover a full 6-hour shoot day under 
editing workload - you'll need to charge regardless.

RECOMMENDATION: Buy the UltraBook Pro + extended 3-year warranty ($299) [Doc4] given 
the thermal demands of video editing. Budget for a portable USB-C power bank (65W+) 
for on-location charging [Doc5].

Confidence: HIGH (based on 5 source documents, 847 customer reviews, and competitive 
benchmarks)

SOURCES CITED:
[Doc1] - UltraBook Pro 15 Product Specifications
[Doc2] - Customer Reviews (847 reviews, 4.3/5 stars)
[Doc3] - TechInsights Competitive Benchmark Report
[Doc4] - Warranty & Return Policy Documentation
[Doc5] - Technical Support FAQ
```

---

## Example 3B: RAG (Retrieval Augmented Generation) - Healthcare

### Task Type: **Clinical Decision Support with Evidence Synthesis**

```
Context: You are a clinical decision support system for primary care physicians at 
"HealthFirst Medical Group." Doctors query you with patient scenarios, and you retrieve 
relevant information from clinical guidelines, research literature, and formulary 
databases to provide evidence-based recommendations. All recommendations must cite 
authoritative medical sources.

Objective: Synthesize information from multiple clinical sources to provide evidence-based 
treatment recommendations with proper medical citations. Flag any conflicting evidence 
or guidelines. Never recommend treatments not supported by retrieved documents.

Style: Clinical decision support tool - systematic, evidence-based, follows medical 
reasoning hierarchy (guidelines → trials → expert opinion)

Tone: Professional medical communication, appropriately cautious about uncertainty, 
clear about strength of evidence

Audience: Primary care physicians making treatment decisions

Response Format:
1. Clinical Summary (2-3 sentences)
2. Evidence-Based Recommendations (tiered by strength of evidence)
3. Key Considerations (drug interactions, contraindications, monitoring)
4. Alternative Options (if first-line fails or is contraindicated)
5. References (formatted as [Source#: Citation])
6. Red Flags (when to escalate or refer)

---

Retrieved Clinical Documents:

[Doc1: ADA Clinical Practice Guidelines 2024 - Type 2 Diabetes Management]
First-Line Therapy for Type 2 Diabetes:
- Metformin remains first-line pharmacologic therapy (Grade A evidence)
- Starting dose: 500mg once or twice daily with meals
- Titrate gradually over 2-4 weeks to minimize GI side effects
- Target dose: 2000mg daily (divided doses) for most patients
- Contraindications: eGFR <30 mL/min/1.73m², acute metabolic acidosis
- Monitor: Renal function every 6-12 months, B12 levels annually

If HbA1c Not at Goal After 3 Months on Metformin:
- Add second agent based on comorbidities:
  * ASCVD or high risk → GLP-1 RA or SGLT2i (both have CV benefit)
  * Heart failure → SGLT2i preferred
  * CKD → SGLT2i preferred
  * Need to minimize hypoglycemia → DPP-4i or GLP-1 RA
  * Cost is major barrier → Sulfonylurea (generic available)

[Doc2: Clinical Trial - EMPA-REG OUTCOME Study]
Study Design: 7,020 patients with T2DM and established CVD
Intervention: Empagliflozin (SGLT2 inhibitor) vs placebo, on top of standard care
Results:
- 14% reduction in 3-point MACE (CV death, MI, stroke) - p=0.04
- 38% reduction in CV death - p<0.001
- 35% reduction in hospitalization for heart failure - p=0.002
Adverse Events:
- Increased genital infections (6.4% vs 1.8%)
- No increase in fractures or amputations in this trial
Conclusion: Strong cardiovascular benefit in T2DM patients with established CVD

[Doc3: Formulary Database - HealthFirst Preferred Drug List]
Tier 1 (Lowest copay - $10):
- Metformin (generic)
- Glipizide (sulfonylurea, generic)

Tier 2 (Medium copay - $40):
- Empagliflozin (SGLT2i, brand: Jardiance)
- Dulaglutide (GLP-1 RA, brand: Trulicity)

Tier 3 (High copay - $80):
- Semaglutide injectable (GLP-1 RA, brand: Ozempic)

Prior Authorization Required:
- GLP-1 receptor agonists: Requires documented trial of metformin + one other agent
- SGLT2 inhibitors: Approved for patients with CVD, HF, or CKD without PA

[Doc4: Drug Interaction Database]
Metformin Interactions:
- Contrast dye (iodinated): HOLD metformin 48h before and after procedure; restart 
  only after confirming normal renal function
- Alcohol: Increases risk of lactic acidosis; advise moderation
- Topiramate: May increase metformin levels; monitor for side effects

Empagliflozin Interactions:
- Diuretics: Increased risk of volume depletion; may need diuretic dose adjustment
- Insulin/Sulfonylureas: Increased hypoglycemia risk; reduce insulin/SU dose by 
  10-20% when initiating
- NSAIDs: May reduce GFR; monitor renal function more frequently

[Doc5: Patient Safety Alert - FDA Warning]
SGLT2 Inhibitors - Diabetic Ketoacidosis Risk:
Rare but serious cases of DKA reported, including euglycemic DKA (normal blood glucose). 
Educate patients on symptoms: nausea, vomiting, abdominal pain, fatigue, difficulty breathing.
Risk factors: Very low carb diet, acute illness, prolonged fasting, surgery
Action: Discontinue SGLT2i if DKA suspected, check ketones regardless of glucose level

[Doc6: Renal Dosing Guidelines]
Metformin:
- eGFR ≥45: No dose adjustment needed
- eGFR 30-44: Maximum 1000mg daily, monitor renal function every 3 months
- eGFR <30: Contraindicated

Empagliflozin:
- eGFR ≥45: 10mg or 25mg daily
- eGFR 30-44: 10mg daily (limited efficacy for glycemic control but maintains CV/renal benefit)
- eGFR <30: Not recommended for glycemic control; may continue for CV benefit if already 
  taking (off-label, specialist consultation recommended)

---

Patient Case:
"58-year-old male, newly diagnosed Type 2 diabetes. HbA1c: 8.2%, fasting glucose: 165 mg/dL.

Medical History:
- Hypertension (controlled on lisinopril 10mg daily)
- Coronary artery disease (MI 2 years ago, on aspirin + atorvastatin)
- eGFR: 58 mL/min/1.73m² (Stage 3a CKD)
- BMI: 32

Current medications: Aspirin 81mg, Atorvastatin 40mg, Lisinopril 10mg

Patient is motivated, willing to make lifestyle changes. Insurance: Standard plan, 
cost-conscious but can afford moderate copays if necessary.

What is the evidence-based treatment approach? Consider his cardiovascular history 
and kidney function."

Provide clinical recommendation with full source citations.
```

**Expected Output:**
```
CLINICAL SUMMARY:
58-year-old male with newly diagnosed T2DM (HbA1c 8.2%) and significant ASCVD (prior MI), 
Stage 3a CKD, requires therapy that addresses both glycemic control and cardiovascular 
risk reduction. Evidence strongly supports dual therapy with metformin plus SGLT2 
inhibitor for this patient profile.

EVIDENCE-BASED RECOMMENDATIONS:

FIRST-LINE THERAPY (Start Both Simultaneously):

1. Metformin 500mg twice daily with meals
   - Rationale: Remains first-line therapy per ADA guidelines (Grade A) [Doc1: ADA 
     Guidelines 2024]
   - Dosing: Start 500mg BID, titrate to 1000mg BID over 2-4 weeks if tolerated 
     [Doc1: Dosing]
   - Renal adjustment: eGFR 58 allows full dose; will need dose reduction to 1000mg/day 
     max if eGFR drops to 30-44 range [Doc6: Renal Dosing]
   - Strength of Evidence: Grade A

2. Empagliflozin (Jardiance) 10mg daily
   - Rationale: Patient has established ASCVD (prior MI), making SGLT2i strongly indicated 
     beyond just glycemic control [Doc1: Add second agent for ASCVD]
   - CV Benefit: EMPA-REG trial showed 14% MACE reduction, 38% CV death reduction in 
     patients exactly like this (T2DM + CVD) [Doc2: EMPA-REG Results]
   - Renal protection: SGLT2i preferred for CKD; provides both CV and renal benefit 
     [Doc1: CKD indication]
   - Formulary: Tier 2 ($40 copay), NO prior authorization needed for patients with 
     CVD [Doc3: Formulary]
   - Strength of Evidence: Grade A for CV outcomes

KEY CONSIDERATIONS:

Drug Interactions & Monitoring:
- ACE Inhibitor (Lisinopril) + SGLT2i: Monitor volume status; empagliflozin can cause 
  diuresis. Consider holding lisinopril if patient develops acute illness with poor 
  PO intake [Doc4: Diuretic interaction]
- Baseline labs needed: Renal panel, urinalysis (check for UTI before starting SGLT2i)
- Follow-up labs (3 months): HbA1c, comprehensive metabolic panel, B12 level [Doc1: 
  Metformin monitoring]
- Renal monitoring: Check eGFR every 6 months given Stage 3a CKD [Doc1: Monitor renal 
  function]

Patient Education - Critical Safety Points:
1. SGLT2i DKA Risk: Educate on symptoms (N/V, abdominal pain, SOB) even if glucose 
   normal. Stop empagliflozin and seek care if suspected [Doc5: FDA Warning]
2. Genital infections: Increased risk (6.4% vs 1.8%); practice good hygiene [Doc2: 
   Adverse events]
3. Metformin GI effects: Take with food, expect initial bloating/diarrhea that usually 
   improves [Doc1: GI side effects]
4. Contrast procedures: Hold metformin 48h before/after if receiving IV contrast; 
   restart only after confirming stable renal function [Doc4: Contrast interaction]

ALTERNATIVE OPTIONS:

If Patient Cannot Afford Empagliflozin ($40/month):
- Consider GLP-1 RA (dulaglutide, Tier 2) BUT requires prior authorization (must 
  document metformin trial first) [Doc3: PA requirements]
- Pros of GLP-1: CV benefit, weight loss
- Cons: Requires PA delay, injection (vs oral), GI side effects common

If Cost is Prohibitive for Any Tier 2 Medication:
- Glipizide (sulfonylurea, Tier 1 - $10) is alternative [Doc3: Tier 1]
- BUT: No CV benefit, causes hypoglycemia and weight gain, not preferred given patient's 
  CV history [Doc1: sulfonylurea as cost barrier option]
- Only use if truly no other option financially

RED FLAGS - When to Refer/Escalate:

Nephrology Referral if:
- eGFR drops below 45 (need specialist co-management for advanced CKD)
- Proteinuria develops (check baseline UACR)

Endocrinology Referral if:
- HbA1c not at goal (<7% for most, <6.5% if no hypoglycemia risk) after 3 months on 
  dual therapy
- Recurrent hypoglycemia
- Patient develops complications requiring intensive management

FOLLOW-UP PLAN:
- Week 2-4: Phone check-in for GI tolerability, volume status
- Month 3: In-person visit with HbA1c, CMP, B12
- Month 6: Renal function check, assess for SGLT2i adverse effects
- Ongoing: Annual foot exam, eye exam, UACR

EXPECTED OUTCOMES:
With metformin + empagliflozin + lifestyle:
- Anticipated HbA1c reduction: 1.5-2.0% (target <7%)
- CV benefit: 14% MACE reduction over next 3-5 years
- CKD progression: Slowed by SGLT2i renal protective effects
- Weight: Likely 3-5 kg reduction (both medications aid weight loss)

REFERENCES:
[Doc1] American Diabetes Association. Standards of Care in Diabetes—2024. Clinical 
       Practice Guidelines for Type 2 Diabetes Management.
[Doc2] EMPA-REG OUTCOME Trial. Empagliflozin cardiovascular outcomes in patients with 
       type 2 diabetes and established cardiovascular disease. N=7,020.
[Doc3] HealthFirst Medical Group Formulary Database, Updated 2024.
[Doc4] Drug Interaction Database - Metformin and Empagliflozin interaction profiles.
[Doc5] FDA Safety Alert: SGLT2 Inhibitors and Diabetic Ketoacidosis Risk (May 2023).
[Doc6] Renal Dosing Guidelines for Diabetes Medications in Chronic Kidney Disease.

STRENGTH OF RECOMMENDATION: Strong (Grade A evidence for both agents in this patient 
population)

CONFIDENCE LEVEL: HIGH (Multiple guideline + RCT support for this specific patient 
profile: T2DM + ASCVD + CKD)
```

---

---

## TASK 4: Summarization 📝

### What is Summarization?

**Summarization** is the task of condensing long text into a shorter version while keeping the most important information. Think of it like creating "TL;DR" (Too Long; Didn't Read) versions of documents.

**How it works:**
The AI reads through long text, identifies the key points, main ideas, and critical details, then rewrites them in a more concise form - removing redundancy and less important information.

**Two Main Types:**

1. **Extractive Summarization:**
   - Pulls exact sentences from the original text
   - Like highlighting key sentences
   - Example: Copy the 3 most important sentences from a 10-paragraph article

2. **Abstractive Summarization:**
   - Rewrites the content in new words
   - More natural and readable
   - Example: Read a 500-word review and write a 50-word summary in your own words
   - *This is what modern AI typically does*

**Real-World Examples:**
- **Meeting Notes** → Action items and decisions (15 pages → 1 page)
- **Medical Records** → Patient discharge summary (detailed notes → patient handout)
- **Research Papers** → Abstract (50 pages → 300 words)
- **Customer Feedback** → Executive summary (1000 reviews → key themes)
- **Legal Documents** → Case brief (200 pages → 5-page summary)
- **News Articles** → Headlines + key facts

**Simple Example:**

*Original (150 words):*
```
Our company held its annual meeting on December 15th at the downtown conference 
center. The CEO presented Q4 results, which showed a 12% increase in revenue 
compared to last year, primarily driven by strong performance in the electronics 
division. However, the home goods division saw a 5% decline. The CFO discussed 
the budget for next year, proposing a 20% increase in marketing spend to boost 
brand awareness. The CTO announced plans to migrate all systems to cloud 
infrastructure by June 2025, which is expected to reduce operating costs by 
15%. There was also a discussion about expanding into three new international 
markets. The HR director reported that employee satisfaction scores increased 
to 8.2 out of 10, and turnover decreased by 3%. The meeting concluded with a 
Q&A session addressing employee questions about remote work policies.
```

*Summary (50 words):*
```
Annual meeting on Dec 15 showed 12% revenue growth led by electronics. Company 
plans 20% marketing increase, cloud migration by June 2025 (15% cost savings), 
and international expansion. Employee satisfaction improved to 8.2/10 with lower 
turnover. Home goods division needs attention with 5% decline.
```

**Key Principles of Good Summarization:**
1. **Preserve Critical Info:** Keep the most important facts, numbers, decisions
2. **Remove Redundancy:** If it's said twice, include it once
3. **Maintain Accuracy:** Don't change the meaning or introduce new information
4. **Match Requested Length:** If asked for 2 sentences, give 2 sentences
5. **Prioritize:** What would the reader NEED to know vs NICE to know?

**When to Use Summarization:**
✅ Text is too long for quick reading  
✅ You need executive summaries for busy stakeholders  
✅ You want key points without details  
✅ Creating patient-friendly versions of technical documents  
✅ Condensing multiple sources into one overview  
✅ Time-sensitive information needs (briefings, updates)  

**When NOT to Use Summarization:**
❌ You need complete details (summarization loses nuance)  
❌ Every detail is important (legal contracts, dosing instructions)  
❌ Text is already concise  
❌ You need specific data extraction (use Entity Extraction instead)  

**Common Summarization Formats:**
- **Executive Summary:** 1-2 paragraphs for leadership
- **Abstract:** Structured summary for research papers
- **Bullet Points:** Key takeaways in list format
- **TL;DR:** One-sentence summary
- **Layered Summary:** Multiple levels (1 sentence, 1 paragraph, 1 page)

**Important Considerations:**

**Length Specification:**
Always specify how long you want the summary:
- "Summarize in 2 sentences"
- "Provide a 100-word summary"
- "Condense to one paragraph"
- "Create a 3-bullet-point summary"

**Target Audience:**
Summaries should match the reader's knowledge level:
- Executive summary → High-level business language
- Patient summary → Simple, non-technical language
- Technical summary → Industry-specific terminology okay

**Example - Audience Matters:**

*Same Medical Report, Different Summaries:*

For Doctor:
```
58yo M, T2DM, HbA1c 8.2%, eGFR 58. Started metformin + empagliflozin per ADA 
guidelines. ASCVD history requires SGLT2i for CV protection. F/U in 3 months.
```

For Patient:
```
You have diabetes with blood sugar that's a bit high. We're starting you on 
two medications to help control it and protect your heart. You'll come back 
in 3 months to check how it's working.
```

**Key Difference from Other Tasks:**

| Task | Purpose |
|------|---------|
| **Summarization** | Make it shorter, keep key points |
| Classification | Put it in a category |
| Entity Extraction | Pull out specific data |
| RAG | Answer questions using documents |

---

## Example 4: Summarization - Medical Patient Notes

### Task Type: **Text Summarization**

```
Context: You are a clinical documentation specialist at Memorial Hospital, helping 
physicians create patient-friendly discharge summaries. These summaries must be clear 
enough for patients to understand but accurate enough for medical-legal purposes.

Objective: Convert detailed clinical notes into a patient discharge summary that 
explains diagnosis, treatment, and follow-up care in accessible language.

Style: Healthcare educator - translates medical terminology into plain English while 
maintaining accuracy

Tone: Reassuring and informative, emphasizing patient's progress and clear next steps

Audience: Patient (67-year-old, high school education, some health anxiety, living 
alone)

Response Format:
1. "What Happened" - diagnosis in plain language (3-4 sentences)
2. "Your Treatment" - what we did in hospital (bullet points)
3. "Your Medications" - simple table with Name, Purpose, How to Take
4. "Warning Signs" - when to call doctor vs. when to go to ER (clear lists)
5. "Follow-up" - specific appointment info
Total: One page, large font, simple language

---

Clinical Notes:
Patient: Maria Rodriguez, 45-year-old female
Chief Complaint: Persistent headaches for 3 weeks
History: Bilateral temporal headaches, worse AM, improving throughout day. Pain 6/10 
average. Mild nausea, no vomiting. No visual changes. No fever. Works as accountant, 
recently increased hours (tax season). Sleep reduced to 5-6 hours nightly. Coffee 
intake increased to 4 cups daily. Denies trauma. No family history of migraines.
Physical Exam: Vitals WNL. BP 128/82. Neurological exam unremarkable. No focal 
deficits. Fundoscopic exam normal. Neck supple, no meningismus.
Assessment: Tension-type headaches likely related to stress, inadequate sleep, 
possible caffeine dependence.
Plan: 
1. Sleep hygiene - target 7-8 hours
2. Gradual caffeine reduction
3. Stress management techniques
4. OTC ibuprofen PRN
5. F/U 2 weeks if symptoms persist
6. Return if red flags: sudden severe HA, fever, vision changes, confusion

Generate patient discharge summary.
```

**Expected Output:**
```
DISCHARGE SUMMARY - Maria Rodriguez

WHAT HAPPENED:
You came to see us because you've been having headaches for the past 3 weeks. 
After examining you and reviewing your symptoms, we determined these are tension 
headaches. The good news is there's nothing serious causing them - no infection, 
no problems with your brain. These headaches are related to stress from work, 
not getting enough sleep, and possibly drinking too much coffee.

YOUR TREATMENT:
• Complete physical examination - everything looked normal
• Checked your blood pressure - normal at 128/82
• Neurological examination - no concerns found
• No prescription medications needed at this time

YOUR MEDICATIONS:

| Medicine | What It's For | How to Take | Important Notes |
|----------|---------------|-------------|-----------------|
| Ibuprofen (Advil) | Pain relief for headaches | 400mg when headache starts, can repeat every 6 hours if needed | Don't take more than 3 times per day. Take with food |

YOUR NEXT STEPS:
1. Get 7-8 hours of sleep each night (currently you're only getting 5-6)
2. Reduce coffee slowly - cut down by 1 cup per week until you're at 2 cups per day
3. Try stress reduction: deep breathing, short walks during work breaks
4. Use ibuprofen when you have a headache

WARNING SIGNS - Call Your Doctor If:
• Headaches don't improve in 2 weeks
• Headaches are getting worse
• You have headaches on more days than before

WARNING SIGNS - Go to Emergency Room If:
• Sudden, severe headache (worst of your life)
• Headache with fever and stiff neck
• Headache with vision changes or confusion
• Headache after a head injury

FOLLOW-UP:
Call our office in 2 weeks to let us know how you're doing. If headaches continue, 
we'll schedule an appointment to explore other treatments.

Questions? Call us at: (555) 123-4567
```

---

## Example 5: Code Generation - Python Function

### Task Type: **Code Generation**

```
Context: You are a senior Python developer creating reusable utility functions for 
an e-commerce platform's inventory management system. The code will be used by other 
developers and must follow PEP 8 standards.

Objective: Generate a production-ready Python function with proper error handling, 
type hints, docstrings, and example usage.

Style: Professional software engineer - clean code, well-documented, defensive 
programming practices

Tone: Technical and precise, assuming intermediate Python knowledge

Audience: Software development team (mid-level to senior developers)

Response Format:
1. Function with type hints
2. Comprehensive docstring (Google style)
3. Input validation
4. Error handling
5. Example usage in __main__ block
6. Unit test example (optional but appreciated)

---

Requirements:
Create a function that checks product inventory levels and generates automatic 
reorder alerts.

Function should:
- Accept: product_id (str), current_stock (int), reorder_threshold (int), reorder_quantity (int)
- Return: dictionary with keys: needs_reorder (bool), items_to_order (int), alert_message (str)
- If current stock is at or below threshold, flag for reorder
- Calculate recommended order quantity
- Include validation for negative numbers
- Handle edge cases (threshold = 0, invalid inputs)

Generate the Python code.
```

**Expected Output:**
```python
from typing import Dict, Union


def check_inventory_reorder(
    product_id: str,
    current_stock: int,
    reorder_threshold: int,
    reorder_quantity: int
) -> Dict[str, Union[bool, int, str]]:
    """
    Check inventory levels and determine if reorder is needed.
    
    This function evaluates current stock against a reorder threshold and
    calculates the recommended order quantity if restocking is needed.
    
    Args:
        product_id: Unique identifier for the product (e.g., "SKU-12345")
        current_stock: Current inventory count (must be >= 0)
        reorder_threshold: Stock level that triggers reorder (must be >= 0)
        reorder_quantity: Number of units to order when restocking
        
    Returns:
        Dictionary containing:
            - needs_reorder (bool): True if stock <= threshold
            - items_to_order (int): Quantity to order (0 if no reorder needed)
            - alert_message (str): Human-readable status message
            
    Raises:
        ValueError: If any numeric parameter is negative
        TypeError: If parameters are not of expected types
        
    Example:
        >>> result = check_inventory_reorder("SKU-001", 15, 20, 50)
        >>> print(result)
        {
            'needs_reorder': True,
            'items_to_order': 50,
            'alert_message': 'ALERT: Product SKU-001 at 15 units (threshold: 20). Order 50 units.'
        }
    """
    # Input validation
    if not isinstance(product_id, str) or not product_id.strip():
        raise ValueError("product_id must be a non-empty string")
    
    if not isinstance(current_stock, int) or current_stock < 0:
        raise ValueError("current_stock must be a non-negative integer")
    
    if not isinstance(reorder_threshold, int) or reorder_threshold < 0:
        raise ValueError("reorder_threshold must be a non-negative integer")
    
    if not isinstance(reorder_quantity, int) or reorder_quantity <= 0:
        raise ValueError("reorder_quantity must be a positive integer")
    
    # Check if reorder is needed
    needs_reorder = current_stock <= reorder_threshold
    
    # Calculate order quantity
    items_to_order = reorder_quantity if needs_reorder else 0
    
    # Generate alert message
    if needs_reorder:
        alert_message = (
            f"ALERT: Product {product_id} at {current_stock} units "
            f"(threshold: {reorder_threshold}). Order {items_to_order} units."
        )
    else:
        alert_message = f"OK: Product {product_id} at {current_stock} units (threshold: {reorder_threshold})."
    
    return {
        "needs_reorder": needs_reorder,
        "items_to_order": items_to_order,
        "alert_message": alert_message
    }


if __name__ == "__main__":
    # Example usage
    print("Example 1: Stock below threshold")
    result1 = check_inventory_reorder("SKU-001", 15, 20, 50)
    print(result1)
    print()
    
    print("Example 2: Stock above threshold")
    result2 = check_inventory_reorder("SKU-002", 100, 20, 50)
    print(result2)
    print()
    
    print("Example 3: Stock exactly at threshold")
    result3 = check_inventory_reorder("SKU-003", 20, 20, 50)
    print(result3)
    print()
    
    # Error handling example
    try:
        result4 = check_inventory_reorder("SKU-004", -5, 20, 50)
    except ValueError as e:
        print(f"Error caught: {e}")
```

---

---

## TASK 6: Chain-of-Thought (CoT) Reasoning 🧠

### What is Chain-of-Thought?

**Chain-of-Thought (CoT)** is a technique where you ask the AI to show its step-by-step thinking process when solving a problem, rather than jumping straight to the answer. Think of it like showing your work in a math class.

**How it works:**
Instead of just giving an answer, the AI breaks down the problem into smaller steps, solves each step in sequence, and shows its reasoning - just like a student solving a word problem step-by-step.

**The Problem CoT Solves:**

*Without CoT (Direct Answer):*
```
Question: "A pharmacy has 45 bottles of medication. Each bottle contains 30 pills. 
If a patient needs 5 pills per day for 12 days, how many bottles are needed?"

AI Answer: "2 bottles"
```
✅ Correct answer, but...
❌ How did it get there?
❌ Can't verify the reasoning
❌ If wrong, hard to debug

*With CoT (Step-by-Step):*
```
Question: [Same as above]

AI Answer:
Step 1: Calculate total pills needed
- Patient needs 5 pills/day for 12 days
- 5 × 12 = 60 pills needed

Step 2: Calculate pills per bottle
- Each bottle contains 30 pills

Step 3: Calculate bottles needed
- 60 pills needed ÷ 30 pills/bottle = 2 bottles

Answer: 2 bottles are needed
```
✅ Correct answer
✅ Can verify each step
✅ Easy to spot errors if any
✅ Builds trust in the answer

**Why Chain-of-Thought is Important:**

1. **Transparency:** You see how AI reached the conclusion
2. **Verification:** Each step can be checked independently
3. **Error Detection:** Easier to spot where reasoning went wrong
4. **Better Accuracy:** AI actually performs better on complex problems when using CoT
5. **Teaching Tool:** Great for explaining concepts step-by-step
6. **Safety Critical:** Essential for medical dosing, financial calculations, etc.

**Real-World Examples:**

**Medical Dosing:**
```
Without CoT: "Give 750mg"
With CoT: 
Step 1: Patient weighs 25kg
Step 2: Dose is 30mg/kg/day
Step 3: 25 × 30 = 750mg/day
Step 4: Divided into 3 doses = 250mg per dose
Safety Check: 250mg is below maximum single dose of 500mg ✓
```

**Business Analysis:**
```
Without CoT: "Don't launch the product"
With CoT:
Step 1: Market size = 100,000 potential customers
Step 2: Expected conversion = 5% = 5,000 customers
Step 3: Revenue per customer = $50
Step 4: Total revenue = $250,000
Step 5: Development cost = $400,000
Step 6: ROI = -$150,000 (negative)
Conclusion: Don't launch - won't break even
```

**When to Use Chain-of-Thought:**
✅ Complex calculations (math, finance, dosing)  
✅ Multi-step reasoning problems  
✅ Safety-critical decisions (medical, engineering)  
✅ Need to verify/audit the reasoning  
✅ Teaching or explaining concepts  
✅ Debugging why AI gave wrong answer  
✅ Building trust in AI recommendations  
✅ Logical deduction problems  

**When NOT to Use CoT:**
❌ Simple questions with obvious answers  
❌ Creative writing (doesn't need reasoning steps)  
❌ Speed is critical and accuracy is less important  
❌ Classification tasks (just need the category)  

**How to Trigger CoT in Prompts:**

Add phrases like:
- "Think step-by-step"
- "Show your work"
- "Explain your reasoning"
- "Let's solve this step by step"
- "Break down the problem"

**Common CoT Formats:**

**Format 1: Thinking Tags**
```
<thinking>
Step 1: [reasoning]
Step 2: [reasoning]
Step 3: [reasoning]
</thinking>

<answer>
Final answer: [result]
</answer>
```

**Format 2: Numbered Steps**
```
Step 1: Identify the given information
- Weight: 22kg
- Dosage: 85mg/kg/day

Step 2: Calculate total daily dose
- 22 × 85 = 1,870mg/day

Step 3: Divide by doses per day
- 1,870 ÷ 2 = 935mg per dose

Final Answer: 935mg per dose, twice daily
```

**Format 3: Question-Answer Chain**
```
Q1: What's the total number of items?
A1: 12 apples

Q2: How many go to each person?
A2: 3 apples per person

Q3: How many people can get apples?
A3: 12 ÷ 3 = 4 people

Answer: 4 people
```

**Advanced CoT: Self-Consistency**

For critical decisions, generate multiple reasoning paths:
```
Reasoning Path 1: [Steps] → Answer: X
Reasoning Path 2: [Steps] → Answer: X
Reasoning Path 3: [Steps] → Answer: X

All paths agree → High confidence in Answer X
```

**CoT Best Practices:**

1. **Show Units:** Always include units in calculations (mg, kg, %, etc.)
2. **Verify Each Step:** Check if the step makes logical sense
3. **Safety Checks:** Add verification steps for critical applications
4. **Clear Labels:** Number steps or use clear headers
5. **Final Answer Separation:** Clearly mark the final answer

**Real Example - Medical Dosing with Safety:**

```
Patient: 6-year-old, 22kg
Medication: Amoxicillin 
Protocol: 80-90 mg/kg/day, divided into 2 doses

Step 1: Calculate daily dose (using 85 mg/kg/day)
- 22kg × 85mg/kg/day = 1,870 mg/day

Step 2: Calculate single dose
- 1,870 mg/day ÷ 2 doses = 935 mg per dose

Step 3: SAFETY CHECK - Compare to maximum
- Maximum pediatric dose: 500mg per dose
- Calculated dose: 935mg
- ⚠️ EXCEEDS MAXIMUM

Step 4: Recommendation
- CANNOT use standard protocol
- Maximum safe dose: 500mg twice daily
- Consult physician before dispensing

Final Answer: 500mg twice daily (maximum safe dose)
⚠️ Requires physician approval - standard protocol exceeds safety limits
```

**Key Difference from Other Tasks:**

| Task | Focus |
|------|-------|
| **Chain-of-Thought** | Show the reasoning process step-by-step |
| Classification | Just give the category |
| Summarization | Condense the content |
| Entity Extraction | Pull specific data |
| Code Generation | Create working code |

---

## Example 6: Chain-of-Thought Reasoning - Healthcare Dosage

### Task Type: **Mathematical Reasoning with Steps**

```
Context: You are a clinical pharmacist calculating pediatric medication dosages for 
a hospital pharmacy system. All calculations must follow evidence-based weight-based 
protocols with safety verification at each step.

Objective: Calculate correct pediatric dosage using step-by-step reasoning, showing 
all work for verification by attending physician.

Style: Clinical pharmacist documenting calculation - methodical, showing each step 
with units clearly labeled

Tone: Professional and safety-focused, meticulous about accuracy

Audience: Healthcare professionals (physicians, nurse practitioners, pharmacists) 
who will verify before administration

Response Format:
<thinking>
Step 1: [Calculate with units and formula]
Step 2: [Next calculation with verification]
Step 3: [Continue until final answer]
Step 4: [Safety check against maximum limits]
</thinking>

<answer>
Final Dosage: [Complete prescription]
Safety Verification: [Confirm within safe limits]
</answer>

---

Patient Information:
- Age: 6 years old
- Weight: 22 kg
- Diagnosis: Acute otitis media (ear infection)

Medication: Amoxicillin
Protocol: 80-90 mg/kg/day divided into 2 doses (use 85 mg/kg/day)
Available: 400mg/5mL suspension
Duration: 10 days
Safety Limit: Maximum 500mg per dose for pediatric patients

Calculate:
1. Total daily dose
2. Single dose amount
3. Volume per dose
4. Total volume needed for 10-day course
5. Verify safety

Think step-by-step and show all calculations.
```

**Expected Output:**
```
<thinking>
Step 1: Calculate total daily dose
Formula: Weight (kg) × Dosage (mg/kg/day)
Calculation: 22 kg × 85 mg/kg/day = 1,870 mg/day
Verification: This is the total amount needed per day

Step 2: Calculate single dose amount
Formula: Total daily dose ÷ Number of doses per day
Calculation: 1,870 mg/day ÷ 2 doses = 935 mg per dose
Verification: Each dose will be 935 mg

Step 3: Calculate volume per dose
Available concentration: 400 mg/5 mL
Formula: (Dose in mg ÷ Concentration in mg) × Volume in mL
Calculation: (935 mg ÷ 400 mg) × 5 mL = 2.34 × 5 = 11.7 mL per dose
Rounded: 11.7 mL per dose (can be rounded to 12 mL for practical measurement)

Step 4: Calculate total volume for 10-day course
Formula: Volume per dose × Doses per day × Number of days
Calculation: 12 mL × 2 doses/day × 10 days = 240 mL total
Verification: Need 240 mL total for complete treatment

Step 5: Safety Check
Single dose: 935 mg
Maximum safe dose: 500 mg per dose
WARNING: 935 mg EXCEEDS the maximum safe pediatric dose of 500 mg!

RECALCULATION REQUIRED:
Maximum safe daily dose: 500 mg × 2 doses = 1,000 mg/day
This equals: 1,000 mg ÷ 22 kg = 45.5 mg/kg/day
This is BELOW the recommended 80-90 mg/kg/day range.

ISSUE IDENTIFIED: Standard weight-based dosing exceeds pediatric safety limits 
for this patient.
</thinking>

<answer>
⚠️ ALERT: Cannot use standard protocol for this patient

The standard amoxicillin dose of 85 mg/kg/day would result in 935 mg per dose, 
which exceeds the pediatric maximum safe dose of 500 mg per dose.

RECOMMENDED ACTION:
Contact prescribing physician to discuss:
1. Use maximum safe dose: 500 mg twice daily (45.5 mg/kg/day)
2. Consider alternative antibiotic with higher safety margin
3. Extend treatment duration if lower dose is used

DO NOT DISPENSE until physician consultation is complete.

If physician approves 500mg twice daily:
- Dose: 500 mg (6.25 mL of 400mg/5mL suspension) twice daily
- Duration: 10 days
- Total volume needed: 125 mL (dispense 150 mL bottle)
</answer>
```

---

## Example 7: Few-Shot Learning - Medical Coding

### Task Type: **Classification with Examples**

```
Context: You are an automated medical coding assistant for a hospital billing 
department. You assign ICD-10 diagnostic codes based on physician documentation to 
ensure proper insurance billing.

Objective: Accurately assign ICD-10 codes to clinical diagnoses by learning from 
provided examples, then applying the pattern to new cases.

Style: Medical coding specialist - precise, following official coding guidelines

Tone: Objective and systematic, no interpretation beyond documented facts

Audience: Medical billing department and insurance claims processors

Response Format:
ICD-10 Code: [CODE]
Description: [Official description]
Confidence: HIGH | MEDIUM | LOW

---

Learn from these examples:

Example 1:
Clinical Note: "Patient presents with Type 2 diabetes mellitus with diabetic 
nephropathy (kidney disease)."
ICD-10: E11.21
Description: Type 2 diabetes mellitus with diabetic nephropathy

Example 2:
Clinical Note: "Patient diagnosed with hypertensive heart disease with heart failure."
ICD-10: I11.0
Description: Hypertensive heart disease with heart failure

Example 3:
Clinical Note: "Patient has acute bronchitis due to respiratory syncytial virus (RSV)."
ICD-10: J20.5
Description: Acute bronchitis due to respiratory syncytial virus

Example 4:
Clinical Note: "Patient presents with major depressive disorder, recurrent episode, 
moderate severity."
ICD-10: F33.1
Description: Major depressive disorder, recurrent, moderate

---

Now code this case:

Clinical Note: "67-year-old male presents with community-acquired pneumonia, right 
lower lobe. Chest X-ray confirms diagnosis. Patient is being admitted for IV 
antibiotic therapy."

Assign the ICD-10 code.
```

**Expected Output:**
```
ICD-10 Code: J18.1
Description: Lobar pneumonia, unspecified organism
Confidence: HIGH

Note: "Community-acquired pneumonia" with specific lobe involvement (right lower lobe) 
is coded as lobar pneumonia. Since the organism is not specified in the documentation, 
the "unspecified organism" code is appropriate. If organism was identified (e.g., 
Streptococcus pneumoniae), a more specific code would be used.
```

---

---

## TASK 8: Data Transformation 🔄

### What is Data Transformation?

**Data Transformation** is the task of converting data from one format to another, or transforming structured data into natural language (and vice versa). Think of it like translating between different "languages" - from computer language to human language, or from one data structure to another.

**How it works:**
The AI takes data in one format (JSON, CSV, XML, database records, tables) and converts it into a different format (natural language reports, different data structures, visualizations, summaries).

**Two Main Directions:**

1. **Structured → Natural Language:**
   - JSON/CSV/Database → Human-readable reports
   - Example: Sales data → Executive summary

2. **Natural Language → Structured:**
   - Text → JSON/CSV/Database
   - Example: Customer email → Structured ticket data

**Real-World Examples:**

**Business Intelligence:**
```
Input: Raw sales JSON data
Output: "Weekly sales reached $487K, up 15% YoY. Electronics drove growth at 28%."
```

**API Responses:**
```
Input: Complex JSON from API
Output: Simple, readable summary for non-technical users
```

**Report Generation:**
```
Input: Database query results
Output: Formatted executive report with insights
```

**Form Processing:**
```
Input: "I want to book a flight from NYC to LA on Dec 25th, returning Jan 2nd"
Output: { "from": "NYC", "to": "LA", "depart": "2024-12-25", "return": "2025-01-02" }
```

**Simple Example:**

*Input (Structured JSON):*
```json
{
  "employee": "Sarah Johnson",
  "department": "Engineering",
  "performance_score": 4.8,
  "projects_completed": 12,
  "promotion_eligible": true
}
```

*Output (Natural Language Report):*
```
Performance Review - Sarah Johnson (Engineering)

Sarah delivered exceptional performance this quarter with a 4.8/5.0 rating. 
She successfully completed 12 projects and has qualified for promotion consideration 
based on her outstanding contributions.
```

**Common Transformation Types:**

1. **JSON → Report**
   - API data → Business summary
   - Analytics data → Executive dashboard narrative

2. **CSV → Insights**
   - Raw data table → Key findings and trends
   - Sales spreadsheet → Performance summary

3. **Database Records → Summary**
   - Customer records → Segment analysis
   - Transaction logs → Financial report

4. **Text → Structured Data**
   - Customer feedback → Sentiment + themes JSON
   - Medical notes → Structured patient data

5. **XML → Human Readable**
   - Configuration files → Setup instructions
   - API responses → User-friendly messages

**When to Use Data Transformation:**
✅ Generating automated reports from databases  
✅ Making technical data accessible to non-technical stakeholders  
✅ Converting API responses to user-friendly messages  
✅ Extracting insights from raw data  
✅ Populating databases from unstructured text  
✅ Creating dashboards narratives from metrics  
✅ Building data pipelines between systems  

**When NOT to Use Data Transformation:**
❌ Data is already in the needed format  
❌ Simple copy-paste would work  
❌ You need complex calculations (use code instead)  
❌ Real-time performance is critical (transformation adds latency)  

**Key Principles of Good Transformation:**

1. **Preserve Critical Information:**
   - Don't lose important data in translation
   - Maintain accuracy of numbers and facts

2. **Add Context and Insights:**
   - Don't just reformat - add meaning
   - Highlight trends, anomalies, key takeaways

3. **Match Audience Needs:**
   - Technical audience → Keep technical terms
   - Business audience → Translate to business language
   - Executives → Focus on high-level insights

4. **Structure for Action:**
   - Reports should lead to decisions
   - Highlight what needs attention
   - Suggest next steps

**Example - Same Data, Different Audiences:**

*Raw Data:*
```json
{
  "server_uptime": 0.997,
  "response_time_p95": 245,
  "error_rate": 0.003,
  "requests_per_second": 1250
}
```

*For Technical Team:*
```
System Performance Metrics:
- Uptime: 99.7% (target: 99.9%)
- P95 Latency: 245ms (within 300ms SLA)
- Error Rate: 0.3% (above 0.1% threshold)
- Throughput: 1,250 req/sec

Action Required: Investigate error rate spike
```

*For Executive Team:*
```
System Health: GOOD with minor issues

Our platform maintained 99.7% availability this week, processing 1,250 requests 
per second with fast response times. However, we're seeing slightly elevated 
error rates (0.3%) that need attention to maintain service quality.

Recommendation: Allocate engineering resources to address error rate
```

**Transformation Best Practices:**

1. **Always Validate Data:**
   ```
   Before: {"amount": "1500"}
   Validate: Is "1500" a number? Is it reasonable?
   Transform: "$1,500"
   ```

2. **Handle Missing Data:**
   ```
   Input: {"name": "John", "email": null}
   Output: "John (email not provided)" not "John null"
   ```

3. **Preserve Units:**
   ```
   Bad: "The distance is 5"
   Good: "The distance is 5 kilometers"
   ```

4. **Add Context:**
   ```
   Bad: "Revenue: $100,000"
   Good: "Revenue: $100,000 (15% increase vs last month)"
   ```

5. **Format Numbers Appropriately:**
   ```
   Data: 1234567
   Report: $1,234,567 or $1.23M (depending on context)
   ```

**Complex Transformation Example:**

*Input (Raw Database Results):*
```json
[
  {"product": "Laptop Pro", "revenue": 125000, "units": 250, "returns": 12},
  {"product": "Tablet X", "revenue": 89000, "units": 445, "returns": 67},
  {"product": "Phone Z", "revenue": 156000, "units": 520, "returns": 31}
]
```

*Output (Executive Report):*
```
Q4 Product Performance Summary

Top Performer: Phone Z
- Revenue: $156,000 (highest)
- Units Sold: 520
- Return Rate: 6.0% (acceptable)

Concern: Tablet X
- Revenue: $89,000
- Units Sold: 445
- Return Rate: 15.1% ⚠️ (significantly above 10% threshold)
- Recommendation: Investigate quality issues

Overall: Strong quarter with $370K total revenue across 1,215 units sold.
Action required on Tablet X return rate.
```

**Common Patterns:**

**Pattern 1: Metric → Insight**
```
Data: sales_growth = 0.15
Transformation: "Sales grew by 15%, indicating strong market demand"
```

**Pattern 2: Multiple Metrics → Story**
```
Data: {revenue_up: true, costs_up: true, profit_down: true}
Transformation: "While revenue increased, rising costs led to decreased profitability"
```

**Pattern 3: Time Series → Trend**
```
Data: [100, 110, 125, 145, 170]
Transformation: "Showing consistent upward trend with 14% average monthly growth"
```

**Key Difference from Other Tasks:**

| Task | Purpose |
|------|---------|
| **Data Transformation** | Change format or structure of data |
| Summarization | Make text shorter |
| Entity Extraction | Pull specific fields from text |
| Classification | Assign to categories |
| RAG | Answer questions from documents |

---

## Example 8: Data Transformation - JSON to Report

### Task Type: **Structured Data to Natural Language**

```
Context: You are generating automated executive summaries for "RetailMetrics," a 
business intelligence platform. Sales managers receive these summaries every Monday 
to review the previous week's performance.

Objective: Transform raw JSON sales data into a clear, actionable executive summary 
that highlights key insights and trends.

Style: Business analyst presenting to executives - data-driven but accessible, 
highlights actionable insights

Tone: Professional and confident, balanced (acknowledge both wins and concerns)

Audience: Sales managers and executives (non-technical, decision-makers)

Response Format:
1. Executive Summary (2-3 sentences - key takeaway)
2. Performance Highlights (3 bullet points - wins)
3. Areas of Concern (2 bullet points - issues)
4. Recommended Actions (2-3 specific next steps)
Total: Under 200 words

---

Weekly Sales Data (JSON):
{
  "week_ending": "2024-12-22",
  "total_revenue": 487650,
  "total_orders": 1823,
  "average_order_value": 267.50,
  "year_over_year_growth": 0.15,
  "top_performing_category": {
    "name": "Electronics",
    "revenue": 195060,
    "growth": 0.28
  },
  "underperforming_category": {
    "name": "Home & Garden",
    "revenue": 48765,
    "growth": -0.12
  },
  "customer_metrics": {
    "new_customers": 342,
    "returning_customers": 1481,
    "customer_retention_rate": 0.81
  },
  "regional_performance": {
    "best_region": "West Coast",
    "worst_region": "Southeast",
    "west_coast_revenue": 170677,
    "southeast_revenue": 87689
  }
}

Generate the executive summary.
```

**Expected Output:**
```
WEEKLY SALES SUMMARY - Week Ending December 22, 2024

EXECUTIVE SUMMARY:
Strong week with $487,650 in revenue (+15% YoY) driven by Electronics category growth 
and excellent customer retention. However, Home & Garden continues to decline and 
Southeast region underperformance requires attention.

PERFORMANCE HIGHLIGHTS:
• Revenue up 15% year-over-year with 1,823 orders at $267.50 average order value
• Electronics category surged 28%, generating $195K (40% of total revenue)
• Customer retention excellent at 81% - returning customers drove 81% of orders

AREAS OF CONCERN:
• Home & Garden category down 12%, losing $6.5K compared to last year
• Southeast region generated only $87.7K (18% of revenue) vs. West Coast's $170.7K

RECOMMENDED ACTIONS:
1. Launch targeted promotion for Home & Garden category to reverse declining trend
2. Analyze Southeast region performance - consider localized marketing campaign
3. Capitalize on Electronics momentum - increase inventory for high-demand items
```

---

---

## TASK 9: Conversational AI / Multi-Turn Dialogue 💬

### What is Conversational AI?

**Conversational AI** is the task of creating natural, back-and-forth conversations where the AI remembers context from previous messages, asks appropriate follow-up questions, and guides the conversation toward a specific goal. Think of it like having a phone conversation with a helpful assistant.

**How it works:**
The AI maintains conversation history, remembers what's been discussed, asks clarifying questions, and systematically gathers information - just like a human customer service representative or appointment scheduler would.

**Key Characteristics:**

1. **Context Awareness:**
   - Remembers what was said 3 messages ago
   - Uses previous answers to inform next questions
   - Doesn't ask for information already provided

2. **Natural Flow:**
   - Asks one question at a time (not overwhelming)
   - Uses conversational language, not robotic
   - Acknowledges user responses before moving on

3. **Goal-Oriented:**
   - Working toward a specific outcome (book appointment, solve problem, gather info)
   - Knows what information is needed
   - Guides user through the process

4. **Adaptive:**
   - Handles unexpected responses
   - Clarifies when confused
   - Adjusts based on user needs

**The Difference:**

*Bad (No Context):*
```
Turn 1:
User: "I need to see a doctor"
AI: "What's your name?"

Turn 2:
User: "John Smith"
AI: "What's your name?" ← Forgot what user just said!
```

*Good (Conversational):*
```
Turn 1:
User: "I need to see a doctor"
AI: "I can help with that. What symptoms are you experiencing?"

Turn 2:
User: "Bad headaches for 2 weeks"
AI: "I'm sorry to hear that. Persistent headaches should definitely be checked. 
     Do you have any fever, vision changes, or neck stiffness?"

Turn 3:
User: "No, just headaches"
AI: "Thank you. That sounds like something our general practice doctors can 
     evaluate. Would you prefer a morning or afternoon appointment?"
```

**Real-World Examples:**

**Appointment Booking:**
```
AI: "What type of service do you need?"
→ User: "Dental cleaning"
AI: "What day works best?"
→ User: "Thursday"
AI: "Morning or afternoon?"
→ User: "Afternoon"
AI: "I have 2pm or 3:30pm available"
```

**Technical Support:**
```
AI: "What issue are you experiencing?"
→ User: "Printer won't print"
AI: "Is the printer showing any error lights?"
→ User: "Red light blinking"
AI: "That usually indicates a paper jam. Let's check the paper tray..."
```

**Customer Service:**
```
AI: "How can I help you today?"
→ User: "I want to return something"
AI: "I can help with that. Do you have your order number?"
→ User: "ORD-12345"
AI: "Found it! I see you ordered a laptop. What's the reason for the return?"
```

**When to Use Conversational AI:**
✅ Information needs to be gathered step-by-step  
✅ Complex workflows need guidance  
✅ User needs help navigating options  
✅ Natural interaction improves user experience  
✅ Reducing user overwhelm (vs long forms)  
✅ Appointment booking, reservations  
✅ Troubleshooting and support  
✅ Qualifying leads  

**When NOT to Use Conversational AI:**
❌ Simple one-question tasks  
❌ All information available upfront  
❌ Speed is critical (forms are faster)  
❌ No branching logic needed  

**Best Practices for Conversational AI:**

**1. One Question at a Time:**
```
❌ Bad: "What's your name, email, phone number, and preferred date?"

✅ Good: "May I have your name?"
       → "Thanks, John. And your email address?"
       → "Perfect. What's the best phone number to reach you?"
```

**2. Acknowledge Responses:**
```
❌ Bad: 
User: "I need urgent care"
AI: "What's your address?"

✅ Good:
User: "I need urgent care"
AI: "I understand this is urgent. I'll get you scheduled right away. What's 
     your address so I can find the closest location?"
```

**3. Provide Context for Questions:**
```
❌ Bad: "Do you have insurance?"

✅ Good: "To make sure we bill correctly, do you have health insurance?"
```

**4. Handle Errors Gracefully:**
```
User: "I want to book for tomorrow"
AI: "I'd love to help, but I'm not sure what type of appointment you need. 
     Are you looking for a doctor visit, lab work, or something else?"
```

**5. Confirm Before Finalizing:**
```
AI: "Let me confirm your appointment:
     - Thursday, Dec 28th at 2:00 PM
     - Dr. Johnson
     - Reason: Persistent headaches
     Is this correct?"
```

**Conversation Design Patterns:**

**Pattern 1: Information Gathering**
```
Goal → Ask questions → Collect data → Confirm → Complete
```

**Pattern 2: Troubleshooting**
```
Problem → Diagnose → Step-by-step fix → Test → Resolve or escalate
```

**Pattern 3: Decision Support**
```
Understand needs → Present options → Clarify → Recommend → Confirm choice
```

**Pattern 4: Qualification**
```
Initial question → Filter → Deep dive or redirect → Qualify or decline
```

**Example - Appointment Booking Flow:**

```
Step 1: Determine Service Type
AI: "I can help you schedule an appointment. What brings you in today?"

Step 2: Assess Urgency
User: "I've been having chest pain"
AI: [URGENT FLAG] "Chest pain needs immediate attention. Are you experiencing 
     chest pain right now?"

Step 3: Route Appropriately
User: "No, it was earlier today"
AI: "I'm glad it's not active now, but chest pain should be evaluated today. 
     Our urgent care clinic has an opening in 30 minutes. Would that work?"

Step 4: Collect Details
User: "Yes"
AI: "Great. May I have your name?"

Step 5: Confirm
AI: "You're all set, John. Urgent care today at 2:30 PM for chest pain evaluation. 
     Please arrive 15 minutes early."
```

**Managing Conversation State:**

The AI needs to track:
- **What information has been collected:** Name ✓, Email ✓, Date ✗
- **What's next:** Need to ask for date
- **Special flags:** Urgent case, VIP customer, etc.
- **Conversation history:** Previous 3-5 exchanges

**Handling Complex Scenarios:**

**Scenario 1: User Changes Mind**
```
AI: "Would you prefer morning or afternoon?"
User: "Actually, can I do it next week instead?"
AI: "Of course! Let me show you next week's availability..."
```

**Scenario 2: User Provides Too Much Info**
```
User: "Hi, I'm John Smith, john@email.com, 555-1234, I need a cleaning on Thursday 
      at 2pm"
AI: "Perfect, John! I have all your details. Let me check if Thursday at 2pm is 
     available for a cleaning..."
[AI extracts and uses all the info, doesn't re-ask]
```

**Scenario 3: Unclear Response**
```
AI: "Would you like morning or afternoon?"
User: "Whatever works"
AI: "I have more availability in the afternoon. How about 2:00 PM or 3:30 PM?"
```

**Safety and Escalation:**

**When to Escalate to Human:**
- Medical emergency mentioned
- Angry/frustrated customer
- Request outside AI's capabilities
- Sensitive situations (complaints, refunds)
- AI is confused after 2-3 clarifications

**Example - Emergency Detection:**
```
User: "I'm having severe chest pain and trouble breathing"
AI: "This sounds like a medical emergency. Please call 911 or go to the nearest 
     emergency room immediately. Do not wait for an appointment."
[+ Optionally notify human staff]
```

**Conversation Quality Metrics:**

Good conversational AI should:
- ✅ Complete task in ≤10 turns for simple tasks
- ✅ Understand 90%+ of user inputs
- ✅ Never ask for same information twice
- ✅ Gracefully handle 95%+ of edge cases
- ✅ Escalate appropriately when stuck

**Key Difference from Other Tasks:**

| Task | Interaction |
|------|-------------|
| **Conversational AI** | Multiple back-and-forth exchanges with context |
| Classification | Single input → Single output |
| Entity Extraction | Single pass through text |
| RAG | Question → Answer (may be complex, but one exchange) |
| Summarization | Input document → Summary |

---

## Example 9: Conversational AI - Multi-Turn Dialogue

### Task Type: **Context-Aware Conversation**

```
Context: You are "MediBot," a healthcare appointment scheduling assistant for 
Memorial Clinic. You help patients book appointments, answer basic questions about 
services, and collect necessary information. You have access to the appointment 
system but cannot diagnose or provide medical advice.

Objective: Guide patient through appointment booking process naturally while 
collecting required information (reason for visit, preferred date/time, insurance).

Style: Conversational healthcare receptionist - friendly but professional, asks 
one question at a time to avoid overwhelming patient

Tone: Warm and helpful, patient and understanding, reassuring for anxious patients

Audience: Patients calling to schedule appointments (all ages, varying health literacy)

Response Format: Natural conversation - acknowledge what they said, ask next question, 
provide helpful context when needed

Conversation Rules:
1. Always confirm before booking
2. If emergency symptoms mentioned, direct to ER
3. Collect: name, reason, preferred date/time, insurance
4. Don't ask for medical history (doctor will do that)

---

Conversation:

Patient: "Hi, I need to see a doctor soon. I've been having really bad headaches 
for about 2 weeks now."

[Your response]

Patient: "They're mostly in the morning, and they're getting worse. Should I be worried?"

[Your response]

Patient: "No fever, no vision problems. Just these headaches and I'm really tired."

[Your response]

Generate the conversation turns.
```

**Expected Output:**
```
Turn 1:
"I'm sorry to hear you've been experiencing headaches. I can help you schedule an 
appointment with one of our doctors. To make sure we get you the right care, can 
you tell me - is this headache sudden and severe, or has it been gradually building 
over the two weeks?"

Turn 2:
"Thank you for that information. While I can't provide medical advice, persistent 
headaches that are worsening should definitely be evaluated by a doctor. Let me ask 
a few quick questions: Are you experiencing any fever, vision changes, or neck 
stiffness along with the headaches?"

Turn 3:
"Okay, thank you. Based on what you've shared, this sounds like something our 
general practice doctors can evaluate - it doesn't require emergency care. We have 
appointments available this week. Would you prefer a morning or afternoon appointment? 
And may I have your name to start booking?"

Turn 4 (if patient says "afternoon, and my name is Sarah"):
"Perfect, Sarah. I have an afternoon appointment available with Dr. Johnson on 
Thursday at 2:00 PM, or Friday at 3:30 PM. Which works better for you?"

Turn 5 (if patient chooses Thursday):
"Great! I've got you scheduled with Dr. Johnson for Thursday, December 26th at 
2:00 PM. One last thing - do you have health insurance? If so, which provider?"

Turn 6 (after insurance info):
"Perfect, Sarah. You're all set for Thursday at 2:00 PM with Dr. Johnson. Please 
arrive 15 minutes early to complete some paperwork. We'll send you a confirmation 
text. Is there anything else I can help you with today?"
```

---

---

## TASK 10: Hybrid / Multi-Task 🎭

### What is Hybrid Multi-Task?

**Hybrid Multi-Task** combines multiple AI capabilities in a single prompt to solve complex, real-world problems. Instead of doing just one thing (classify OR extract OR generate), it does several tasks together in a coordinated workflow. Think of it like a Swiss Army knife - multiple tools working together.

**How it works:**
The AI performs several different operations sequentially or simultaneously:
1. Extracts information (Entity Extraction)
2. Classifies it (Classification)
3. Reasons about it (Chain-of-Thought)
4. Generates a response (Generation)
5. Makes recommendations (Decision Support)

**Why Hybrid Tasks Matter:**

Real-world problems don't fit into single task boxes. For example, a customer service request needs:
- Extract order details
- Classify issue type
- Assess urgency
- Generate appropriate response
- Recommend resolution
- All at once!

**Simple Example:**

*Single Task (Classification Only):*
```
Input: Customer complaint email
Output: CATEGORY: "Shipping Delay"
```
↑ Not very useful by itself!

*Hybrid Multi-Task:*
```
Input: Customer complaint email

Output:
1. Extracted Entities:
   - Order: #ORD-5567
   - Product: Laptop
   - Order Date: Dec 10
   - Expected Delivery: Dec 15
   
2. Classification:
   - Issue Type: DELIVERY_DELAY
   - Urgency: HIGH
   - Customer Sentiment: FRUSTRATED
   
3. Analysis:
   - Package delayed by 5 days
   - Customer has deadline (gift for Dec 20)
   - Loyal customer (10+ previous orders)
   
4. Generated Response:
   [Personalized apology email]
   
5. Recommended Actions:
   - Expedite shipping (overnight)
   - Offer 20% discount
   - Follow up in 24 hours
```
↑ Complete, actionable solution!

**Real-World Hybrid Examples:**

**1. Product Recommendation Engine:**
```
Tasks Combined:
- Analyze user profile (Entity Extraction)
- Classify user preferences (Classification)
- Match with products (RAG)
- Reason about fit (Chain-of-Thought)
- Generate recommendations (Generation)
- Format as JSON (Data Transformation)
```

**2. Medical Triage System:**
```
Tasks Combined:
- Extract symptoms and vitals (Entity Extraction)
- Classify urgency level (Classification)
- Reference clinical guidelines (RAG)
- Calculate risk scores (Chain-of-Thought)
- Generate care plan (Generation)
- Format for EHR (Data Transformation)
```

**3. Intelligent Email Assistant:**
```
Tasks Combined:
- Understand email intent (Classification)
- Extract action items (Entity Extraction)
- Draft response (Generation)
- Check calendar availability (RAG)
- Suggest meeting times (Reasoning)
```

**When to Use Hybrid Multi-Task:**
✅ Complex business workflows  
✅ End-to-end automation needed  
✅ Rich, comprehensive outputs required  
✅ Multiple criteria must be evaluated  
✅ Real-world scenarios that don't fit one task  
✅ Decision support systems  
✅ Complete customer service automation  

**When NOT to Use Hybrid Multi-Task:**
❌ Simple single-purpose tasks  
❌ When one task type is sufficient  
❌ Performance/speed is critical (multi-task is slower)  
❌ Debugging complexity is a concern  

**Common Hybrid Patterns:**

**Pattern 1: Extract → Classify → Generate**
```
Example: Support Ticket Processing
1. Extract: Order number, product, issue details
2. Classify: Issue type, priority, department
3. Generate: Response email + routing decision
```

**Pattern 2: Retrieve → Analyze → Recommend**
```
Example: Product Recommendation
1. Retrieve: User history, product catalog
2. Analyze: Preferences, budget, style
3. Recommend: Top 5 products with reasoning
```

**Pattern 3: Classify → Reason → Generate → Validate**
```
Example: Medical Diagnosis Support
1. Classify: Symptom severity
2. Reason: Differential diagnosis
3. Generate: Treatment recommendations
4. Validate: Safety checks against contraindications
```

**Pattern 4: Extract → Transform → Analyze → Report**
```
Example: Business Intelligence
1. Extract: Key metrics from data
2. Transform: Calculate trends, changes
3. Analyze: Identify insights, anomalies
4. Report: Executive summary with recommendations
```

**Design Principles for Hybrid Tasks:**

**1. Sequential Logic:**
Order matters! Each task should build on previous ones.
```
✅ Good Order:
   Extract data → Classify → Analyze → Recommend

❌ Bad Order:
   Recommend → Extract data ← Can't recommend without data!
```

**2. Clear Task Boundaries:**
Define what each sub-task does.
```
COSTAR Objective: 
"Analyze customer feedback by:
1. Extracting key themes (Entity Extraction)
2. Classifying sentiment (Classification)
3. Generating executive summary (Summarization)"
```

**3. Structured Output:**
Multi-task outputs need clear structure.
```
{
  "extraction": {...},
  "classification": {...},
  "analysis": {...},
  "recommendations": [...]
}
```

**4. Error Handling:**
What if one task fails?
```
If entity extraction finds no order number:
→ Classification: "INSUFFICIENT_INFO"
→ Generate: "Please provide your order number to assist you"
```

**Real Example - E-commerce Returns:**

*Input:* Customer email about returning a product

**Task 1: Extract Entities**
```
- Order Number: ORD-12345
- Product: Blue Widget
- Purchase Date: Nov 15, 2024
- Reason: "Changed my mind"
- Customer: Sarah Chen (VIP status)
```

**Task 2: Classify**
```
- Return Eligibility: ELIGIBLE (within 30 days)
- Return Reason Category: REMORSE_RETURN
- Customer Segment: VIP
- Priority: MEDIUM
```

**Task 3: Check Policy (RAG)**
```
Return Policy Retrieved:
- 30-day window: ✓ (29 days elapsed)
- Unopened products: Need to verify
- VIP members: Free return shipping
- Restocking fee: Waived for VIPs
```

**Task 4: Reason (CoT)**
```
Step 1: Check eligibility
- Within 30 days? YES (ordered Nov 15, today is Dec 14)

Step 2: Calculate refund
- Product price: $149
- Shipping originally paid: $0 (free shipping)
- Restocking fee: $0 (waived for VIP)
- Total refund: $149

Step 3: Determine shipping label
- VIP customer → Free return shipping label

Conclusion: Approve return, issue $149 refund
```

**Task 5: Generate Response**
```
"Hi Sarah,

I've processed your return request for the Blue Widget (Order #ORD-12345). 

Here's what happens next:
1. I've emailed you a prepaid return shipping label
2. Once we receive the item (unopened), we'll refund $149 to your original 
   payment method
3. Refund typically processes within 3-5 business days

As a VIP member, there's no return shipping cost or restocking fee.

Is there anything else I can help you with today?

Best regards,
Customer Service"
```

**Task 6: Create Action Items**
```
Internal Actions:
- [ ] Email return label to sarah@email.com
- [ ] Create return RMA #RMA-12345
- [ ] Flag for QC: Check if unopened
- [ ] Schedule refund for 3 business days after receipt
- [ ] Update customer profile: Return history
```

**Complete Output (Structured):**
```json
{
  "entities": {
    "order_number": "ORD-12345",
    "product": "Blue Widget",
    "customer": "Sarah Chen",
    "customer_segment": "VIP"
  },
  "classification": {
    "return_eligible": true,
    "reason": "REMORSE_RETURN",
    "priority": "MEDIUM"
  },
  "policy_check": {
    "within_window": true,
    "days_elapsed": 29,
    "restocking_fee": 0,
    "return_shipping_cost": 0
  },
  "calculations": {
    "refund_amount": 149.00,
    "processing_time_days": "3-5"
  },
  "customer_response": "...",
  "internal_actions": [...]
}
```

**Benefits of Hybrid Approach:**

1. **Complete Solution:** One prompt handles entire workflow
2. **Consistency:** All tasks use same context
3. **Efficiency:** Faster than separate prompts
4. **Rich Output:** Comprehensive, actionable results
5. **Realistic:** Matches real-world complexity

**Challenges:**

1. **Complexity:** Harder to design and debug
2. **Longer Prompts:** More tokens used
3. **Error Propagation:** One task's error affects others
4. **Harder to Optimize:** Many moving parts

**Best Practices:**

**1. Start Simple, Add Complexity:**
```
Version 1: Extract + Classify
Version 2: Extract + Classify + Generate
Version 3: Extract + Classify + RAG + Generate + Recommend
```

**2. Test Each Task Separately First:**
```
✓ Does extraction work?
✓ Does classification work?
✓ Then combine them
```

**3. Use Clear Section Headers:**
```
COSTAR Response Format:
"Provide output in sections:
1. EXTRACTED ENTITIES: {...}
2. CLASSIFICATION: {...}
3. ANALYSIS: {...}
4. RECOMMENDATIONS: [...]"
```

**4. Include Validation Steps:**
```
"After extraction, verify:
- Is order number valid format?
- Is date reasonable?
If validation fails, flag for human review"
```

**Key Difference from Other Tasks:**

| Task | Complexity |
|------|------------|
| **Hybrid Multi-Task** | Combines 3+ different AI tasks in one workflow |
| Single Tasks | One specific operation (classify, extract, etc.) |
| Chain-of-Thought | Multi-step, but all reasoning |
| Conversational | Multi-turn, but same task type |

---

## Example 10: Hybrid Task - E-commerce Product Recommendation Engine

### Task Type: **Multi-Task (Classification + Reasoning + Generation)**

```
Context: You are the AI recommendation engine for "StyleHub," a fashion e-commerce 
platform with 500K users. You analyze user behavior and purchase history to suggest 
complementary products that create complete outfits and increase cart value.

Objective: Generate personalized product recommendations that: (1) complement items 
in cart, (2) match user's style profile, (3) fit budget preferences, (4) create 
complete outfit combinations.

Style: Personal fashion stylist - knowledgeable about style principles, color 
coordination, and wardrobing

Tone: Confident and helpful, enthusiastic about fashion but not pushy about sales

Audience: Style-conscious shopper (age 32, professional, values quality, price-aware)

Response Format: For each recommendation provide:
{
  "product_name": "",
  "price": 0,
  "why_recommended": "Specific reason it complements current selection",
  "outfit_idea": "How to wear it together",
  "priority": "HIGH | MEDIUM | LOW"
}

Recommend 5 items total, mixing price points.

---

User Profile:
- Age: 32, Male, Professional career
- Past purchases: Dress shoes ($120), Leather belt ($45), Casual sneakers ($95)
- Recently viewed: Blazers, Chinos, Oxford shirts
- Price preference: $40-$150 per item
- Style: Business casual, classic with modern touches

Current Cart:
- Navy blue Oxford button-down shirt ($89)
- Viewing product: Men's slim-fit chinos in khaki

Browsing Context: Looking at the chinos product page, spending 45 seconds, 
has not added to cart yet.

Generate recommendations that will:
1. Encourage adding the chinos to cart
2. Build a complete outfit
3. Increase total order value
4. Match his style profile

Provide product recommendations.
```

**Expected Output:**
```json
{
  "recommendations": [
    {
      "product_name": "Tan Leather Belt - Classic Buckle",
      "price": 55,
      "why_recommended": "Essential to complete the look with khaki chinos and navy 
      shirt. Matches your existing leather accessories and fills a gap in neutral belt 
      colors.",
      "outfit_idea": "Wear with the navy Oxford and khaki chinos for a polished 
      business casual look. The tan belt bridges the navy and khaki beautifully.",
      "priority": "HIGH"
    },
    {
      "product_name": "Gray Herringbone Blazer - Unstructured",
      "price": 145,
      "why_recommended": "You've been viewing blazers, and this gray herringbone pairs 
      perfectly with navy and khaki - a classic color combination. Unstructured style 
      keeps it modern and comfortable.",
      "outfit_idea": "Layer over the navy shirt and khaki chinos for client meetings. 
      Remove blazer for Friday casual. This is your complete business casual uniform.",
      "priority": "HIGH"
    },
    {
      "product_name": "Brown Leather Loafers - Dress Casual",
      "price": 128,
      "why_recommended": "Completes the business casual outfit. Brown leather works 
      with both khaki and navy, and matches your preference for quality leather 
      accessories ($120 dress shoes in history).",
      "outfit_idea": "Perfect with this outfit for the office. Also works with your 
      existing wardrobe - dress them up or down.",
      "priority": "MEDIUM"
    },
    {
      "product_name": "White Premium Cotton Pocket Square",
      "price": 28,
      "why_recommended": "Affordable way to elevate the blazer look. White works with 
      any color combination and adds polish without being too formal.",
      "outfit_idea": "Tuck into the blazer pocket when wearing with navy shirt and 
      khaki chinos for professional events or dates.",
      "priority": "LOW"
    },
    {
      "product_name": "Slim Fit Chinos - Navy (Same Style as Khaki)",
      "price": 89,
      "why_recommended": "If you love the fit of these khaki chinos, the navy version 
      creates outfit versatility. Navy chinos + white/light blue shirt is a wardrobe 
      staple.",
      "outfit_idea": "Alternate between khaki and navy chinos throughout the week. 
      Navy chinos work with almost any shirt color in your wardrobe.",
      "priority": "MEDIUM"
    }
  ],
  
  "summary": "These 5 items create a complete, versatile business casual wardrobe. 
  Total investment: $534 (including cart items). This gives you multiple outfit 
  combinations suitable for your professional lifestyle.",
  
  "complete_outfit_total": 534,
  "estimated_number_of_outfits": "8-10 different combinations",
  
  "urgency_note": "The gray herringbone blazer is trending and selling fast in your 
  size. Consider adding it now to secure your size."
}
```

---

## Summary Table: 10 Task Types

| # | Task Type | Domain | Key COSTAR Elements |
|---|-----------|--------|-------------------|
| 1 | Classification | E-commerce | Objective: Clear categories, Format: JSON |
| 2 | Entity Extraction | Customer Support | Format: XML structure, Tone: Neutral |
| 3 | RAG/Q&A | Product Support | Context: Source docs, Objective: Cite sources |
| 4 | Summarization | Healthcare | Audience: Patient, Style: Plain language |
| 5 | Code Generation | Software Dev | Format: Code+docs+tests, Style: Professional |
| 6 | Chain-of-Thought | Healthcare | Format: Show steps, Tone: Safety-focused |
| 7 | Few-Shot Learning | Medical Coding | Context: Examples first, Objective: Learn pattern |
| 8 | Data Transformation | Business Analytics | Audience: Executives, Style: Insights-focused |
| 9 | Conversational AI | Healthcare Booking | Tone: Warm, Style: One question at a time |
| 10 | Hybrid Multi-Task | E-commerce | Multiple objectives, Complex format |

---

*Use these templates as starting points - adjust COSTAR components based on your specific needs!*
