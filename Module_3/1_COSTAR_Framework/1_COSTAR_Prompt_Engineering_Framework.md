Costar concise guide · MD
Copy

# COSTAR Prompt Engineering Framework
## Practical Guide for AWS Bedrock & OpenAI

---

## What is COSTAR?

COSTAR is a framework for writing effective prompts. It has 6 components:

```
C - Context
O - Objective  
S - Style
T - Tone
A - Audience
R - Response Format
```

---

## The 6 Components Explained

### **C - Context**
**What it is:** Background information about the situation

**Example:**
```
Context: You are a customer service AI for an e-commerce electronics store. 
The customer has been waiting 10 days for an order that should have arrived in 5-7 days.
```

---

### **O - Objective**
**What it is:** The specific task or goal

**Example:**
```
Objective: Write an email that apologizes for the delay, explains the situation, 
and offers a solution to retain the customer.
```

---

### **S - Style**
**What it is:** HOW you write (structure and format)

**Think:** The tool you use - bullets, paragraphs, technical language, simple words

**Example:**
```
Style: Professional customer service representative with clear, structured responses
```

---

### **T - Tone**
**What it is:** HOW you sound (emotion and attitude)

**Think:** The feeling you convey - friendly, serious, urgent, calm

**Example:**
```
Tone: Empathetic and apologetic, but confident in the solution
```

---

### **Style vs. Tone - Simple Explanation**

**Style** = Format and structure  
**Tone** = Attitude and feeling

**Example:** Same message, different style and tone

```
Message: "The project will be delayed"

STYLE (structure):
• Short: "The project will be delayed."
• Detailed: "Due to supply chain issues, the project timeline will extend by 2 weeks."
• Bullets: "• Status: Delayed • Reason: Supply issues • New date: +2 weeks"

TONE (feeling):
• Calm: "The project will be delayed. We have a plan to get back on track."
• Apologetic: "I'm really sorry, but the project will be delayed."
• Urgent: "The project will be delayed! We need to act now."
```

---

### **A - Audience**
**What it is:** Who will read this

**Example:**
```
Audience: A frustrated customer who values quick service and has been loyal for 3+ years
```

---

### **R - Response Format**
**What it is:** The structure of the output

**Example:**
```
Response Format: 
1. Greeting with apology
2. Explanation in 2-3 sentences
3. Solution offered
4. Closing with contact info
```

---

## Complete COSTAR Example

### E-commerce Customer Service

```
Context: You are a customer service AI for "TechStore." A loyal customer's order 
(#12345) was placed 10 days ago with 5-7 day shipping promise. They just contacted 
asking where their laptop is.

Objective: Write an email response that keeps this customer happy and loyal.

Style: Professional but friendly customer service, clear and organized

Tone: Apologetic and empathetic, but confident we'll fix it

Audience: A busy professional who is frustrated but has been a loyal customer

Response Format:
1. Apologize sincerely
2. Explain what happened (briefly)
3. Offer specific solution
4. Close with reassurance

---

Customer's message: "Where is my laptop? It's been 10 days and I needed it for work!"

Write the response email.
```