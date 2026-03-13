"""
clinical_trials_loader.py
==========================
Fetches clinical trial data from the ClinicalTrials.gov v2 API and loads it
into a Neo4j graph database using a fully functional (no-class) approach.

Each trial in CLINICAL_TRIALS is fetched live, parsed, and ingested as a
connected subgraph:

    Trial ──TARGETS──► Disease
         ──USES──────► Drug
         ──SPONSORED_BY──► Sponsor
         ──MANAGED_BY────► CRO
         ──CONDUCTED_IN──► Country
         ──LOCATED_AT────► Site ──IN_COUNTRY──► Country
         ──MEASURES──────► Outcome
         ──INCLUDES──────► PatientPopulation
         ──MONITORS──────► Biomarker
         ──FALLS_UNDER───► TherapeuticArea
         ──BELONGS_TO────► TrialCategory
"""

import logging
import requests
from neo4j import GraphDatabase

# ---------------------------------------------------------------------------
# Logging – INFO level so each major step is visible in the console
# ---------------------------------------------------------------------------
logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Neo4j connection – replace URI / credentials before running
# ---------------------------------------------------------------------------
URI  = "neo4j+s://52c31090.databases.neo4j.io"             # e.g. "neo4j://localhost" or AuraDB URL
AUTH = ("52c31090", "DtRQEbNB8H-zXfeJPyhWmOxtEclUQiUztyFF8IRXgqQ") # e.g. ("neo4j", "Root@12345")

# ---------------------------------------------------------------------------
# Trials to fetch – NCT IDs are resolved against the ClinicalTrials.gov API
# ---------------------------------------------------------------------------
CLINICAL_TRIALS = [
    {"nct_id": "NCT04368728", "name": "Remdesivir_COVID"},
    {"nct_id": "NCT04470427", "name": "Pfizer_Vaccine"},
    {"nct_id": "NCT03235752", "name": "Ulcerative_Colitis"},
    {"nct_id": "NCT03961204", "name": "Classic_MS"},
    {"nct_id": "NCT03164772", "name": "Heart_Failure"},
    {"nct_id": "NCT04032704", "name": "CAR-T_Cell"},
    {"nct_id": "NCT03753074", "name": "Hepatitis_B_TAF"},
    {"nct_id": "NCT02014597", "name": "Scleroderma_Study"},
    {"nct_id": "NCT03181503", "name": "Lupus_Nephritis"},
    {"nct_id": "NCT03434379", "name": "Breast_Cancer"},
    {"nct_id": "NCT04652245", "name": "Janssen_COVID_Vax"},
    {"nct_id": "NCT04280705", "name": "Hydroxychloroquine_COVID"},
    {"nct_id": "NCT04614948", "name": "Moderna_Vaccine"},
    {"nct_id": "NCT03548935", "name": "Alzheimers_Trial"},
    {"nct_id": "NCT03155620", "name": "Parkinsons_Study"},
    {"nct_id": "NCT02968303", "name": "HIV_Treatment"},
    {"nct_id": "NCT03518606", "name": "Melanoma_Immuno"},
    {"nct_id": "NCT02863419", "name": "Lung_Cancer_NSCLC"},
    {"nct_id": "NCT02951156", "name": "Prostate_Cancer"},
    {"nct_id": "NCT03374254", "name": "Colon_Cancer"},
    {"nct_id": "NCT02788279", "name": "Leukemia_CAR_T"},
    {"nct_id": "NCT03544736", "name": "Multiple_Myeloma"},
    {"nct_id": "NCT03423992", "name": "Rheumatoid_Arthritis"},
    {"nct_id": "NCT02579382", "name": "Crohns_Disease"},
    {"nct_id": "NCT03662659", "name": "Type2_Diabetes"},
]

# Base URL for the ClinicalTrials.gov v2 REST API
CT_API_BASE = "https://clinicaltrials.gov/api/v2/studies"


# ===========================================================================
# SECTION 1 – API FETCH
# ===========================================================================

