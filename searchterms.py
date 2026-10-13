"""
Search terms for tracking text movement in Momijiyama Bunko
Organized by category with priority rankings
"""

# ============================================================================
# PRIORITY LIST: Wiebke's Original Search Terms
# ============================================================================
WIEBKE_PRIORITY = [
    "朝鮮",        # Korean (general)
    "朝鮮刊",      # Korean-printed
    "朝鮮本",      # Korean edition
    "明刊",        # Ming-printed
    "明版",        # Ming edition
    "進上",        # presented to (shogun)
    "献上",        # offered as tribute
    "御分与",      # official distribution
    "御譲",        # official transfer
    "駿河御譲本",  # Suruga transfer texts
    "元和御譲本",  # Genwa era transfer texts
    "家康",        # Tokugawa Ieyasu
    "御本",        # imperial/shogunal copy
]

# ============================================================================
# GIVING / PRESENTING
# ============================================================================
GIVING_PRESENTING = [
    "進上",        # presented to (esp. to shogun)
    "献上",        # offered up, presented as tribute
    "献",          # offer, present, donate
    "賜",          # grant, bestow (downward giving)
    "給",          # give, provide
    "贈",          # gift, present
    "奉献",        # consecrate, dedicate
    "捐献",        # donate
    "奉呈",        # present respectfully
    "寄進",        # donate to temple/shrine
]

# ============================================================================
# RECEIVING / ACQUIRING
# ============================================================================
RECEIVING_ACQUIRING = [
    "受取",        # receive
    "所持",        # possession, ownership
    "購入",        # purchase
    "請求",        # request, order
    "蒙",          # receive (honorific)
    "得",          # obtain, get
    "納",          # deliver, present
    "収",          # collect, gather
    "入手",        # acquire
]

# ============================================================================
# TRANSFER / TRANSMISSION
# ============================================================================
TRANSFER_TRANSMISSION = [
    "御譲",        # official transfer/giving (esp. Tokugawa)
    "御分与",      # official distribution
    "譲",          # transfer, hand over
    "分与",        # distribute, portion out
    "相続",        # inherit, succession
    "移譲",        # transfer of authority
    "伝来",        # transmission, provenance
    "来歴",        # history, provenance
    "源流",        # origin, source
    "由来",        # origin, reason
]

# ============================================================================
# PRINTING / EDITION TYPES
# ============================================================================
PRINTING_EDITIONS = [
    # General printing terms
    "刊",          # print, publish
    "版",          # edition, woodblock
    "刻",          # engrave, carve
    "印",          # print, stamp
    "刻本",        # block-printed edition
    "版本",        # edition (bibliographic)
    "初版",        # first edition
    "重刻",        # recarving, recut edition
    "翻刻",        # reproduction edition
    "影刻",        # facsimile edition
    "写刻",        # manuscript-based woodblock

    # Printing by institution
    "官刻",        # official printing
    "坊刻",        # commercial/shop printing
    "私刻",        # private printing

    # Regional origins
    "朝鮮刊",      # Korean-printed
    "朝鮮本",      # Korean edition
    "朝鮮",        # Korean (general)
    "明刊",        # Ming-printed
    "明版",        # Ming edition
    "明",          # Ming (general)
    "宋刊",        # Song-printed
    "宋版",        # Song edition
    "宋",          # Song (general)
    "元刊",        # Yuan-printed
    "元版",        # Yuan edition
    "元",          # Yuan (general)
    "唐",          # Tang (general)
]

# ============================================================================
# OWNERSHIP / INSCRIPTION MARKS
# ============================================================================
OWNERSHIP_MARKS = [
    "蔵書印",      # ownership seal
    "蔵印",        # collection seal
    "御本",        # imperial/shogunal copy
    "家康",        # Tokugawa Ieyasu (specific owner)
    "旧蔵",        # formerly owned
    "蔵",          # collection, treasure
    "本",          # copy (as in "this copy")
    "印",          # seal, stamp
    "署",          # signature, inscription
    "箱題",        # box inscription
    "題鼎",        # dedication inscription
    "貼紙",        # owner's label
    "識語",        # colophon, inscription
]

