"""
clean_momijiyama.py
Parse, clean, and flag the Momijiyama provenance records.

Input : data/momijiyama/evidence_with_translations.md  (pasted "Key: value" text)
        or a .csv with the same column names
Output: data/momijiyama/clean/records_clean.csv   (all unique records, flagged)
        data/momijiyama/clean/books_clean.csv     (non-administrative records only)
        data/momijiyama/clean/qa_report.txt       (what was dropped / flagged)
"""
import re
from pathlib import Path

import pandas as pd

RAW_PATH = Path("momijiyama_data/translations_parley/evidence_with_translations.csv")  # or .csv
OUT_DIR = Path("momijiyama_data/clean")
OUT_DIR.mkdir(parents=True, exist_ok=True)

KEYS = [
    "Record_ID", "Library", "Title_and_Author", "Volume_Info",
    "Exact_Provenance_Language_JP", "Remarks_Notes", "Type_Category",
    "Fascicle_Count", "Keywords_Present", "Search_Term_Hit", "Search_Category",
    "Source_URL", "Literal_English_Translation", "Confidence_Level",
    "Notes_and_Uncertainty", "Extraction_Date", "Summary",
]
KEY_RE = re.compile(r"^(" + "|".join(KEYS) + r"):(.*)$")

# ---------------------------------------------------------------------------
# Heuristic rules. These are starting points: review the QA report and
# adjust the patterns. First match wins for edition_origin.
# ---------------------------------------------------------------------------
EDITION_RULES = [
    ("Korean print", r"韓板|朝鮮板"),
    ("Ming print", r"明官板|明板"),
    ("Song/Yuan print", r"宋板|宋槧|北宋|元大德"),
    ("Korean-held copy", r"韓人|高麗國藏書|朝鮮國王|韓賜|經筵"),
    ("Keichō copy/print", r"慶長寫本|慶長官刻|慶長活字|慶長.*寫"),
    ("Kanazawa Bunko copy", r"金澤文庫|金澤"),
    ("Movable type (JP)", r"活字"),
    ("Manuscript (other)", r"寫本|寫"),
]

ROUTE_RULES = {
    "gift": r"獻|寄進|賜",
    "purchase": r"購|買",
    "copy_made": r"寫|摹",
    "war_or_campaign": r"征伐|役|載セ歸",
    "transfer_to_library": r"收|移|遷|轉",
    "bequest": r"遺物|遺命",
}

HEDGE_RE = re.compile(r"蓋|恐|ナルヘシ|ナルヤ|ナルモ|知ルヘカラス|詳ニ|明據|或ハ|ナルニヤ")

SECTIONS = ["番外部", "經部", "史部", "子部", "集部", "國書部", "御家類", "附存部"]

ERA_START = {  # first year of each era (元年)
    "文應": 1260, "文永": 1264, "建長": 1249, "弘安": 1278, "正安": 1299, "嘉元": 1303,
    "永享": 1429, "永正": 1504, "天文": 1532,
    "文祿": 1592, "文禄": 1592, "慶長": 1596, "元和": 1615, "寬永": 1624,
    "正保": 1644, "慶安": 1648, "承應": 1652, "明曆": 1655, "萬治": 1658,
    "寬文": 1661, "延寶": 1673, "天和": 1681, "貞享": 1684, "元祿": 1688,
    "寶永": 1704, "正德": 1711, "享保": 1716, "元文": 1736, "寬保": 1741,
    "延享": 1744, "寬延": 1748, "寶曆": 1751, "明和": 1764, "安永": 1772,
    "天明": 1781, "寬政": 1789, "享和": 1801, "文化": 1804, "文政": 1818,
    "天保": 1830, "弘化": 1844, "嘉永": 1848, "安政": 1854, "萬延": 1860, "文久": 1861,
}
ERA_RE = re.compile(
    "(" + "|".join(sorted(ERA_START, key=len, reverse=True)) + r")"
    r"((?:廿|十|元|[一二三四五六七八九])+)年"
)
HONORIFIC_RE = re.compile(r"[／/]?[（(][双単三]擡[）)]")


