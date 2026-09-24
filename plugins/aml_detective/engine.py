from __future__ import annotations

import difflib
import hashlib
import random
import re
from datetime import date, datetime, timedelta, timezone

WINDOW_DAYS = 30

HIGH_RISK_COUNTRIES = {"KP": "North Korea", "IR": "Iran", "MM": "Myanmar"}

COUNTRY_NAMES = {
    "US": "United States", "CA": "Canada", "MX": "Mexico", "GB": "United Kingdom",
    "DE": "Germany", "CY": "Cyprus", "HK": "Hong Kong", "LV": "Latvia",
    "RU": "Russia", "BY": "Belarus", **HIGH_RISK_COUNTRIES,
}

# Fictional sanctions list
WATCHLIST = [
    {"name": "Dmitri Volkanov", "dob": "1971-03-14", "nationality": "RU",
     "program": "Fictional list: arms procurement network"},
    {"name": "Hassan Qaderi", "dob": "1968-11-02", "nationality": "IR",
     "program": "Fictional list: sanctions evasion facilitator"},
    {"name": "Arkady Belenko", "dob": "1980-07-21", "nationality": "BY",
     "program": "Fictional list: state-linked procurement"},
    {"name": "Golden Lotus Trading Co", "dob": None, "nationality": "HK",
     "program": "Fictional list: front company"},
]

TYPOLOGIES = {
    "structuring": "Structuring",
    "funnel_account": "Funnel account",
    "rapid_movement": "Rapid movement of funds",
    "high_risk_jurisdiction": "High-risk jurisdiction",
    "sanctions_match": "Sanctions match",
}

RULES = {
    "R01": {"name": "Cash deposits just under $10,000", "weight": 35},
    "R02": {"name": "Many unrelated senders", "weight": 30},
    "R03": {"name": "Funds in and out within 48 hours", "weight": 30},
    "R04": {"name": "Wire to or from a high-risk jurisdiction", "weight": 35},
    "R05": {"name": "Watchlist name match", "weight": 50},
    "R06": {"name": "Activity far above KYC profile", "weight": 15},
}

WATCHLIST_THRESHOLD = 0.88

FIRST = ["Maya", "Jordan", "Priya", "Luis", "Grace", "Omar", "Elena", "Marcus", "Aiko",
         "Tomas", "Nadia", "Caleb", "Sofia", "Andre", "Hannah", "Ravi", "Chloe", "Diego",
         "Imani", "Felix", "Leah", "Kwame", "Rosa", "Ethan", "Mei", "Samuel", "Zara", "Owen"]
LAST = ["Alvarez", "Brennan", "Chowdhury", "Delgado", "Okafor", "Fischer", "Gallagher",
        "Hartley", "Ibarra", "Jansen", "Kowalski", "Lindqvist", "Moreau", "Nakamura",
        "Ortega", "Pereira", "Quinlan", "Ramirez", "Sato", "Thornton", "Underwood",
        "Vasquez", "Whitaker", "Yilmaz", "Zimmerman", "Abernathy", "Castellano"]
BIZ_A = ["Harbor", "Summit", "Juniper", "Ironwood", "Bluefield", "Cedar", "Keystone",
         "Northgate", "Redline", "Silverleaf", "Tidewater", "Granite"]
BIZ_B = ["Advisory", "Logistics", "Holdings", "Partners", "Supply", "Ventures",
         "Consulting", "Trading", "Imports", "Group"]
US_CITIES = ["Phoenix AZ", "Tulsa OK", "Reno NV", "Dayton OH", "Boise ID", "El Paso TX",
             "Fresno CA", "Omaha NE", "Tampa FL", "Albany NY", "Spokane WA", "Macon GA"]



# Stage 1: synthetic activity

