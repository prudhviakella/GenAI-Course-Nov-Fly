# =================================================================
# GOOGLE CLOUD GEN AI FIELD ARCHITECT — INTERVIEW PREP
# Consolidated Q1 + Q2 — Full Thinking Framework + Code
#
# Structure for each question:
#   1. Problem Statement
#   2. Clarifying Questions
#   3. What You Have
#   4. Assumptions
#   5. Solution
#   6. Full Code
# =================================================================


# =================================================================
# =================================================================
# QUESTION 1: FINANCIAL ADVISORY ASSISTANT
# =================================================================
# =================================================================

# -----------------------------------------------------------------
# 1. PROBLEM STATEMENT
# -----------------------------------------------------------------
#
# A bank wants to automate financial advice to customers
# using an LLM agent.
#
# Two risks if we get this wrong:
#
# Risk 1 — Hallucination (Groundedness Problem):
#   LLM generates confident advice not traceable
#   to any approved source document.
#   Customer acts on it.
#   Bank faces regulatory action and liability.
#
# Risk 2 — Unsafe Uncertainty (Suppression Problem):
#   Agent gives an answer it cannot fully verify.
#   Showing uncertain advice is as dangerous
#   as showing hallucinated advice.
#   Bank still faces liability.
#
# Core constraint:
#   Compliance CANNOT be prompt-based.
#   "Never hallucinate" in a system prompt
#   is not legally defensible.
#   Every claim must be deterministically
#   traceable to an approved source.
#
# Opening line for interview:
#   "The bank cannot be liable for an LLM hallucinating
#    financial advice. Compliance must be deterministic —
#    enforced in code, not in prompts.
#    I have two problems: groundedness and suppression.
#    Let me ask a few questions before I design anything."

# -----------------------------------------------------------------
# 2. CLARIFYING QUESTIONS
# -----------------------------------------------------------------
#
# Q1: Is this real-time customer-facing or async report generation?
#   Why it matters:
#   Real-time → max_retries = 3, latency is critical
#   Async     → max_retries = 5+, accuracy over speed
#
# Q2: Does internal policy take absolute precedence over market
#     news in all cases? Or are there exceptions?
#   Why it matters:
#   Absolute   → enforce by sort order in code, simple
#   Exceptions → need conditional priority logic, complex
#
# Q3: What happens to suppressed queries?
#     Is there a human review queue?
#   Why it matters:
#   If yes → HANDOFF_TO_HUMAN with full trace attached
#   If no  → suppress with polite explanation to customer
#
# Q4: Does search_market_news use web search or vector database?
#   Why it matters:
#   Web search → need source allowlist (Bloomberg, Reuters, SEC)
#                open internet = untrusted sources
#   Vector DB  → need ingestion freshness check
#                financial data stale after 4 hours = wrong advice
#   Near real-time VDB → what quality rules applied at ingestion?
#
# Q5: What if internal policy and market news directly conflict
#     on the same data point?
#   Why it matters:
#   Cannot show customer two contradictory numbers
#   → Suppression trigger regardless of confidence
#
# KEY PHRASE:
#   "I ask because the answer changes my design.
#    If market news is open web I need a source validation
#    layer before I trust anything it returns.
#    If it's a vector DB I need to check data freshness
#    because stale financial data is as dangerous
#    as hallucinated data."

# -----------------------------------------------------------------
# 3. WHAT YOU HAVE
# -----------------------------------------------------------------
#
# Two retrieval tools:
#   search_internal_policy(query)
#   → bank approved policies and product data
#   → PRIORITY 1 — always overrides market news
#
#   search_market_news(query)
#   → real-time external market data
#   → PRIORITY 2 — supplementary only
#
# Two LLM calls available:
#   Generator → creates draft answer with [SOURCE_ID] citations
#   Validator → checks groundedness, outputs Boolean only
#
# Constraint:
#   Must write raw orchestration logic
#   No LangChain, CrewAI, LlamaIndex