# ---------------------------------------------------------------------------
# 1. Load
# ---------------------------------------------------------------------------
def parse_record_blocks(text: str) -> pd.DataFrame:
    """Parse 'Key: value' blocks. Lines that don't start with a known key
    are treated as continuations of the previous field."""
    records, current, field = [], None, None
    for raw in text.splitlines():
        line = raw.rstrip()
        if line.strip() in {"---", "```", "```md"} or line.startswith("# "):
            continue
        m = KEY_RE.match(line)
        if m:
            key, value = m.group(1), m.group(2).strip()
            if key == "Record_ID":
                if current is not None:
                    records.append(current)
                current = {}
            if current is None:  # text before the first record
                continue
            current[key] = value
            field = key
        elif current is not None and field and line.strip():
            current[field] = (current.get(field, "") + "\n" + line.strip()).strip()
    if current is not None:
        records.append(current)
    return pd.DataFrame(records)


def load(path: Path) -> pd.DataFrame:
    if path.suffix.lower() == ".csv":
        return pd.read_csv(path, dtype=str, encoding="utf-8-sig")
    return parse_record_blocks(path.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# 2. Text helpers
# ---------------------------------------------------------------------------
def clean_text(s):
    """Remove honorific line-break markers (／（双擡） etc.) and normalise spaces."""
    if not isinstance(s, str):
        return None
    s = HONORIFIC_RE.sub("", s).replace("\u3000", " ")
    s = re.sub(r"[ \t]+", " ", s)
    s = re.sub(r"\n\s*\n", "\n", s)
    return s.strip() or None


def first_match(text: str, rules, default):
    for label, pattern in rules:
        if re.search(pattern, text):
            return label
    return default


def classify_record(t):
    if not isinstance(t, str):
        return "unknown"
    if "始末記" in t:
        return "admin_log"          # acquisition/administration log, not a book
    if "來歷志" in t:
        return "provenance_record"  # provenance note on a book
    if "主目錄" in t or "彙刻書目" in t:
        return "catalogue_entry"    # plain catalogue entry
    return "other"


def classify_section(t):
    if not isinstance(t, str):
        return "unspecified"
    return next((s for s in SECTIONS if s in t), "unspecified")


def kanji_to_int(s: str):
    """Convert 元, 一…九, 十, 十二, 二十三, 廿一 to int."""
    if s == "元":
        return 1
    digits = {"一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9}
    if s.startswith("廿"):
        return 20 + digits.get(s[1:], 0)
    if "十" in s:
        a, _, b = s.partition("十")
        return (digits.get(a, 1) if a else 1) * 10 + digits.get(b, 0)
    return digits.get(s)


def first_era_year(text: str):
    """Return (era, year) for the first era-year date in the text, else (None, None).
    Parenthetical alternatives like 慶長十八（九）年 are removed first."""
    if not text:
        return None, None
    t = re.sub(r"（[^）]*）|〈[^〉]*〉", "", text)
    m = ERA_RE.search(t)
    if not m:
        return None, None
    era, num = m.group(1), kanji_to_int(m.group(2))
    if num is None:
        return None, None
    return era, ERA_START[era] + num - 1


# ---------------------------------------------------------------------------
# 3. Main pipeline
# ---------------------------------------------------------------------------
def main():
    raw = load(RAW_PATH)
    qa = [f"Raw rows parsed: {len(raw)}"]

    df = raw.copy()
    for col in df.columns:
        df[col] = df[col].map(clean_text)

    df["Record_ID"] = pd.to_numeric(df["Record_ID"], errors="coerce").astype("Int64")
    df["Fascicle_Count"] = pd.to_numeric(df["Fascicle_Count"], errors="coerce").astype("Int64")
    n_missing_id = df["Record_ID"].isna().sum()
    if n_missing_id:
        qa.append(f"Rows without Record_ID (dropped): {n_missing_id}")
        df = df.dropna(subset=["Record_ID"])

    # Keep every search term a record was hit by, before de-duplicating.
    hits = df.groupby("Record_ID")["Search_Term_Hit"].agg(
        lambda s: "|".join(sorted(set(s.dropna())))
    )
    dup_ids = sorted(df.loc[df.duplicated("Record_ID", keep=False), "Record_ID"].unique())
    qa.append(f"Duplicate Record_IDs (kept first occurrence): {[int(i) for i in dup_ids]}")
    df = df.drop_duplicates("Record_ID", keep="first").copy()
    df["Search_Term_Hit"] = df["Record_ID"].map(hits)
    qa.append(f"Unique records: {len(df)}")

    # Classification
    df["record_class"] = df["Type_Category"].map(classify_record)
    df["section"] = df["Type_Category"].map(classify_section)
    df["is_book"] = df["record_class"].ne("admin_log")

    text_edition = df[["Title_and_Author", "Volume_Info",
                       "Exact_Provenance_Language_JP", "Remarks_Notes"]] \
        .fillna("").agg(" ".join, axis=1)
    text_route = df[["Volume_Info", "Exact_Provenance_Language_JP"]] \
        .fillna("").agg(" ".join, axis=1)

    df["edition_origin"] = text_edition.map(lambda t: first_match(t, EDITION_RULES, "unspecified"))
    df["route_types"] = text_route.map(
        lambda t: "|".join(k for k, pat in ROUTE_RULES.items() if re.search(pat, t)) or None
    )
    df["hedged"] = text_route.map(lambda t: bool(HEDGE_RE.search(t)))

    era_text = df[["Title_and_Author", "Volume_Info", "Exact_Provenance_Language_JP"]] \
        .fillna("").agg(" ".join, axis=1)
    era_pairs = era_text.map(first_era_year)
    era_df = pd.DataFrame(era_pairs.tolist(), index=df.index, columns=["era", "era_year"])
    df["era"] = era_df["era"]
    df["era_year"] = pd.to_numeric(era_df["era_year"]).astype("Int64")

    keep_cols = [
        "Record_ID", "Title_and_Author", "Volume_Info", "Type_Category", "record_class",
        "section", "is_book", "edition_origin", "route_types", "hedged", "era", "era_year",
        "Fascicle_Count", "Keywords_Present", "Search_Term_Hit", "Exact_Provenance_Language_JP",
        "Remarks_Notes", "Literal_English_Translation", "Summary",
    ]
    df = df[[c for c in keep_cols if c in df.columns]]
    books = df[df["is_book"]].copy()

    # Outputs
    df.to_csv(OUT_DIR / "records_clean.csv", index=False, encoding="utf-8-sig")
    books.to_csv(OUT_DIR / "books_clean.csv", index=False, encoding="utf-8-sig")

    # QA report
    qa.append("\nRecord class:\n" + df["record_class"].value_counts().to_string())
    qa.append("\nBook records by edition origin:\n" + books["edition_origin"].value_counts().to_string())
    qa.append("\nBook records by section:\n" + books["section"].value_counts().to_string())
    qa.append(f"\nBook records with an era year: {books['era_year'].notna().sum()} / {len(books)}")
    qa.append(f"Hedged provenance claims (蓋/恐/ナルヘシ etc.): {books['hedged'].sum()}")
    qa.append("\nBooks with no Title (check manually):\n"
              + books.loc[books["Title_and_Author"].isna(), "Record_ID"].to_string(index=False))
    report = "\n".join(qa)
    (OUT_DIR / "qa_report.txt").write_text(report, encoding="utf-8")
    print(report)
    print(f"\nWrote {OUT_DIR/'records_clean.csv'} and {OUT_DIR/'books_clean.csv'}")


if __name__ == "__main__":
    main()
