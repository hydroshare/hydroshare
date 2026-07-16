"""
Categorize an existing spam_report.csv produced by ai_spam_resources.
Adds a 'category' column based on the buckets identified from the data.

Buckets (in priority order):
  FALSE_POSITIVE        - confirmed legitimate water-related resources misclassified
  EXTERNAL_SPAM         - commercial ads, essay services, travel, gaming
  STUDENT_WORK          - class assignments, homework, course exercises
  PLATFORM_INFRA        - logos, release notes, news articles (NOT conference presentations)
  OFF_TOPIC             - content clearly unrelated to water
  GEOGRAPHIC_PLACEHOLDER - only a place/name, no content
  TEST_DEV              - test/demo/debug resources from developers or staff
  OTHER                 - doesn't fit the above

Usage:
    python3 scripts/categorize_spam_report.py spam_report.csv [output.csv]
"""

import csv, re, sys

INPUT_FILE  = sys.argv[1] if len(sys.argv) > 1 else "spam_report.csv"
OUTPUT_FILE = sys.argv[2] if len(sys.argv) > 2 else INPUT_FILE.replace(".csv", "_categorized.csv")

# ─── Rules ────────────────────────────────────────────────────────────────────

# Confirmed false positives — legitimate water/science resources the AI misclassified
R_FALSE_POS_TITLE = re.compile(
    # Conference/academic presentations (CIROH DevCon, AGU, AMS, NWHC, etc.)
    r"ciroh devcon|cuahsi.*devcon|devcon.*cuahsi|"
    r"\bagu \d{4}\b|\bams \d{4}\b|\bufwi \d{4}\b|\bawra\b|"
    r"\bnwhc \d{4}\b|\bnhwc \d{4}\b|"
    r"science meeting.*presentation|presentation.*science meeting|"
    r"lightning talk|devcon.*workshop|workshop.*devcon|devcon.*keynote|"
    r"devcon.*poster|summer institute.*workshop|"
    # Water research software tools/binaries
    r"gdal.*binary|binary.*gdal|virtual gdal|cyberduck software|"
    # Directly water-related resources
    r"nitrate calculator|"
    r"informe de confianza al consumidor|"  # Consumer Confidence Report = water utility doc
    r"tethered balloon.*atmospheric|"       # CTEMPs = stream temperature org
    r"asainju_homewatershed|"
    r"floodmap.*viewer|"
    r"test python code for summa|"          # SUMMA = hydrology model
    r"porosity.?dependent.*elastic moduli|"
    r"radial invasion patterns.*fluids.*fracture|"
    r"bridge foundations.*waterborne sediments|"
    # Puerto Rico disaster response project (water infrastructure)
    r"health services in puerto rico|"
    r"population health reports for puerto rico|"
    r"pharmacies in puerto rico|"
    r"urgent care facilities in puerto rico|"
    # Community poems by HydroShare members
    r"hydroinformatics poem|hidroinformatic.*poem|poema hidroinform",
    re.I,
)

R_EXT_SPAM_TITLE = re.compile(
    r"essay|persuasive|argumentative|expository|synthesis|speech writing|"
    r"informative essay|compare and contrast|essay outline|extemporaneous|"
    r"rogerian|exemplification|good country people|"
    r"PUBG|sewa mobil|pakej percutian|labuan bajo tour|aquatec innovative|"
    r"buy cheap|cheap medication|escort|antivirus|staying hydrated|"
    r"water.*human body|human body.*water|hydration.*health",
    re.I,
)
R_EXT_SPAM_USERS = {"william130","jogjacars","pakejpadang","labuanbajotour","aquatec","alexandramario22"}

R_STUDENT_TITLE = re.compile(
    r"\b514\b|byu\b|ceen\b|ce\s*en\b|class.*exercise|exercise.*class|"
    r"\bhomework\b|hw\d|lab\d+\b|\bassignment\b|in.?class\b|inclass\b|"
    r"web map activity|nfie2017|cyber.?carpentry|summer institute|"
    r"nwc si 2019|intersect.*training|training.*intersect|\[training\]|\[byu|"
    r"\bA\d+[-_][A-Za-z]|KylerAshby|flood forecasting.*dream vacations|"
    r"brigham young university class|cities i want to visit|"
    r"visited.?countries|shapes of interest",
    re.I,
)
R_STUDENT_REASON = re.compile(r"student|homework|class|course|assignment|software training", re.I)