def fetch_trial(nct_id: str) -> dict | None:
    """Fetch raw study JSON for one NCT ID from ClinicalTrials.gov v2 API.

    Args:
        nct_id: The ClinicalTrials.gov identifier, e.g. 'NCT04368728'.

    Returns:
        Parsed JSON dict on success, or None if every attempt fails.

    WHY the v2 API?
        The v2 endpoint returns a stable, deeply nested protocolSection that
        maps cleanly onto the graph schema (sponsor, arms, locations, eligibility).
        Earlier v1 responses used flat CSV-style fields that required brittle
        string splitting — v2 gives us typed lists natively.

    WHY a User-Agent header?
        ClinicalTrials.gov rate-limits headless scripts that omit User-Agent.
        Supplying a descriptive string keeps requests identifiable and avoids
        silent 429/403 responses during bulk fetches of 25+ trials.

    WHY retry up to 3 times?
        The API occasionally returns 5xx errors under load. A short retry loop
        recovers from transient failures without a full backoff library.
    """
    url     = f"{CT_API_BASE}/{nct_id}"
    headers = {"User-Agent": "clinical-trials-neo4j-loader/1.0 (research use)"}

    for attempt in range(1, 4):
        try:
            resp = requests.get(url, headers=headers, timeout=20)
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as exc:
            log.warning(f"Attempt {attempt}/3 failed for {nct_id}: {exc}")

    log.error(f"All retries exhausted for {nct_id}")
    return None


def dig(data: dict, *keys, default=None):
    """Safely traverse a nested dict/list by a sequence of keys/indices.

    Args:
        data:    The root dict (or list) to traverse.
        *keys:   Ordered keys or integer indices describing the path.
        default: Value returned when any key is missing or the value is None.

    Returns:
        The value at the resolved path, or *default*.

    WHY a helper instead of chained .get()?
        API responses from ClinicalTrials.gov are deeply nested (6+ levels).
        Chaining .get() produces unreadable one-liners. This helper keeps each
        call site readable while handling KeyError, IndexError, and None
        transparently.
    """
    for key in keys:
        if data is None:
            return default
        try:
            data = data[key]
        except (KeyError, IndexError, TypeError):
            return default
    return data if data is not None else default


# ===========================================================================
# SECTION 2 – API RESPONSE → FLAT GRAPH RECORD
# ===========================================================================