# -----------------------------------------------------------------
# 4. ASSUMPTIONS
# -----------------------------------------------------------------
#
# Assumption 1 — Source priority is a CODE rule, not a prompt rule
#   Internal policy always overrides market news
#   Enforced by sort order in retrieved context list
#   NOT by instructing the LLM to prioritize
#   Why: LLM can ignore prompt instructions, code cannot
#
# Assumption 2 — Validator never rewrites
#   Validator outputs Boolean + feedback ONLY
#   If Validator could rewrite → Validator itself could hallucinate
#   Strict separation: Generator creates, Validator only judges
#
# Assumption 3 — Confidence is NOT log probability
#   Log probability is unreliable for factual claims:
#     LLM can be 99% confident about wrong facts
#     (learned from internet which contains misinformation)
#     LLM can be confident about claims NOT in retrieved docs
#   Confidence = "Did Validator approve within N retries?"
#   Deterministic, auditable, legally defensible
#
# Assumption 4 — Legal disclaimer always injected by code
#   Never trust LLM to include legal disclaimer
#   Injected programmatically on EVERY response
#   Including suppressed responses
#   Why: LLM may omit it, rephrase it, or get it wrong
#
# Assumption 5 — Silence is safer than wrong answer
#   max_retries = 3 for real-time financial context
#   After 3 failed Validator checks → suppress entirely
#   Never show unverified answer to customer
#   Suppression is a FEATURE not a failure
#
# Assumption 6 — Source conflict is a suppression trigger
#   If internal policy and market news contradict
#   on the same specific data point → suppress immediately
#   Cannot show customer two contradictory numbers

# -----------------------------------------------------------------
# 5. SOLUTION
# -----------------------------------------------------------------
#
# Step 1 — Retrieve and prioritize (code-enforced)
#   Call both tools
#   Sort combined results by priority in code:
#     internal_policy docs → priority 1
#     market_news docs     → priority 2
#   LLM sees context in this order — highest trust first
#
# Step 2 — Source validation (if web search)
#   Filter to trusted domains only:
#     Bloomberg, Reuters, SEC, RBI, FT, WSJ
#   Remove untrusted sources before passing to Generator
#
# Step 3 — Freshness check (if vector DB)
#   Check ingested_at timestamp per document
#   Flag docs older than 4 hours with staleness warning
#   Don't suppress — but warn Generator in context
#
# Step 4 — Deterministic citation check FIRST (zero token cost)
#   Before any LLM call:
#   Does draft contain [SOURCE_ID] tags?
#   Do those SOURCE_IDs exist in retrieved docs?
#   If not → immediate rejection, zero token cost
#   Always run this before Validator LLM call
#
# Step 5 — Generator / Validator reflection loop
#   Generator creates draft with [SOURCE_ID] citations
#   Validator checks: is every claim traceable to retrieved doc?
#   Validator outputs: is_approved (Boolean) + feedback (string)
#   Validator NEVER rewrites the draft
#   On rejection → Generator retries with Validator feedback
#
# Step 6 — On Validator approval
#   Inject legal disclaimer programmatically
#   Return answer with citations and sources
#   Status: 200_APPROVED
#
# Step 7 — On exhausted retries (suppression)
#   Return NOTHING to customer as answer
#   Route to HANDOFF_TO_HUMAN with full trace
#   Inject legal disclaimer even on suppression
#   Status: 400_LOW_CONFIDENCE

# -----------------------------------------------------------------
# 6. FULL CODE
# -----------------------------------------------------------------

from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime, timezone


# ── Data Structures ───────────────────────────────────────────────

@dataclass
class SourceDocument:
    """
    A retrieved document from either tool.
    priority: 1 = internal policy, 2 = market news
    source_id: used for [SOURCE_ID] citation tags
    ingested_at: for freshness check (vector DB sources)
    source_url: for allowlist check (web search sources)
    """
    source_id:   str
    content:     str
    priority:    int                    # 1=internal, 2=market
    source_url:  Optional[str] = None   # web search sources
    ingested_at: Optional[datetime] = None  # vector DB sources


@dataclass
class GeneratorDraft:
    text:      str
    citations: list[str]    # list of [SOURCE_ID] tags found


@dataclass
class ValidatorResult:
    is_approved: bool
    improvement_suggestions: str    # feedback to Generator on retry
    # Validator NEVER rewrites — only Boolean + feedback


@dataclass
class AgentResponse:
    status:          str            # "200_APPROVED" | "400_LOW_CONFIDENCE"
    answer:          Optional[str]  # None if suppressed
    citations:       list[str]
    sources_used:    list[str]
    action:          Optional[str]  # "HANDOFF_TO_HUMAN" if suppressed
    legal_disclaimer: str           # always injected by code
    retry_count:     int
    failure_reason:  Optional[str]


# ── Tool Stubs (provided by bank infrastructure) ─────────────────

