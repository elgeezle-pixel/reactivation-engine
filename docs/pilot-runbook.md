# Reactivation Engine: Pilot Runbook

How to run a patient reactivation batch for a clinic, start to finish.
Follow it in order every time. Don't rely on memory.

---

## 0. Every session starts here

```
cd ~/Documents/reactivation-engine
source .venv/bin/activate
git status
```

- The prompt must start with `(.venv)`. If not, activate again.
- `git status` should say "nothing to commit". If not, find out why before changing anything.
- Before creating any new file in VS Code, click **reactivation-engine** at the top of the Explorer, so the file lands in the main folder.

---

## 1. One-time setup for a new clinic

**Agree with the clinic first (no code):**
- [ ] Patients have agreed to be contacted by the clinic (e.g. registration form)
- [ ] Advice taken on data protection for patient data
- [ ] Which WhatsApp number sends: the clinic's own number
- [ ] Who answers replies, and that they're ready before the first batch
- [ ] Date format of their export confirmed by looking at sample rows
- [ ] Any offer: exact wording, what it covers, end date, front desk told
- [ ] How success is measured: replies, bookings, attendance

**Create the clinic folder** (inside `clients/`, which git ignores):

```
mkdir -p clients/<clinic-name>
cp demo_clinic/settings.json clients/<clinic-name>/settings.json
```

Edit `clients/<clinic-name>/settings.json`:
- `clinic_name`, `greeting`
- month cut-offs (`skip_under_months`, `due_until_months`, `lapsed_until_months`)
- `incentive`: set the exact offer text, `valid_until` (YYYY-MM-DD) and `segments`,
  or delete the whole `incentive` block for no offer
- optional: `"contact_cooldown_days": 60`

Save the clinic's export as `clients/<clinic-name>/patients.csv` with
columns `name,phone,last_visit`.

**Dry run (no messages):**

```
python3 patients.py clients/<clinic-name>
```

- Read every `needs_review` reason and fix the rows with the clinic.
- If it stops with a month-first date error, the file's date format is
  wrong. Do not work around it; confirm the format with the clinic.
- If it prints a date WARNING, confirm the format with the clinic before sending.

---

## 2. Each batch

**a. Create the review file**

```
python3 make_patient_review.py clients/<clinic-name>
```

Note the filename it prints. Check the summary:
- API errors: re-run the command later
- Failed checks: read those messages first
- Phone problems: fix the number in `patients.csv`, then re-run
- "Skipped, contacted in the last 60 days": normal, nobody gets messaged twice

**b. Review and approve**

Open the review file in VS Code. For each patient, read the message
(including spelling) and type `yes` at the very end of the record,
after the last comma. Leave blank or type `no` to hold back.

- A flag means "read carefully", not "reject".
- You may edit the wording. The edited text is what gets sent.
- For a pilot sent 10 a day: approve 10 per review file.

Save (Cmd+S), then confirm what was saved:

```
python3 -c "import csv; [print(r['name'], '|', repr(r['approved'])) for r in csv.DictReader(open('review/<review-file>.csv', encoding='utf-8-sig'))]"
```

**c. Build the send list** (this also logs everyone on it as contacted)

```
python3 make_send_list.py review/<review-file>.csv clients/<clinic-name>
open review/<review-file>_send.html
```

- Build **one** send list per review file. Never go back to an old review file.
- "Approved but blocked" means read the reason and fix it. Never force it.

**d. Send**

- WhatsApp Web or Desktop must be logged in to the **clinic's** number.
- For each card: tap "Open in WhatsApp", check the message, send, tick "Sent".
- Ticks are remembered in that browser only.

**e. Track results** (keep a simple sheet)

`name | date sent | replied (y/n) | booked (y/n) | attended (y/n)`

---

## 3. Never do

- Never `git add .` or `git commit -a`. Always name the files.
- Never commit anything from `clients/` or `review/`, or `contact_log.csv`.
  Check `git status` before every commit.
- Never paste the API key into a chat or screenshot.
- Never tap WhatsApp links for demo or test data.

---

## 4. Troubleshooting

| What you see | Cause | Fix |
|---|---|---|
| `No module named 'dotenv'` | venv not active | `source .venv/bin/activate` |
| `can't open file ...` | file in the wrong folder | `find . -name "<file>" -not -path "./.venv/*"`, then move it |
| `401 invalid x-api-key` | API key revoked or replaced | New key in the Anthropic Console, update `.env` |
| `missing column(s)` | export has different headers | Rename the headers to `name,phone,last_visit` |
| Month-first date error | export uses MM/DD/YYYY | Confirm with the clinic; don't edit dates by hand |
| `API error: Request timed out` | network dropped | Re-run the review later |
| A file still shows in `git status` after adding it to `.gitignore` | space before the line | `cat .gitignore` and remove leading spaces |