def parse_trial(raw: dict) -> dict:
    """Transform the raw ClinicalTrials.gov v2 JSON into a flat graph record.

    Args:
        raw: The full JSON dict returned by the v2 API for one study.

    Returns:
        A dict keyed by graph-entity names (Trial, Disease, Drug, …) whose
        values are dicts/lists ready to be written directly to Neo4j.

    WHY parse into an intermediate record?
        Separating 'parse the API' from 'write to Neo4j' means each concern
        can be tested and changed independently. The loader functions below
        never touch the raw API shape — they only see this canonical record.
    """
    ps   = dig(raw, "protocolSection", default={})
    ident  = dig(ps, "identificationModule", default={})
    status = dig(ps, "statusModule", default={})
    design = dig(ps, "designModule", default={})
    arms   = dig(ps, "armsInterventionsModule", default={})
    spons  = dig(ps, "sponsorCollaboratorsModule", default={})
    elig   = dig(ps, "eligibilityModule", default={})
    locs   = dig(ps, "contactsLocationsModule", default={})   # v2 key (not "locationsModule")
    outcomes_mod = dig(ps, "outcomesModule", default={})
    conds  = dig(ps, "conditionsModule", default={})

    # Bug fix 2: derivedSection is a sibling of protocolSection at the top level
    # of the API response, NOT nested inside protocolSection. Pulling it from ps
    # always returned [] which is why MeSH terms were missing.
    ds = dig(raw, "derivedSection", default={})

    # Combine condition + intervention MeSH terms so drug-related terms
    # (e.g. "Antiviral Agents") appear alongside disease terms ("COVID-19").
    mesh = (
        dig(ds, "conditionBrowseModule",   "meshes", default=[]) +
        dig(ds, "interventionBrowseModule","meshes", default=[])
    )

    # -- Trial core ----------------------------------------------------------
    trial = {
        "nctId":               dig(ident,  "nctId"),
        "briefTitle":          dig(ident,  "briefTitle"),
        "officialTitle":       dig(ident,  "officialTitle"),
        "acronym":             dig(ident,  "acronym"),
        "overallStatus":       dig(status, "overallStatus"),
        "startDate":           dig(status, "startDateStruct", "date"),
        "primaryCompletionDate": dig(status, "primaryCompletionDateStruct", "date"),
        "completionDate":      dig(status, "completionDateStruct", "date"),
        "studyFirstSubmitDate": dig(status, "studyFirstSubmitDate"),
        "lastUpdateSubmitDate": dig(status, "lastUpdateSubmitDate"),
        "statusVerifiedDate":  dig(status, "statusVerifiedDate"),
        "phase":               ", ".join(dig(design, "phases", default=[])),
        "enrollmentCount":     dig(design, "enrollmentInfo", "count"),
        "enrollmentType":      dig(design, "enrollmentInfo", "type"),
    }

    # -- Disease / Indication (conditions listed by the sponsor) -------------
    conditions = dig(conds, "conditions", default=[])

    # -- Drugs / Interventions -----------------------------------------------
    # WHY filter by interventionType?
    #   Trials list DRUG, DEVICE, PROCEDURE, BEHAVIORAL etc. We capture all
    #   but tag each so downstream Cypher queries can filter by type if needed.
    interventions = [
        {
            "name":       dig(iv, "interventionName"),
            "type":       dig(iv, "interventionType"),
            "otherNames": dig(iv, "otherNames", default=[]),
        }
        for iv in dig(arms, "interventions", default=[])
    ]

    # -- Sponsor + Collaborators (CROs) --------------------------------------
    lead_sponsor = dig(spons, "leadSponsor", "name")
    collaborators = [
        dig(c, "name") for c in dig(spons, "collaborators", default=[])
        if dig(c, "name")
    ]

    # -- Locations -----------------------------------------------------------
    locations = [
        {
            "facility": dig(loc, "facility"),
            "city":     dig(loc, "city"),
            "country":  dig(loc, "country"),
            "zip":      dig(loc, "zip"),
            "lat":      dig(loc, "geoPoint", "lat"),
            "lon":      dig(loc, "geoPoint", "lon"),
        }
        for loc in dig(locs, "locations", default=[])
    ]

    # -- Outcomes ------------------------------------------------------------
    primary_outcomes = [
        {
            "measure":     dig(o, "measure"),
            "description": dig(o, "description", default=""),
            "timeFrame":   dig(o, "timeFrame", default=""),
            "type":        "primary",
        }
        for o in dig(outcomes_mod, "primaryOutcomes", default=[])
    ]
    secondary_outcomes = [
        {
            "measure":   dig(o, "measure"),
            "timeFrame": dig(o, "timeFrame", default=""),
            "type":      "secondary",
        }
        for o in dig(outcomes_mod, "secondaryOutcomes", default=[])
    ]

    # -- Patient population --------------------------------------------------
    patient_population = {
        "eligibilityCriteria": dig(elig, "eligibilityCriteria"),
        "gender":              dig(elig, "sex"),
        "minimumAge":          dig(elig, "minimumAge"),
        "maximumAge":          dig(elig, "maximumAge"),
        "stdAges":             dig(elig, "stdAges", default=[]),
        "healthyVolunteers":   str(dig(elig, "healthyVolunteers", default="")),
    }

    # -- MeSH terms (controlled vocabulary from NLM) -------------------------
    mesh_terms = [dig(m, "term") for m in mesh if dig(m, "term")]

    return {
        "trial":              trial,
        "conditions":         conditions,
        "interventions":      interventions,
        "lead_sponsor":       lead_sponsor,
        "collaborators":      collaborators,
        "locations":          locations,
        "primary_outcomes":   primary_outcomes,
        "secondary_outcomes": secondary_outcomes,
        "patient_population": patient_population,
        "mesh_terms":         mesh_terms,
    }


# ===========================================================================
# SECTION 3 – NEO4J SCHEMA SETUP
# ===========================================================================