def search_internal_policy(query: str) -> list[SourceDocument]:
    """
    Returns bank's approved policies and product data.
    Priority 1 — always overrides market news.
    """
    # Stub — returns mock internal policy document
    return [
        SourceDocument(
            source_id="INT_001",
            content="Our APAC Growth Fund has delivered 8.2% YTD returns "
                    "as of Q3 2024. Minimum investment: ₹50,000.",
            priority=1,
            source_url="internal://policy/apac-fund"
        )
    ]


def search_market_news(query: str) -> list[SourceDocument]:
    """
    Returns real-time external market data.
    Priority 2 — supplementary only.
    Source must be validated before use.
    """
    # Stub — returns mock market news document
    return [
        SourceDocument(
            source_id="MKT_001",
            content="APAC equity markets showed strong momentum "
                    "in Q3 2024 with average fund returns of 9.1%.",
            priority=2,
            source_url="reuters.com/markets/apac-q3",
            ingested_at=datetime.now(timezone.utc)
        )
    ]


# ── Source Validation ─────────────────────────────────────────────

# Trusted domains for web search sources
# Anything not in this list is rejected before Generator sees it
TRUSTED_DOMAINS = [
    "bloomberg.com",
    "reuters.com",
    "sec.gov",
    "rbi.org.in",
    "ft.com",
    "wsj.com",
    "internal://"       # internal policy always trusted
]

STALENESS_THRESHOLD_HOURS = 4      # financial data stale after 4 hours


def _validate_source(doc: SourceDocument) -> tuple[bool, str]:
    """
    Two checks:
    1. Source allowlist — is this a trusted domain?
    2. Freshness check — is this data recent enough?

    KEY POINT:
    "Stale financial data is as dangerous as hallucinated data.
     A price from yesterday morning is wrong by 3 PM today."
    """

    # Internal policy always trusted — skip checks
    if doc.priority == 1:
        return True, ""

    # Check 1: Source allowlist
    if doc.source_url:
        is_trusted = any(
            domain in doc.source_url
            for domain in TRUSTED_DOMAINS
        )
        if not is_trusted:
            return False, (
                f"Untrusted source rejected: {doc.source_url}. "
                f"Only approved financial sources accepted."
            )

    # Check 2: Freshness check (vector DB sources have ingested_at)
    if doc.ingested_at:
        now       = datetime.now(timezone.utc)
        age_hours = (now - doc.ingested_at).seconds / 3600

        if age_hours > STALENESS_THRESHOLD_HOURS:
            # Don't reject — add staleness warning to content
            doc.content += (
                f"\n[STALENESS WARNING: Data is {age_hours:.1f} hours old. "
                f"Verify current values before acting on this information.]"
            )

    return True, ""


# ── Deterministic Citation Check ──────────────────────────────────

def _check_citation_format(
    draft: GeneratorDraft,
    available_source_ids: set[str]
) -> tuple[bool, str]:
    """
    Deterministic check — runs BEFORE Validator LLM call.
    Zero token cost.

    Checks:
    1. Does draft contain any [SOURCE_ID] citations?
    2. Do all cited SOURCE_IDs exist in retrieved docs?

    KEY POINT:
    "I run this before the Validator LLM call deliberately.
     If citations are malformed or hallucinated, I catch it
     for free without spending a single token."
    """

    if not draft.citations:
        return False, (
            "No citations found in draft. "
            "Every claim must include a [SOURCE_ID] tag."
        )

    for cited_id in draft.citations:
        if cited_id not in available_source_ids:
            return False, (
                f"Citation [{cited_id}] does not exist "
                f"in retrieved documents. "
                f"Available IDs: {available_source_ids}"
            )

    return True, ""


# ── Generator LLM ────────────────────────────────────────────────