class _Builder:
    def __init__(self, seed: str, as_of: date):
        digest = hashlib.sha256(seed.encode()).hexdigest()
        self.rng = random.Random(int(digest[:16], 16))
        self.as_of = as_of
        self.start = as_of - timedelta(days=WINDOW_DAYS - 1)
        self.accounts: dict[str, dict] = {}
        self.counterparties: dict[str, dict] = {}
        self.transactions: list[dict] = []
        self.planted: dict[str, dict] = {}
        self._n_acct = 0
        self._n_cp = 0
        self._n_txn = 0
        self._used_names: set[str] = set()

    # ids and names 
    def person_name(self) -> str:
        for _ in range(200):
            name = f"{self.rng.choice(FIRST)} {self.rng.choice(LAST)}"
            if name not in self._used_names:
                self._used_names.add(name)
                return name
        return f"{self.rng.choice(FIRST)} {self.rng.choice(LAST)} {self._n_cp}"

    def business_name(self, suffix: str = "LLC") -> str:
        for _ in range(200):
            name = f"{self.rng.choice(BIZ_A)} {self.rng.choice(BIZ_B)} {suffix}"
            if name not in self._used_names:
                self._used_names.add(name)
                return name
        return f"{self.rng.choice(BIZ_A)} {self.rng.choice(BIZ_B)} {self._n_cp} {suffix}"

    def day(self, offset: int) -> str:
        offset = max(0, min(WINDOW_DAYS - 1, offset))
        return (self.start + timedelta(days=offset)).isoformat()

    # entities 
    def account(self, kind: str, occupation: str, expected: int, notes: str,
                name: str | None = None, opened_years_ago: int | None = None) -> str:
        self._n_acct += 1
        acct_id = f"ACC-{self._n_acct:05d}"
        years = opened_years_ago if opened_years_ago is not None else self.rng.randint(1, 12)
        self.accounts[acct_id] = {
            "id": acct_id,
            "name": name or (self.person_name() if kind == "individual" else self.business_name()),
            "kind": kind,
            "occupation": occupation,
            "expected_monthly": expected,
            "opened": (self.as_of - timedelta(days=365 * years + self.rng.randint(0, 300))).isoformat(),
            "kyc_notes": notes,
        }
        return acct_id

    def cp(self, name: str, country: str = "US", kind: str = "individual",
           dob: str | None = None, nationality: str | None = None, note: str | None = None) -> str:
        self._n_cp += 1
        cp_id = f"CP-{self._n_cp:05d}"
        self.counterparties[cp_id] = {
            "id": cp_id, "name": name, "country": country,
            "country_name": COUNTRY_NAMES.get(country, country), "kind": kind,
            "dob": dob, "nationality": nationality, "note": note,
        }
        return cp_id

    def txn(self, acct: str, day: int, direction: str, channel: str, amount: float,
            cp: str | None = None, memo: str = "") -> str:
        self._n_txn += 1
        txn_id = f"TXN-{self._n_txn:06d}"
        self.transactions.append({
            "id": txn_id, "account_id": acct, "date": self.day(day), "direction": direction,
            "channel": channel, "amount": round(float(amount), 2), "counterparty_id": cp,
            "memo": memo,
        })
        return txn_id

    # ordinary activity 
    def background(self, acct: str, expected: int) -> None:
        a = self.accounts[acct]
        r = self.rng
        if a["kind"] == "individual":
            employer = self.cp(self.business_name("Inc"), kind="business")
            landlord = self.cp(self.person_name())
            pay = round(expected * r.uniform(0.40, 0.48), 2)
            first_payday = r.randint(0, 5)
            for d in range(first_payday, WINDOW_DAYS, 14):
                self.txn(acct, d, "in", "ach", pay, employer, "Payroll")
            self.txn(acct, r.randint(0, 4), "out", "ach", round(expected * r.uniform(0.25, 0.35), 2),
                     landlord, "Rent")
            for _ in range(r.randint(4, 8)):
                self.txn(acct, r.randint(0, WINDOW_DAYS - 1), "out", "card",
                         round(r.uniform(15, min(400, expected * 0.08)), 2), None,
                         r.choice(["Grocery", "Fuel", "Pharmacy", "Restaurant", "Utilities", "Online retail"]))
            if r.random() < 0.3:
                self.txn(acct, r.randint(0, WINDOW_DAYS - 1), "in", "cash",
                         round(r.uniform(100, 1500), 2), None, "Branch deposit")
        else:
            customers = [self.cp(self.business_name("Inc"), kind="business") for _ in range(r.randint(2, 4))]
            supplier = self.cp(self.business_name("Co"), kind="business")
            per_customer = expected * r.uniform(0.6, 0.8) / len(customers)
            for c in customers:
                self.txn(acct, r.randint(0, WINDOW_DAYS - 1), "in", "ach",
                         round(per_customer * r.uniform(0.8, 1.2), 2), c, "Invoice payment")
            self.txn(acct, r.randint(0, WINDOW_DAYS - 1), "out", "ach",
                     round(expected * r.uniform(0.25, 0.35), 2), supplier, "Supplier payment")
            for d in (r.randint(0, 3), r.randint(14, 17)):
                self.txn(acct, d, "out", "ach", round(expected * r.uniform(0.1, 0.15), 2), None, "Payroll run")