def create_constraints_and_indexes(driver):
    """Create uniqueness constraints and lookup indexes before any data loads.

    Args:
        driver: An active Neo4j GraphDatabase driver.

    WHY run this before loading?
        MERGE statements (used throughout the loaders) rely on unique
        constraints to guarantee idempotency — running the loader twice must
        not create duplicate nodes. Indexes on status/phase/city speed up the
        MATCH clauses that link nodes together mid-transaction.
    """
    ddl = [
        # Uniqueness constraints – prevent duplicate nodes on re-runs
        "CREATE CONSTRAINT trial_nct_id        IF NOT EXISTS FOR (t:Trial)           REQUIRE t.nctId     IS UNIQUE",
        "CREATE CONSTRAINT category_name       IF NOT EXISTS FOR (tc:TrialCategory)   REQUIRE tc.name     IS UNIQUE",
        "CREATE CONSTRAINT disease_name        IF NOT EXISTS FOR (d:Disease)          REQUIRE d.name      IS UNIQUE",
        "CREATE CONSTRAINT drug_name           IF NOT EXISTS FOR (dr:Drug)            REQUIRE dr.name     IS UNIQUE",
        "CREATE CONSTRAINT sponsor_name        IF NOT EXISTS FOR (s:Sponsor)          REQUIRE s.name      IS UNIQUE",
        "CREATE CONSTRAINT cro_name            IF NOT EXISTS FOR (cro:CRO)            REQUIRE cro.name    IS UNIQUE",
        "CREATE CONSTRAINT country_name        IF NOT EXISTS FOR (co:Country)         REQUIRE co.name     IS UNIQUE",
        "CREATE CONSTRAINT therapeutic_area    IF NOT EXISTS FOR (ta:TherapeuticArea) REQUIRE ta.area     IS UNIQUE",
        # Lookup indexes – speed up MATCH inside load functions
        "CREATE INDEX trial_status   IF NOT EXISTS FOR (t:Trial)   ON (t.overallStatus)",
        "CREATE INDEX trial_phase    IF NOT EXISTS FOR (t:Trial)   ON (t.phase)",
        "CREATE INDEX site_city      IF NOT EXISTS FOR (si:Site)   ON (si.city)",
        "CREATE INDEX mesh_term_idx  IF NOT EXISTS FOR (m:MeSHTerm) ON (m.term)",
    ]
    with driver.session() as session:
        for stmt in ddl:
            try:
                session.run(stmt)
                log.info(f"DDL OK: {stmt[:60]}…")
            except Exception as exc:
                log.warning(f"DDL skipped (probably exists): {exc}")


# ===========================================================================
# SECTION 4 – NODE / RELATIONSHIP WRITERS
# ===========================================================================

def load_trial_node(session, trial: dict):
    """MERGE a Trial node that is the hub of every other entity in the graph.

    Args:
        session: Active Neo4j session.
        trial:   Flat dict from parse_trial()['trial'].

    WHY MERGE instead of CREATE?
        MERGE is idempotent — safe to re-run the loader without duplicating
        the central Trial node that everything else hangs off of.
    """
    session.run("""
        MERGE (t:Trial {nctId: $nctId})
        SET t.briefTitle           = $briefTitle,
            t.officialTitle        = $officialTitle,
            t.acronym              = $acronym,
            t.overallStatus        = $overallStatus,
            t.startDate            = $startDate,
            t.phase                = $phase,
            t.statusVerifiedDate   = $statusVerifiedDate,
            t.primaryCompletionDate= $primaryCompletionDate,
            t.completionDate       = $completionDate,
            t.studyFirstSubmitDate = $studyFirstSubmitDate,
            t.lastUpdateSubmitDate = $lastUpdateSubmitDate,
            t.enrollmentCount      = $enrollmentCount,
            t.enrollmentType       = $enrollmentType
    """, **trial)


def load_category(session, nct_id: str, conditions: list):
    """MERGE a TrialCategory from the first listed condition and link to Trial.

    Args:
        session:    Active Neo4j session.
        nct_id:     NCT ID of the parent trial.
        conditions: List of condition strings from the API.

    WHY only the first condition?
        TrialCategory is intentionally a coarse grouping (one per trial) used
        for top-level browsing. Granular disease targeting is handled by the
        Disease nodes linked via TARGETS.
    """
    category = conditions[0] if conditions else "Unknown"
    session.run("""
        MERGE (tc:TrialCategory {name: $category})
        WITH tc
        MATCH (t:Trial {nctId: $nctId})
        MERGE (t)-[:BELONGS_TO]->(tc)
    """, category=category, nctId=nct_id)