R_INFRA_TITLE = re.compile(
    r"\blogo[s]?\b|release notes|migration timeline|"
    r"\bcjw\b|i-guide jupyterhub|jupyterhub$|binderhub|binder.*dockerfile|"
    r"official list.*apps|approved apps|hydroshare pictures|"
    r"data series viewer|geoconnex|cybergis.?compute|"
    r"compile.*rhessys|sciunit.*export|binder.*parflow|"
    r"uploading.*google drive|open science contribution|"
    r"featured.*courses|featured.*datasets|"
    r"ciroh.*portal|portal.*ciroh|"
    r"google.*articles|news.*articles|"
    r"loeffler.*flyover|flyover.*country|"
    r"semantic scholar|iguide.?datacatalog|"
    r"gdal.*ogr|"
    r"documents for cuahsi|ad hoc committee|"
    r"enviro.?wiki|tech transfer|"
    r"cybergis.?jupyter.*release|cjw.*release|"
    r"cybergis.?jupyter.*migration|cjw.*migration|"
    r"logos_honduras|logos_panama|logos_belize|logos_guatemala|"
    r"social_vulnerability_index|social vulnerability index|"
    r"ssl cert.*hydroshare|side effect.*ssl|"
    r"gateway file actions|file actions dropdown",
    re.I,
)
R_INFRA_REASON = re.compile(
    r"\blogo\b|release notes|news articles|middleware", re.I,
)

R_OFFTOPIC_TITLE = re.compile(
    r"\bair pollution\b|food inspection|\bcovid\b|"
    r"pollen count|electricity generation|permian basin|"
    r"turfgrass|coyotes.*cougar|cougar.*coyote|"
    r"cities.*visit|visit.*cities|places.*visited|visited.*places|"
    r"cities i want|pakej percutian|labuan bajo|sewa mobil|tour resource|"
    r"aircraft.*detect|radar.*ads-b|"
    r"\bpoem\b|hidroinformatic.*poem|poema|"
    r"impact of land use on air|health.*hydration|"
    r"clean water.*hydration|water.*human body|"
    r"significant factor of soil forming|"
    r"urban.?informatics|ma colleges|"
    r"flood forecasting.*dream|dream.*vacation",
    re.I,
)
R_OFFTOPIC_REASON = re.compile(
    r"unrelated to water|no connection to water|not related to water|"
    r"travel|tourism|\bair pollution\b|food inspection|"
    r"gaming|personal travel|book writing|"
    r"turfgrass|coyote", re.I,
)

R_GEO_USERS = {"sherenachills"}
R_GEO_TITLE  = re.compile(r"^[A-Za-z][A-Za-z\s\-\.]{1,22}$")
R_GEO_REASON = re.compile(
    r"no relevant information|no plausible connection|too vague|lacks.*content|"
    r"no meaningful|abstract.*name|only.*name", re.I,
)

R_TEST_TITLE = re.compile(
    r"^(test|testing|tests|demo|dummy|debug|hello world|hello from|"
    r"hstest|hstestmodel|hs\s*#|binder|new resource|new_resource|"
    r"my first|myfirst|example resource|warehouse app|"
    r"jupyter.*test|test.*jupyter|jupyter.*demo|sciunit|csvtest|"
    r"again$|est$|vert check|watershed test|resource creator|"
    r"resource for testing|assorted file|test.*copy|copy.*test|"
    r"geoserver test|wms test|test wms|web map.*test|test.*web map|"
    r"test.*resource|resource.*test|test_\d+|test \d+|test\d+|"
    r"nwm.*test|test.*nwm|irods test|another test|swat test|"
    r"lab\d+$|nwis resource|hs #|hs#|"
    r"jerson data|example.*data|data.*example|qgis export|"
    r"untitled resource|ngiab.*tethys|tethys.*ngiab|"
    r"wabash example|composite resource type design|"
    r"hello.*jupyterhub|jupyterhub.*hello|"
    r"a test.*purposes|test.*purposes|"
    r"NWM_App_Display|NWM_New_Test|api-sd\d|"
    r"dummy data|sciunit testing|stream$|"
    r"reaches$|catchment_nexus|r\d+_geom|r\d+_reaches|"
    r"resource viewer$|wms map viewer|"
    r"webinar demo|\bbbgc\d+|hdr raster|\bexample$|"
    r"flatriver_|\bh\d+$|\bdcia\b|ky\d$|large epanet|"
    r"datebase|floodmap_database|hydroshare sample|hydroshare_test|"
    r"jupyter notebook.*(snow|puyallup|rhessys)|"
    r"correlation script|openagua|\bpackage$|\bpractice \d|"
    r"rhessys model|rhessys input|summa model instance|"
    r"smcdonald.*watershed|\bfldta\b|ikewai.*dev|"
    r"myanalysis|\bhydro$|valid_winter|bbgc62|"
    r"coweeta.*rhessys|rhessys.*coweeta|"
    r"plot of ueb|ueb.*sac.sma|ueb output|"
    r"fsr\d+.*bighorn|hydrogeophysics|"
    r"czo.*geophysics|geophysics.*czo|"
    r"taudem.*terrain|terrain.*taudem|"
    r"\bvic$|cliamte_model|"
    r"pandora.*project|pandora.*climate|"
    r"surface water barriers|basinmorphometric|"
    r"viewing geospatial|geospatial.*service|"
    r"binder.vanilla|flask.*example|matlab test|his reference|"
    r"tohoku\d+.*test|test.*tohoku|"
    r"sciunit testing|assorted file.*composite|"
    r"geotrust server|geotrust$|"
    r"mybinder$|cvmfs|cern.*virtual machine)",
    re.I,
)
R_TEST_REASON = re.compile(
    r"test resource|demo resource|placeholder|dummy|debugging|"
    r"no legitimate|vague.*test|test.*vague|generic test|"
    r"nonsensical|gibberish|repetitive test|Lorem Ipsum|"
    r"demo session|appears.*test|test.*appears", re.I,
)
R_TEST_USERS = {
    "drew","dtarb","mseul","TonyCastronova","aaraney","igarousi",
    "sblack","dcowan","pkdash","rayi","sherry","jerson01",
    "danames","rfun","lmarini","SteveCossSWOT","ElkinGiovanni",
    "sandeshm","sandesh","testwithnodots","devin.r.cowan@dartmouth.edu",
}