# ============================================================================
# SPECIFIC TOKUGAWA PROVENANCE
# ============================================================================
TOKUGAWA_PROVENANCE = [
    "駿河御譲本",  # texts transferred from Suruga (Ieyasu's first province)
    "元和御譲本",  # texts transferred in Genwa era (1615-1624)
    "駿河",        # Suruga (Ieyasu's domain)
    "元和",        # Genwa era (1615-1624, post-Summer Campaign of Osaka)
    "寛永",        # Kanei era (1624-1644, early Tokugawa peace)
    "家康蔵",      # from Ieyasu's collection
    "家康",        # Tokugawa Ieyasu
    "将軍",        # shogun (general)
    "本丸",        # Edo Castle main citadel
]

# ============================================================================
# ORDER / COMMAND TERMS
# ============================================================================
ORDERS_COMMANDS = [
    "命",          # order, command, mandate
    "依命",        # by order/mandate
    "詔",          # imperial edict
    "勅",          # imperial command
    "指図",        # instruction, directive
    "指示",        # direction, instruction
    "令",          # order, decree
]

# ============================================================================
# CIRCULATION / MOVEMENT
# ============================================================================
CIRCULATION = [
    "流布",        # circulation, dissemination
    "行本",        # circulating edition
    "通行本",      # common/widely circulated edition
    "所蔵",        # holding, possession
    "保有",        # keep, retain
    "逸失",        # lost, missing
    "散逸",        # scattered, dispersed
    "散亡",        # lost and scattered
    "流出",        # outflow, dispersal
]

# ============================================================================
# MASTER DICTIONARY
# ============================================================================
SEARCH_TERM_CATEGORIES = {
    "PRIORITY": WIEBKE_PRIORITY,
    "GIVING_PRESENTING": GIVING_PRESENTING,
    "RECEIVING_ACQUIRING": RECEIVING_ACQUIRING,
    "TRANSFER_TRANSMISSION": TRANSFER_TRANSMISSION,
    "PRINTING_EDITIONS": PRINTING_EDITIONS,
    "OWNERSHIP_MARKS": OWNERSHIP_MARKS,
    "TOKUGAWA_PROVENANCE": TOKUGAWA_PROVENANCE,
    "ORDERS_COMMANDS": ORDERS_COMMANDS,
    "CIRCULATION": CIRCULATION,
}

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_all_terms():
    """Return flat list of all search terms (excluding duplicates)"""
    all_terms = set()
    for category, terms in SEARCH_TERM_CATEGORIES.items():
        all_terms.update(terms)
    return sorted(list(all_terms))

def get_category_for_term(term):
    """Return which category(ies) a term belongs to"""
    categories = []
    for category, terms in SEARCH_TERM_CATEGORIES.items():
        if term in terms:
            categories.append(category)
    return categories

def get_priority_rank(term):
    """Return priority rank if term is in WIEBKE_PRIORITY, else None"""
    try:
        return WIEBKE_PRIORITY.index(term) + 1
    except ValueError:
        return None

# ============================================================================
# DISPLAY / DEBUGGING
# ============================================================================

def print_summary():
    """Print summary of all search terms"""
    all_terms = get_all_terms()
    print("="*70)
    print("SEARCH TERM SUMMARY")
    print("="*70)
    print(f"Total unique terms: {len(all_terms)}\n")

    for category, terms in SEARCH_TERM_CATEGORIES.items():
        print(f"{category}: {len(terms)} terms")
        if category == "PRIORITY":
            print(f"  {' | '.join(terms)}")
        else:
            # Show first 5, then ellipsis if more
            display = terms[:5]
            if len(terms) > 5:
                print(f"  {' | '.join(display)} | ...")
            else:
                print(f"  {' | '.join(display)}")
        print()

if __name__ == "__main__":
    print_summary()