# Scenario generators

def _plant(b: _Builder, acct: str, disposition: str, typology: str | None,
           scenario: str, debrief: str) -> None:
    b.planted[acct] = {"disposition": disposition, "typology": typology,
                       "scenario": scenario, "debrief": debrief}


def _structuring(b: _Builder) -> None:
    r = b.rng
    expected = r.choice([3500, 4000, 4500])
    acct = b.account("individual", r.choice(["Rideshare driver", "Retail associate", "Line cook"]),
                     expected, "Paid by direct deposit. No cash-intensive business declared.")
    b.background(acct, expected)
    n = r.randint(4, 6)
    start = r.randint(2, 14)
    days = sorted(r.sample(range(start, start + 9), n))
    total = 0.0
    for d in days:
        amt = r.randrange(8200, 9901, 50)
        total += amt
        b.txn(acct, d, "in", "cash", amt, None, f"Branch deposit, {r.choice(US_CITIES)}")
    dest = b.cp(b.business_name(), kind="business")
    b.txn(acct, days[-1] + r.randint(1, 3), "out", "wire", round(total * r.uniform(0.9, 0.97), -2),
          dest, "Purchase")
    _plant(b, acct, "sar", "structuring", "structuring",
           f"{n} cash deposits between $8,200 and $9,900 in under ten days, every one just below the "
           f"$10,000 Currency Transaction Report threshold, then wired out almost in full. Nothing in the "
           f"profile of a salaried {b.accounts[acct]['occupation'].lower()} explains that much cash.")


def _funnel(b: _Builder) -> None:
    r = b.rng
    expected = r.choice([1500, 1800, 2000])
    acct = b.account("individual", "Graduate student", expected,
                     "Student account. Part-time campus job, paid monthly.", opened_years_ago=1)
    b.background(acct, expected)
    senders = r.randint(8, 11)
    start = r.randint(2, 12)
    total = 0.0
    for _ in range(senders):
        cp = b.cp(b.person_name(), note=f"Sent from {r.choice(US_CITIES)}")
        amt = round(r.uniform(700, 2900), 2)
        total += amt
        b.txn(acct, start + r.randint(0, 10), "in", "p2p", amt, cp, r.choice(["", "rent", "thx", "for the thing", "💸"]))
    for k in range(r.randint(3, 5)):
        b.txn(acct, start + 3 + k * 2, "out", "cash", round(r.uniform(800, 1000), -1), None, "ATM withdrawal")
    dest = b.cp(b.person_name(), country="MX")
    b.txn(acct, start + 12, "out", "wire", round(total * 0.55, -2), dest, "Family")
    _plant(b, acct, "sar", "funnel_account", "funnel",
           f"{senders} unrelated people in different states paid a student account within two weeks, and "
           f"the money left almost immediately as ATM cash and a cross-border wire. A student with a campus "
           f"job has no reason to collect money from strangers nationwide. This is a funnel account.")


def _rapid(b: _Builder) -> None:
    r = b.rng
    expected = r.choice([20000, 25000, 30000])
    name = b.business_name("LLC").replace("Holdings", "Advisory")
    acct = b.account("business", "Management consulting", expected,
                     "Declared clients are domestic mid-size firms. No foreign operations declared.", name=name)
    b.background(acct, expected)
    origin = b.cp(b.business_name("Ltd"), country=r.choice(["CY", "LV"]), kind="business")
    onward = b.cp(b.business_name("Ltd"), country="HK", kind="business")
    cycles = r.randint(2, 3)
    for k in range(cycles):
        d = 4 + k * 8 + r.randint(0, 2)
        amt = round(r.uniform(60000, 180000), -3)
        b.txn(acct, d, "in", "wire", amt, origin, f"Invoice {r.randint(2000, 2999)}")
        b.txn(acct, d + r.randint(0, 1), "out", "wire", round(amt * r.uniform(0.96, 0.99), 2), onward, "Services")
    _plant(b, acct, "sar", "rapid_movement", "rapid_movement",
           f"{cycles} large wires arrived from an offshore company and 96 to 99 percent of each left within "
           f"a day for Hong Kong. A domestic consultancy is being used as a pass-through to add a layer "
           f"between origin and destination, which is textbook layering.")