def load_diseases(session, nct_id: str, conditions: list):
    """MERGE one Disease node per condition and link each to the Trial.

    Args:
        session:    Active Neo4j session.
        nct_id:     NCT ID of the parent trial.
        conditions: List of raw condition strings (e.g. ['Type 2 Diabetes']).

    Relationship created: (Trial)-[:TARGETS]->(Disease)

    WHY MERGE on name?
        Multiple trials may target the same disease. MERGE on name collapses
        them into a shared node so we can later query 'all trials for Disease X'
        without duplicates.
    """
    for condition in conditions:
        if condition and condition.strip():
            session.run("""
                MERGE (d:Disease {name: $name})
                WITH d
                MATCH (t:Trial {nctId: $nctId})
                MERGE (t)-[:TARGETS]->(d)
            """, name=condition.strip(), nctId=nct_id)


def load_drugs(session, nct_id: str, interventions: list):
    """MERGE Drug nodes for each intervention and link them to the Trial.

    Args:
        session:       Active Neo4j session.
        nct_id:        NCT ID of the parent trial.
        interventions: List of dicts {name, type, otherNames} from parse_trial().

    Relationship created: (Trial)-[:USES]->(Drug)

    WHY store otherNames as a property rather than separate nodes?
        Alias names are rarely queried individually — they mainly help human
        readers recognise a drug by its commercial or INN name. Keeping them
        as a list property avoids a costly fan-out of synonym nodes.
    """
    for iv in interventions:
        name = (iv.get("name") or "").strip()
        if name:
            session.run("""
                MERGE (dr:Drug {name: $name})
                SET dr.type       = $type,
                    dr.otherNames = $otherNames
                WITH dr
                MATCH (t:Trial {nctId: $nctId})
                MERGE (t)-[:USES]->(dr)
            """, name=name,
                 type=iv.get("type", ""),
                 otherNames=iv.get("otherNames", []),
                 nctId=nct_id)


def load_sponsor(session, nct_id: str, lead_sponsor: str):
    """MERGE a Sponsor node for the lead organisation and link to Trial.

    Args:
        session:      Active Neo4j session.
        nct_id:       NCT ID of the parent trial.
        lead_sponsor: Name string of the lead sponsor.

    Relationship created: (Trial)-[:SPONSORED_BY]->(Sponsor)
    """
    if lead_sponsor and lead_sponsor.strip():
        session.run("""
            MERGE (s:Sponsor {name: $name})
            WITH s
            MATCH (t:Trial {nctId: $nctId})
            MERGE (t)-[:SPONSORED_BY]->(s)
        """, name=lead_sponsor.strip(), nctId=nct_id)


def load_cros(session, nct_id: str, collaborators: list):
    """MERGE CRO nodes for each collaborator and link them to the Trial.

    Args:
        session:       Active Neo4j session.
        nct_id:        NCT ID of the parent trial.
        collaborators: List of collaborator name strings.

    Relationship created: (Trial)-[:MANAGED_BY]->(CRO)

    WHY CRO (Contract Research Organisation) label?
        Not every collaborator is a CRO, but in pharma trials the overwhelming
        majority of listed collaborators are CROs or co-sponsors playing an
        operational role. The label makes the operational vs. financial sponsor
        distinction queryable without a free-text search.
    """
    for name in collaborators:
        if name and name.strip():
            session.run("""
                MERGE (cro:CRO {name: $name})
                WITH cro
                MATCH (t:Trial {nctId: $nctId})
                MERGE (t)-[:MANAGED_BY]->(cro)
            """, name=name.strip(), nctId=nct_id)