def categorize(row: dict) -> str:
    title  = row.get("title",  "")
    reason = row.get("reason", "")
    users  = row.get("owner_usernames", "").split("|")
    user0  = users[0].strip()

    # FALSE_POSITIVE checked first — protects confirmed legitimate resources
    if R_FALSE_POS_TITLE.search(title):
        return "FALSE_POSITIVE"

    if user0 in R_EXT_SPAM_USERS or R_EXT_SPAM_TITLE.search(title):
        return "EXTERNAL_SPAM"

    if R_STUDENT_TITLE.search(title) or R_STUDENT_REASON.search(reason):
        return "STUDENT_WORK"

    if R_INFRA_TITLE.search(title) or R_INFRA_REASON.search(reason):
        return "PLATFORM_INFRA"

    if R_OFFTOPIC_TITLE.search(title) or R_OFFTOPIC_REASON.search(reason):
        return "OFF_TOPIC"

    if user0 in R_GEO_USERS:
        return "GEOGRAPHIC_PLACEHOLDER"
    if R_GEO_TITLE.match(title) and R_GEO_REASON.search(reason):
        return "GEOGRAPHIC_PLACEHOLDER"

    if user0 in R_TEST_USERS or R_TEST_TITLE.search(title) or R_TEST_REASON.search(reason):
        return "TEST_DEV"

    return "OTHER"


# ─── Process CSV ──────────────────────────────────────────────────────────────

with open(INPUT_FILE, newline="", encoding="utf-8") as f:
    reader    = csv.DictReader(f)
    fieldnames = list(reader.fieldnames or [])
    if "category" not in fieldnames:
        idx = fieldnames.index("verdict") + 1 if "verdict" in fieldnames else 1
        fieldnames.insert(idx, "category")
    rows = list(reader)

CATEGORIES = [
    "EXTERNAL_SPAM","TEST_DEV","STUDENT_WORK","PLATFORM_INFRA",
    "GEOGRAPHIC_PLACEHOLDER","OFF_TOPIC","FALSE_POSITIVE","OTHER",
]

with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    counts = {}
    for row in rows:
        if row.get("verdict") == "SPAM":
            row["category"] = categorize(row)
        counts[row.get("category", "")] = counts.get(row.get("category", ""), 0) + 1
        writer.writerow(row)

genuine = sum(counts.get(c, 0) for c in CATEGORIES if c not in ("FALSE_POSITIVE", "OTHER"))
fp      = counts.get("FALSE_POSITIVE", 0) + counts.get("OTHER", 0)
total   = sum(counts.values())

print(f"Written {len(rows)} rows to {OUTPUT_FILE}\n")
print("Category breakdown:")
for cat in CATEGORIES:
    n = counts.get(cat, 0)
    tag = "  ← excluded from spam count" if cat in ("FALSE_POSITIVE","OTHER") else ""
    print(f"  {cat:<30} {n}{tag}")
print(f"\n  Total flagged by AI:       {total}")
print(f"  False positives excluded:  {fp}")
print(f"  Genuine concerns:          {genuine}")