def _high_risk(b: _Builder) -> None:
    r = b.rng
    expected = r.choice([12000, 15000, 18000])
    acct = b.account("individual", "Dentist, private practice owner", expected,
                     "No declared foreign business ties or family abroad.")
    b.background(acct, expected)
    country = r.choice(["MM", "IR"])
    dest = b.cp(b.business_name("Co"), country=country, kind="business")
    for k in range(r.randint(2, 4)):
        b.txn(acct, 3 + k * 7 + r.randint(0, 2), "out", "wire", round(r.uniform(9000, 24000), -2),
              dest, r.choice(["Consulting fee", "Equipment", "Services"]))
    _plant(b, acct, "sar", "high_risk_jurisdiction", "high_risk",
           f"Repeated wires to a company in {HIGH_RISK_COUNTRIES[country]}, a FATF call-for-action "
           f"jurisdiction, with vague memos. The KYC profile declares no foreign business or family, so "
           f"there is no reason on file for these payments.")


def _sanctions(b: _Builder) -> None:
    r = b.rng
    entry = r.choice([w for w in WATCHLIST if w["dob"]])
    variants = {"Dmitri Volkanov": "Dmitry Volkanov", "Hassan Qaderi": "Hasan Qaderi",
                "Arkady Belenko": "Arkadiy Belenko"}
    expected = r.choice([8000, 10000])
    acct = b.account("business", "Industrial parts distributor", expected,
                     "Buys machine parts from domestic and European suppliers.")
    b.background(acct, expected)
    cp = b.cp(variants.get(entry["name"], entry["name"]), country="DE", kind="individual",
              dob=entry["dob"], nationality=entry["nationality"])
    for k in range(r.randint(1, 2)):
        b.txn(acct, 6 + k * 9, "out", "wire", round(r.uniform(15000, 45000), -2), cp, "Parts brokerage")
    _plant(b, acct, "sar", "sanctions_match", "sanctions",
           f"The beneficiary is a spelling variant of {entry['name']}, and the date of birth and "
           f"nationality both match the list entry exactly. Three matching identifiers is a true hit. In "
           f"practice you would block the payment and file a blocked-property report with OFAC within "
           f"10 business days, alongside the SAR.")


def _seasonal_fp(b: _Builder) -> None:
    r = b.rng
    expected = r.choice([25000, 30000])
    acct = b.account("business", "Seasonal holiday decor retailer", expected,
                     "Peak season is underway. Prior-year statements on file show sales at 4 to 5 times "
                     "the monthly average during this period.", name=b.business_name("Inc").replace("Advisory", "Home"))
    processor = b.cp("Keystone Card Services", kind="business")
    wholesaler = b.cp(b.business_name("Wholesale"), kind="business")
    total = 0.0
    for d in range(0, WINDOW_DAYS, 2):
        amt = round(expected * r.uniform(0.2, 0.28), 2)
        total += amt
        b.txn(acct, d, "in", "ach", amt, processor, "Card settlement")
    for d in (5, 15, 25):
        b.txn(acct, d, "out", "ach", round(total * 0.2, 2), wholesaler, "Inventory")
    for d in (1, 15):
        b.txn(acct, d, "out", "ach", round(expected * 0.4, 2), None, "Payroll run")
    _plant(b, acct, "close", None, "seasonal_false_positive",
           "Volume is far above the monthly average, which is why the rule fired. But the money arrives "
           "as card settlements from one processor and leaves as inventory and payroll. The KYC file "
           "documents this exact seasonal surge in prior years. Close with a note.")


