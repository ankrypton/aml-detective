# AML Detective

**Work a real anti-money-laundering alert queue inside the Airflow UI.**

An Airflow DAG runs a transaction-monitoring pipeline over synthetic bank activity. Its rules engine raises alerts, and an Airflow 3.1 plugin turns those alerts into case files you investigate. Close the alert or escalate it with a SAR, and see how your judgment compares to the answer key.

Built for the Astronomer Apache Airflow hackathon, **Plugin Powerhouse** track.

[**Watch the 3-minute demo**](https://youtu.be/tjbrTRkdkHc)

![A case file in AML Detective, stamped SAR FILED]()

---

## Quick start

Requires Docker and the [Astro CLI](https://www.astronomer.io/docs/astro/cli/overview).

git clone https://github.com/ankrypton/aml-detective.git

cd aml-detective

astro dev start

1. Open [http://localhost:8080](http://localhost:8080).  
2. Trigger the **aml\_detective\_case\_factory** DAG.  
3. Go to **Browse \> AML Detective**, enter an analyst name, and start your shift.

Before the DAG has run, the plugin serves a practice shift, so the page is never empty.

## How to play

Each alert in your queue is a case file with three parts:

- **Customer profile:** who they are, what they do, and how much money normally moves through their account each month.  
- **Why this alerted:** the rules that fired. Click one to highlight the transactions behind it.  
- **Money flows and statement:** a graph of where the money came from and went, plus every transaction from the last 30 days.

Decide whether it's laundering. **Close alert** if it's a false positive, or **Escalate and file SAR** and name the typology. The file gets stamped, and a debrief explains what was really going on.

| Outcome | Points |
| :---- | :---- |
| Correct escalation | \+100 |
| ...and the right typology | \+50 more |
| Correct close | \+100 |
| Speed bonus (decisions under 90 seconds) | up to \+30 |
| Escalating a false positive | \-50 |
| Missing a real case | \-150 |

A missed SAR costs the most, because in real compliance work it's the worst outcome. Each shift has its own leaderboard.

## How it works

### The DAG builds each shift

`aml_detective_case_factory` produces a new shift on every run:

generate\_activity  ──\>  screen\_transactions  ──\>  publish\_case\_batch  ──\>  Asset: aml\_case\_batches

48 accounts,            rules engine screens      case files and a

\~440 transactions       every account blind       server-side answer key

1. **generate\_activity** creates 30 days of synthetic bank activity. A few accounts carry a planted scenario; the rest are ordinary customers.  
2. **screen\_transactions** runs a rules engine over every account with no knowledge of what was planted, the way a production monitoring system works.  
3. **publish\_case\_batch** turns the alerts into case files and stores the answer key where the browser can't see it.

### The rules

| Rule | Fires on |
| :---- | :---- |
| R01 | 3+ cash deposits of \$8,000 to \$9,999 within 10 days |
| R02 | 6+ different senders within 14 days |
| R03 | A deposit of \$25,000+ followed within 48 hours by a withdrawal of at least 90% of it |
| R04 | Wires to or from a FATF call-for-action jurisdiction |
| R05 | A counterparty name 88%+ similar to a watchlist entry |
| R06 | 30-day volume above 3 times the customer's expected monthly activity |

### The scenarios

Every shift mixes real laundering with convincing false positives. The false positives trip the same rules as the real cases, so you have to read the file to tell them apart.

| Real typologies | False positives |
| :---- | :---- |
| **Structuring:** cash deposits kept just under the \$10,000 reporting threshold | **Seasonal retailer:** a holiday surge that's documented in prior years |
| **Funnel account:** many unrelated senders, money out as cash and wires | **Innocent namesake:** a name close to a watchlist entry, but the birth date and nationality don't match |
| **Rapid movement of funds:** offshore money in, out again within a day | **Escrow agent:** money in and straight back out, which is the business model |
| **High-risk jurisdiction:** repeated wires with no business reason on file |  |
| **Sanctions match:** name, birth date, and nationality all match a list entry |  |

All names, companies, and watchlist entries are fictional.

### The plugin

The plugin uses Airflow 3.1's plugin system:

- A **FastAPI app** (`fastapi_apps`) serves the game's API and its JavaScript at `/aml-detective`.  
- A **React app** entry (`react_apps`) adds **AML Detective** to the Browse menu.

There's no frontend build step. The UI is a single JavaScript file that uses the React instance the Airflow UI shares with plugins. Verdicts are scored on the server, and each case can only be scored once per analyst.

## Airflow features used

- **Airflow 3.1 plugins:** `AirflowPlugin` with `fastapi_apps` and `react_apps`  
- **The shared React runtime** the Airflow UI provides to plugins  
- **TaskFlow API** from the Airflow 3 Task SDK (`airflow.sdk`)  
- **Assets:** each run updates the `aml_case_batches` asset  
- **Airflow Variables:** tasks write shifts through the Task SDK; the plugin reads them from the metadata database  
- **`[api] base_url`:** browser-facing URLs include any deployment path prefix  
- **`dag.test()`** and DagBag checks in the test suite

## Project structure

aml-detective/

├── dags/

│   └── aml\_detective\_case\_factory.py      \# the pipeline that builds each shift

├── plugins/

│   ├── aml\_detective\_plugin.py            \# plugin registration and FastAPI app

│   └── aml\_detective/

│       ├── engine.py                      \# activity generator, rules engine, scoring

│       ├── store.py                       \# shift and leaderboard storage

│       └── static/aml-detective.js        \# the game UI

├── tests/

│   ├── dags/                              \# DAG integrity and end-to-end tests

│   └── plugins/                           \# engine and API tests

├── Dockerfile                             \# Astro Runtime 3.1

└── requirements.txt

## Tests

astro dev pytest

The suite covers:

- **The rules engine:** across 50 seeds, every planted scenario alerts and no ordinary account does.  
- **Signature rules:** each scenario fires the rule it's designed around.  
- **Secrecy:** the answer key never reaches the browser.  
- **Scoring**, the verdict API, and the leaderboard.  
- **End to end:** the real DAG runs, writes a shift through Variables, and the plugin serves and scores it.

## Configuration

| Variable | Default | Purpose |
| :---- | :---- | :---- |
| `AML_DETECTIVE_STORE` | `variable` | Where shifts and the leaderboard live. `variable` uses Airflow Variables and works anywhere. `file` uses JSON files, which suits offline tests. |
| `AML_DETECTIVE_DATA_DIR` | `include/aml_detective` | Folder for the `file` backend. |

With the default backend, the answer key is stored under a Variable name Airflow masks on its Variables page.

## Known limits

- The React plugin interface is marked experimental in Airflow 3.1.  
- The plugin's API endpoints aren't behind Airflow authentication. Add a FastAPI security dependency before using this anywhere real.  
- Fonts load from Google Fonts and fall back to system fonts if blocked.

## Ideas for what's next

- **Human in the loop:** escalating a case triggers a SAR-filing DAG that waits for a supervisor's sign-off through an Airflow 3.1 approval step.  
- **Agentic narratives:** an LLM drafts the SAR narrative from the case file for the analyst to edit.  
- **Dashboard widget:** open alerts shown on the Airflow home page.