def _call_generator(
    query: str,
    context_docs: list[SourceDocument],
    past_feedback: Optional[str] = None
) -> GeneratorDraft:
    """
    Generates a draft answer with [SOURCE_ID] citation tags.

    KEY POINT:
    "Generator's ONLY job is to produce a draft with
     every claim cited to a source document.
     It does not verify its own output — that's Validator's job."

    System prompt enforces:
    - Every claim must end with [SOURCE_ID]
    - Use only information from provided context
    - If context doesn't contain the answer, say so explicitly
    """

    context_text = "\n\n".join([
        f"[{doc.source_id}] (Priority {doc.priority}): {doc.content}"
        for doc in context_docs
    ])

    feedback_instruction = ""
    if past_feedback:
        feedback_instruction = (
            f"\n\nPrevious attempt was rejected. "
            f"Specific issues to fix: {past_feedback}"
        )

    system_prompt = f"""
You are a financial advisor assistant.
Answer the query using ONLY the provided context documents.
After every claim, add the source citation in format [SOURCE_ID].
Example: "The fund returned 8% [INT_001] in Q3."

If the context does not contain enough information to answer safely,
respond with: INSUFFICIENT_CONTEXT

Context documents:
{context_text}
{feedback_instruction}
"""

    # In production: response = llm_api.generate(system_prompt, query)
    # Stub response:
    raw_text = (
        "Our APAC Growth Fund delivered 8.2% YTD returns [INT_001]. "
        "This compares favorably to the broader APAC market average "
        "of 9.1% [MKT_001]. Minimum investment is ₹50,000 [INT_001]."
    )

    # Extract citation tags from response
    import re
    citations = re.findall(r'\[([A-Z_0-9]+)\]', raw_text)

    return GeneratorDraft(
        text=raw_text,
        citations=list(set(citations))
    )


# ── Validator LLM ─────────────────────────────────────────────────

def _call_validator(
    draft: GeneratorDraft,
    context_docs: list[SourceDocument]
) -> ValidatorResult:
    """
    Validates groundedness of draft against source documents.

    KEY POINTS:
    "Validator has one job: check if every claim in the draft
     is traceable to a retrieved source document.

     Validator outputs Boolean + feedback ONLY.
     Validator NEVER rewrites the draft.
     If Validator rewrote the draft, it could hallucinate too.
     We'd just move the problem one step.

     This is External Reflection — separate LLM with
     different weights means different failure modes.
     Much stronger than self-reflection."
    """

    context_text = "\n\n".join([
        f"[{doc.source_id}]: {doc.content}"
        for doc in context_docs
    ])

    system_prompt = f"""
You are a strict financial compliance validator.
Your ONLY job is to check if every claim in the answer
is directly supported by the provided source documents.

Source documents:
{context_text}

Answer to validate:
{draft.text}

Output format (STRICT):
APPROVED: true/false
FEEDBACK: <specific claims that are ungrounded, if any>

Do NOT rewrite the answer. Do NOT suggest improvements.
Only output APPROVED and FEEDBACK.
"""

    # In production: response = llm_api.generate(system_prompt)
    # Stub — approved for demonstration:
    return ValidatorResult(
        is_approved=True,
        improvement_suggestions=""
    )


# ── Legal Disclaimer ──────────────────────────────────────────────

def _get_mandatory_disclaimer() -> str:
    """
    Always injected by code — never by LLM.

    KEY POINT:
    "Legal disclaimer is programmatically injected on every
     response including suppressed ones.
     I never trust the LLM to include it — it might rephrase
     it, omit it, or get the wording wrong.
     This is non-negotiable compliance logic."
    """
    return (
        "DISCLAIMER: This information is for educational purposes only "
        "and does not constitute financial advice. Past performance is "
        "not indicative of future results. Please consult a certified "
        "financial advisor before making investment decisions."
    )


# ── Conflict Detection ────────────────────────────────────────────

def _detect_source_conflict(
    internal_docs: list[SourceDocument],
    market_docs: list[SourceDocument]
) -> tuple[bool, str]:
    """
    Checks if internal policy and market news directly contradict
    on the same data point.

    KEY POINT:
    "If internal policy says our fund returned 8%
     and market news says APAC funds returned 12%,
     that's not necessarily a conflict — different scopes.

     But if internal policy says fund NAV is ₹100
     and market news says fund NAV is ₹87 —
     same data point, different values.
     I cannot show the customer both.
     This is an immediate suppression trigger."

    In production: use LLM to detect semantic conflicts.
    Stub: return no conflict for demonstration.
    """
    # In production: semantic conflict detection via LLM
    return False, ""


# ── Main Orchestration Function ───────────────────────────────────