def _name_fp(b: _Builder) -> None:
    r = b.rng
    expected = r.choice([4000, 5000])
    acct = b.account("individual", "Retired schoolteacher", expected,
                     "Pension and Social Security income. Renting since 2021.")
    pension = b.cp("State Teachers Retirement System", kind="business")
    for d in (1, 15):
        b.txn(acct, d, "in", "ach", round(expected * 0.45, 2), pension, "Pension")
    entry = next(w for w in WATCHLIST if w["name"] == "Hassan Qaderi")
    landlord = b.cp("Hassan Qadeer", country="US", dob="1994-05-09", nationality="US",
                    note="Payee on this account every month since 2021")
    b.txn(acct, r.randint(0, 3), "out", "ach", round(expected * 0.35, 2), landlord, "Rent")
    for _ in range(r.randint(4, 7)):
        b.txn(acct, r.randint(0, WINDOW_DAYS - 1), "out", "card", round(r.uniform(20, 180), 2), None,
              r.choice(["Grocery", "Pharmacy", "Utilities", "Bookstore"]))
    _plant(b, acct, "close", None, "name_false_positive",
           f"The landlord's name is close to {entry['name']} on the list, but the date of birth "
           f"(1994 vs {entry['dob'][:4]}) and nationality (US vs {entry['nationality']}) don't match, and "
           f"the payments are routine domestic rent going back years. A name alone is not a hit. Close.")


def _escrow_fp(b: _Builder) -> None:
    r = b.rng
    expected = 400000
    acct = b.account("business", "Licensed title and escrow agent", expected,
                     "Receives buyer funds and disburses to sellers and lenders at closing. State "
                     "license verified.", name=f"{r.choice(BIZ_A)} Title & Escrow LLC")
    for k in range(r.randint(2, 3)):
        d = 3 + k * 9 + r.randint(0, 2)
        buyer = b.cp(b.person_name())
        seller = b.cp(b.person_name())
        street = f"{r.randint(10, 999)} {r.choice(['Oak Ridge', 'Maple', 'Lakeview', 'Cypress'])} Rd"
        amt = round(r.uniform(280000, 620000), -2)
        b.txn(acct, d, "in", "wire", amt, buyer, f"Escrow deposit, {street}")
        b.txn(acct, d + 1, "out", "wire", round(amt * 0.94, 2), seller, f"Closing proceeds, {street}")
        b.txn(acct, d + 1, "out", "ach", round(amt * 0.03, 2), None, f"Commissions and fees, {street}")
    _plant(b, acct, "close", None, "escrow_false_positive",
           "Money in and straight back out looks like layering, but this is an escrow agent. Every wire "
           "names a property, buyers and sellers are different people, and fees are withheld. Pass-through "
           "is the whole business model here. Close.")


SCENARIOS = [_structuring, _funnel, _rapid, _high_risk, _sanctions, _seasonal_fp, _name_fp, _escrow_fp]


def generate_activity(seed: str, as_of: date | None = None, n_background: int = 40) -> dict:
    as_of = as_of or datetime.now(timezone.utc).date()
    b = _Builder(seed, as_of)
    scenarios = SCENARIOS[:]
    b.rng.shuffle(scenarios)
    plan: list = scenarios + [None] * n_background
    b.rng.shuffle(plan)
    for item in plan:
        if item is None:
            kind = "individual" if b.rng.random() < 0.7 else "business"
            expected = b.rng.choice([3000, 4500, 6000, 8000]) if kind == "individual" else b.rng.choice([20000, 40000, 60000])
            occupation = b.rng.choice(["Nurse", "Teacher", "Electrician", "Accountant", "Designer"]) \
                if kind == "individual" else b.rng.choice(["Landscaping", "Bakery", "IT services", "Auto repair"])
            acct = b.account(kind, occupation, expected, "Standard retail profile.")
            b.background(acct, expected)
        else:
            item(b)
    b.transactions.sort(key=lambda t: (t["date"], t["id"]))
    return {
        "seed": seed,
        "as_of": as_of.isoformat(),
        "window_start": b.start.isoformat(),
        "accounts": b.accounts,
        "counterparties": b.counterparties,
        "transactions": b.transactions,
        "planted": b.planted,
    }


# Stage 2: rules engine

def _norm(name: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z ]", "", name.lower())).strip()