def load_locations(session, nct_id: str, locations: list):
    """MERGE Country and Site nodes from the trial's location list.

    Args:
        session:   Active Neo4j session.
        nct_id:    NCT ID of the parent trial.
        locations: List of dicts {facility, city, country, zip, lat, lon}.

    Relationships created:
        (Trial)-[:CONDUCTED_IN]->(Country)
        (Trial)-[:LOCATED_AT]->(Site)-[:IN_COUNTRY]->(Country)

    WHY lat/lon on the Site rather than Country?
        Country centroids would be misleading for multi-site trials. Storing
        the facility's actual geoPoint enables distance-based queries like
        'find all open trials within 50 km of a patient's location'.
    """
    for loc in locations:
        country = (loc.get("country") or "").strip()
        facility = (loc.get("facility") or "").strip()

        if country:
            session.run("""
                MERGE (co:Country {name: $country})
                WITH co
                MATCH (t:Trial {nctId: $nctId})
                MERGE (t)-[:CONDUCTED_IN]->(co)
            """, country=country, nctId=nct_id)

            if facility:
                session.run("""
                    MERGE (si:Site {facility: $facility})
                    SET si.city = $city,
                        si.zip  = $zip,
                        si.lat  = $lat,
                        si.lon  = $lon
                    WITH si
                    MATCH (t:Trial {nctId: $nctId})
                    MATCH (co:Country {name: $country})
                    MERGE (t)-[:LOCATED_AT]->(si)
                    MERGE (si)-[:IN_COUNTRY]->(co)
                """, facility=facility,
                     city=loc.get("city"),
                     zip=loc.get("zip"),
                     lat=loc.get("lat"),
                     lon=loc.get("lon"),
                     nctId=nct_id,
                     country=country)


def load_outcomes(session, nct_id: str, primary: list, secondary: list):
    """CREATE Outcome nodes for primary and secondary endpoints.

    Args:
        session:   Active Neo4j session.
        nct_id:    NCT ID of the parent trial.
        primary:   List of primary outcome dicts {measure, description, timeFrame}.
        secondary: List of secondary outcome dicts {measure, timeFrame}.

    Relationship created: (Trial)-[:MEASURES]->(Outcome)

    WHY CREATE instead of MERGE?
        Outcome measures are trial-specific free text — two trials may use the
        same phrasing (e.g. 'Overall Survival') but they are logically distinct
        endpoints. MERGE would collapse them into one node, losing trial context.
    """
    for outcome in primary + secondary:
        measure = (outcome.get("measure") or "").strip()
        if measure:
            session.run("""
                CREATE (o:Outcome {
                    measure:     $measure,
                    description: $description,
                    timeFrame:   $timeFrame,
                    type:        $type
                })
                WITH o
                MATCH (t:Trial {nctId: $nctId})
                MERGE (t)-[:MEASURES]->(o)
            """, measure=measure,
                 description=outcome.get("description", ""),
                 timeFrame=outcome.get("timeFrame", ""),
                 type=outcome.get("type", ""),
                 nctId=nct_id)


def load_patient_population(session, nct_id: str, pp: dict):
    """CREATE a PatientPopulation node capturing eligibility criteria.

    Args:
        session: Active Neo4j session.
        nct_id:  NCT ID of the parent trial.
        pp:      Dict {eligibilityCriteria, gender, minimumAge, maximumAge,
                       stdAges, healthyVolunteers}.

    Relationship created: (Trial)-[:INCLUDES]->(PatientPopulation)

    WHY CREATE?
        Eligibility text is trial-specific prose — even trials targeting the
        same population use different wording. Merging on criteria text would
        require exact string match which is fragile and rarely meaningful.
    """
    session.run("""
        CREATE (pp:PatientPopulation {
            eligibilityCriteria: $eligibilityCriteria,
            gender:              $gender,
            minimumAge:          $minimumAge,
            maximumAge:          $maximumAge,
            stdAges:             $stdAges,
            healthyVolunteers:   $healthyVolunteers
        })
        WITH pp
        MATCH (t:Trial {nctId: $nctId})
        MERGE (t)-[:INCLUDES]->(pp)
    """, eligibilityCriteria=pp.get("eligibilityCriteria"),
         gender=pp.get("gender"),
         minimumAge=pp.get("minimumAge"),
         maximumAge=pp.get("maximumAge"),
         stdAges=pp.get("stdAges", []),
         healthyVolunteers=pp.get("healthyVolunteers"),
         nctId=nct_id)