def run_financial_agent(user_query: str) -> AgentResponse:
    """
    Main orchestration function for Financial Advisory Agent.

    Flow:
    1. Retrieve from both sources
    2. Validate sources (allowlist + freshness)
    3. Check for conflicts
    4. Generator/Validator reflection loop (max 3 retries)
    5. On approval → return with disclaimer
    6. On exhaustion → suppress, handoff to human

    KEY DESIGN DECISIONS to verbalize:
    - Source priority enforced by sort order in code (not prompt)
    - Deterministic citation check BEFORE Validator LLM call
    - Validator never rewrites — Boolean + feedback only
    - Legal disclaimer injected by code on every response
    - Silence safer than unverified answer in financial context
    """

    print(f"\n[AGENT] Query: {user_query}")

    # ── Step 1: Retrieve from both sources ────────────────────────
    internal_results = search_internal_policy(user_query)
    market_results   = search_market_news(user_query)

    # ── Step 2: Validate market sources ───────────────────────────
    # Source allowlist + freshness check
    validated_market = []
    for doc in market_results:
        is_valid, reason = _validate_source(doc)
        if is_valid:
            validated_market.append(doc)
        else:
            print(f"[AGENT] Source rejected: {reason}")

    # If all market sources rejected → use internal only
    # Internal policy is always valid — no validation needed
    if not validated_market:
        print("[AGENT] No valid market sources — using internal only")

    # ── Step 3: Check for conflicts ───────────────────────────────
    has_conflict, conflict_reason = _detect_source_conflict(
        internal_results, validated_market
    )

    if has_conflict:
        print(f"[AGENT] Source conflict detected: {conflict_reason}")
        return AgentResponse(
            status="400_CONFLICT",
            answer=None,
            citations=[],
            sources_used=[],
            action="HANDOFF_TO_HUMAN",
            legal_disclaimer=_get_mandatory_disclaimer(),
            retry_count=0,
            failure_reason=f"Source conflict: {conflict_reason}"
        )

    # ── Step 4: Combine and sort by priority (CODE enforced) ──────
    # Internal policy (priority=1) always appears before market (priority=2)
    # This is a hard business rule enforced by sort order
    # NOT by telling the LLM to prioritize
    combined_context = sorted(
        internal_results + validated_market,
        key=lambda doc: doc.priority
    )

    available_source_ids = {
        doc.source_id for doc in combined_context
    }

    print(f"[AGENT] Context: {len(combined_context)} docs | "
          f"Source IDs: {available_source_ids}")

    # ── Step 5: Generator / Validator reflection loop ─────────────
    max_retries      = 3       # real-time financial context
    attempt          = 0
    critique_feedback = None

    while attempt < max_retries:
        print(f"[AGENT] Attempt {attempt + 1}/{max_retries}")

        # Generate draft with citations
        draft = _call_generator(
            query=user_query,
            context_docs=combined_context,
            past_feedback=critique_feedback
        )

        # ── Deterministic check FIRST (zero token cost) ──────────
        # Run BEFORE Validator LLM call to save tokens
        is_valid, format_error = _check_citation_format(
            draft, available_source_ids
        )

        if not is_valid:
            print(f"[AGENT] Citation format check failed: {format_error}")
            critique_feedback = format_error
            attempt += 1
            continue

        # ── Validator LLM check (semantic groundedness) ──────────
        validation = _call_validator(draft, combined_context)

        if validation.is_approved:
            print(f"[AGENT] Validated on attempt {attempt + 1}")
            return AgentResponse(
                status="200_APPROVED",
                answer=draft.text,
                citations=draft.citations,
                sources_used=list(available_source_ids),
                action=None,
                legal_disclaimer=_get_mandatory_disclaimer(),
                retry_count=attempt + 1,
                failure_reason=None
            )

        # Validator rejected — store feedback for next attempt
        print(f"[AGENT] Validator rejected: "
              f"{validation.improvement_suggestions}")
        critique_feedback = validation.improvement_suggestions
        attempt += 1

    # ── Step 6: Suppression — retries exhausted ───────────────────
    # Silence is safer than an unverified answer
    # Suppression is a FEATURE not a failure
    print(f"[AGENT] Suppressing — could not verify after {max_retries} attempts")

    return AgentResponse(
        status="400_LOW_CONFIDENCE",
        answer=None,                    # nothing shown to customer
        citations=[],
        sources_used=[],
        action="HANDOFF_TO_HUMAN",      # route to human review
        legal_disclaimer=_get_mandatory_disclaimer(),
        retry_count=max_retries,
        failure_reason=(
            f"Could not verify all claims after "
            f"{max_retries} attempts. "
            f"Last feedback: {critique_feedback}"
        )
    )

if __name__ == "__main__":

    # ── Q1: Financial Advisory Agent ─────────────────────────────
    print("\n" + "="*60)
    print("Q1: FINANCIAL ADVISORY AGENT")
    print("="*60)

    response = run_financial_agent(
        "Should I invest in the APAC Growth Fund?"
    )