def name_similarity(a: str, b: str) -> float:
    return difflib.SequenceMatcher(None, _norm(a), _norm(b)).ratio()


def _d(s: str) -> date:
    return date.fromisoformat(s)


def _money(x: float) -> str:
    return f"${x:,.0f}"


def _rule_hits(acct: dict, txns: list[dict], cps: dict) -> list[dict]:
    hits = []

    # R01 cash deposits $8,000-$9,999, 3+ inside any 10-day window
    cash = [t for t in txns if t["channel"] == "cash" and t["direction"] == "in" and 8000 <= t["amount"] < 10000]
    best: list[dict] = []
    for i, t in enumerate(cash):
        win = [u for u in cash[i:] if (_d(u["date"]) - _d(t["date"])).days <= 9]
        if len(win) > len(best):
            best = win
    if len(best) >= 3:
        hits.append({"code": "R01", "detail": f"{len(best)} cash deposits of $8,000 to $9,999 within 10 days, "
                     f"{_money(sum(t['amount'] for t in best))} in total.", "txn_ids": [t["id"] for t in best]})

    # R02 six or more distinct senders inside any 14-day window
    inbound = [t for t in txns if t["direction"] == "in" and t["counterparty_id"]]
    best = []
    for i, t in enumerate(inbound):
        win = [u for u in inbound[i:] if (_d(u["date"]) - _d(t["date"])).days <= 13]
        if len({u["counterparty_id"] for u in win}) > len({u["counterparty_id"] for u in best}):
            best = win
    senders = {t["counterparty_id"] for t in best}
    if len(senders) >= 6:
        hits.append({"code": "R02", "detail": f"{len(senders)} different senders within 14 days.",
                     "txn_ids": [t["id"] for t in best]})

    # R03 inbound >= $25k matched by an outbound >= 90% of it within 48h
    pairs = []
    outs = [t for t in txns if t["direction"] == "out"]
    for t in (t for t in txns if t["direction"] == "in" and t["amount"] >= 25000):
        for o in outs:
            gap = (_d(o["date"]) - _d(t["date"])).days
            if 0 <= gap <= 2 and o["amount"] >= 0.9 * t["amount"]:
                pairs.append((t, o))
                break
    if pairs:
        moved = sum(o["amount"] for _, o in pairs)
        hits.append({"code": "R03", "detail": f"{len(pairs)} large deposits followed within 48 hours by "
                     f"withdrawals of at least 90 percent, {_money(moved)} moved.",
                     "txn_ids": [x["id"] for p in pairs for x in p]})

    # R04 wires with a high-risk jurisdiction
    risky = [t for t in txns if t["channel"] == "wire" and t["counterparty_id"]
             and cps[t["counterparty_id"]]["country"] in HIGH_RISK_COUNTRIES]
    if risky:
        countries = sorted({HIGH_RISK_COUNTRIES[cps[t['counterparty_id']]['country']] for t in risky})
        hits.append({"code": "R04", "detail": f"{len(risky)} wires involving {', '.join(countries)}.",
                     "txn_ids": [t["id"] for t in risky]})

    # R05 counterparty name close to a watchlist entry
    matches = []
    for cp_id in {t["counterparty_id"] for t in txns if t["counterparty_id"]}:
        cp = cps[cp_id]
        for entry in WATCHLIST:
            sim = name_similarity(cp["name"], entry["name"])
            if sim >= WATCHLIST_THRESHOLD:
                matches.append({"counterparty_id": cp_id, "counterparty": cp, "entry": entry,
                                "similarity": round(sim, 3)})
    if matches:
        m = max(matches, key=lambda x: x["similarity"])
        hits.append({"code": "R05", "detail": f"\u201c{m['counterparty']['name']}\u201d is a "
                     f"{round(m['similarity'] * 100)}% name match to \u201c{m['entry']['name']}\u201d.",
                     "txn_ids": [t["id"] for t in txns if t["counterparty_id"] in {x['counterparty_id'] for x in matches}],
                     "matches": matches})

    # R06 total volume over the window above 3x expected monthly
    volume = sum(t["amount"] for t in txns)
    if volume > 3 * acct["expected_monthly"]:
        ratio = volume / acct["expected_monthly"]
        hits.append({"code": "R06", "detail": f"{_money(volume)} moved in 30 days, {ratio:.1f} times the "
                     f"{_money(acct['expected_monthly'])} monthly profile.", "txn_ids": []})

    for h in hits:
        h["name"] = RULES[h["code"]]["name"]
    return hits