def load_mesh_terms(session, nct_id: str, mesh_terms: list):
    """MERGE MeSHTerm nodes and link them to the Trial.

    Args:
        session:    Active Neo4j session.
        nct_id:     NCT ID of the parent trial.
        mesh_terms: List of MeSH term strings derived by NLM indexers.

    Relationship created: (Trial)-[:ASSOCIATED_WITH]->(MeSHTerm)

    WHY MeSH?
        Medical Subject Headings are NLM's controlled vocabulary — they provide
        a standardised, hierarchical classification of medical concepts. Using
        MeSH nodes enables cross-trial comparisons ('all trials tagged Neoplasms')
        that free-text disease names cannot support reliably.
    """
    for term in mesh_terms:
        if term and term.strip():
            session.run("""
                MERGE (m:MeSHTerm {term: $term})
                WITH m
                MATCH (t:Trial {nctId: $nctId})
                MERGE (t)-[:ASSOCIATED_WITH]->(m)
            """, term=term.strip(), nctId=nct_id)


# ===========================================================================
# SECTION 5 – ORCHESTRATION
# ===========================================================================

def load_record(driver, record: dict):
    """Orchestrate all loader functions for a single parsed trial record.

    Args:
        driver: Active Neo4j GraphDatabase driver.
        record: The dict returned by parse_trial().

    WHY one session per trial?
        Keeping each trial in its own session scopes any failure to that trial
        alone — a bad location string won't roll back the sponsor or drug nodes
        already written for the same trial.
    """
    nct_id = record["trial"].get("nctId")
    if not nct_id:
        log.warning("Skipping record with no nctId")
        return

    with driver.session() as session:
        try:
            load_trial_node(session,       record["trial"])
            load_category(session,         nct_id, record["conditions"])
            load_diseases(session,         nct_id, record["conditions"])
            load_drugs(session,            nct_id, record["interventions"])
            load_sponsor(session,          nct_id, record["lead_sponsor"])
            load_cros(session,             nct_id, record["collaborators"])
            load_locations(session,        nct_id, record["locations"])
            load_outcomes(session,         nct_id, record["primary_outcomes"],
                                                   record["secondary_outcomes"])
            load_patient_population(session, nct_id, record["patient_population"])
            load_mesh_terms(session,       nct_id, record["mesh_terms"])

            # Counts help spot trials where the API returned no locations/mesh data
            log.info(
                f"Loaded {nct_id} | "
                f"conditions={len(record['conditions'])} "
                f"drugs={len(record['interventions'])} "
                f"locations={len(record['locations'])} "
                f"mesh={len(record['mesh_terms'])} "
                f"outcomes={len(record['primary_outcomes'])+len(record['secondary_outcomes'])}"
            )
        except Exception as exc:
            log.error(f"Failed to load {nct_id}: {exc}")


def print_stats(driver):
    """Query and print node counts for the main labels in the graph.

    Args:
        driver: Active Neo4j GraphDatabase driver.
    """
    labels = ["Trial", "Disease", "Drug", "Sponsor", "CRO",
              "Country", "Site", "Outcome", "MeSHTerm", "TherapeuticArea"]
    with driver.session() as session:
        print("\n── Graph statistics ─────────────────────")
        for label in labels:
            count = session.run(
                f"MATCH (n:{label}) RETURN count(n) AS c"
            ).single()["c"]
            print(f"  {label:<20} {count:>5}")
        print("─────────────────────────────────────────\n")


# ===========================================================================
# SECTION 6 – ENTRY POINT
# ===========================================================================

def main():
    """Fetch every trial in CLINICAL_TRIALS, parse it, and load it into Neo4j."""
    with GraphDatabase.driver(URI, auth=AUTH) as driver:

        # Verify the database is reachable before doing any work
        driver.verify_connectivity()
        log.info("Neo4j connection verified")

        # Set up schema (idempotent – safe to run on a populated database)
        create_constraints_and_indexes(driver)

        for entry in CLINICAL_TRIALS:
            nct_id = entry["nct_id"]
            log.info(f"Fetching {nct_id}  ({entry['name']})")

            # Step 1 – pull live data from ClinicalTrials.gov
            raw = fetch_trial(nct_id)
            if raw is None:
                log.warning(f"No data for {nct_id}, skipping")
                continue

            # Step 2 – transform API JSON into a canonical graph record
            record = parse_trial(raw)

            # Step 3 – write every node and relationship into Neo4j
            load_record(driver, record)

        # Show a summary of what ended up in the graph
        print_stats(driver)


if __name__ == "__main__":
    main()