def screen(activity: dict) -> list[dict]:
    
    by_acct: dict[str, list[dict]] = {}
    for t in activity["transactions"]:
        by_acct.setdefault(t["account_id"], []).append(t)
    alerts = []
    for acct_id, acct in activity["accounts"].items():
        txns = sorted(by_acct.get(acct_id, []), key=lambda t: (t["date"], t["id"]))
        hits = _rule_hits(acct, txns, activity["counterparties"])
        if hits:
            alerts.append({"account_id": acct_id, "hits": hits,
                           "risk_score": min(100, sum(RULES[h["code"]]["weight"] for h in hits))})
    alerts.sort(key=lambda a: -a["risk_score"])
    return alerts


# Stage 3: case files + answer key

UNPLANTED_TRUTH = {
    "disposition": "close", "typology": None, "scenario": "background",
    "debrief": "Ordinary activity that brushed a threshold. Nothing in the pattern or profile "
               "suggests laundering. Close.",
}


def assemble_batch(activity: dict, alerts: list[dict], batch_id: str, source: str = "dag",
                   run_id: str | None = None) -> dict:
    by_acct: dict[str, list[dict]] = {}
    for t in activity["transactions"]:
        by_acct.setdefault(t["account_id"], []).append(t)
    cases, truth = [], {}
    for i, alert in enumerate(alerts, start=1):
        acct_id = alert["account_id"]
        txns = by_acct.get(acct_id, [])
        cp_ids = {t["counterparty_id"] for t in txns if t["counterparty_id"]}
        case_id = f"ALRT-{i:04d}"
        cases.append({
            "case_id": case_id,
            "account": activity["accounts"][acct_id],
            "risk_score": alert["risk_score"],
            "hits": alert["hits"],
            "transactions": txns,
            "counterparties": {c: activity["counterparties"][c] for c in sorted(cp_ids)},
        })
        truth[case_id] = activity["planted"].get(acct_id, UNPLANTED_TRUTH)
    return {
        "batch_id": batch_id,
        "source": source,
        "run_id": run_id,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "as_of": activity["as_of"],
        "window_start": activity["window_start"],
        "stats": {"accounts": len(activity["accounts"]), "transactions": len(activity["transactions"]),
                  "alerts": len(alerts)},
        "typologies": TYPOLOGIES,
        "rules": {k: v["name"] for k, v in RULES.items()},
        "cases": cases,
        "truth": truth,
    }


def public_view(batch: dict) -> dict:
    return {k: v for k, v in batch.items() if k != "truth"}



# Scoring

def score_verdict(truth: dict, disposition: str, typology: str | None, seconds: float) -> dict:
    speed_bonus = max(0, int((90 - seconds) / 3)) if seconds < 90 else 0
    if truth["disposition"] == "sar" and disposition == "sar":
        typology_ok = typology == truth["typology"]
        points = 100 + (50 if typology_ok else 0) + speed_bonus
        outcome = "correct_sar"
        headline = ("Correct escalation, and you named the typology." if typology_ok else
                    f"Correct escalation, but the typology was {TYPOLOGIES[truth['typology']].lower()}.")
    elif truth["disposition"] == "sar":
        points, outcome = -150, "missed_sar"
        headline = "Missed SAR. This one needed to be reported."
    elif disposition == "close":
        points, outcome = 100 + speed_bonus, "correct_close"
        headline = "Correct. A false positive, closed cleanly."
    else:
        points, outcome = -50, "defensive_filing"
        headline = "Defensive filing. This activity has a documented explanation."
    return {
        "points": points,
        "outcome": outcome,
        "headline": headline,
        "speed_bonus": speed_bonus if points > 0 else 0,
        "debrief": truth["debrief"],
        "truth": {"disposition": truth["disposition"], "typology": truth["typology"],
                  "typology_label": TYPOLOGIES.get(truth["typology"]) if truth["typology"] else None},
    }
