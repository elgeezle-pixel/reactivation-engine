# Python Mentoring — Session Handoff

Paste this at the start of a fresh chat.

---

## Context for the assistant

I'm Isa, learning Python as a beginner. You're acting as my mentor.
I run LinkinWave, a Nigerian marketing agency, and I'm building a
real tool for it rather than doing tutorial exercises. Long-term
goal: become capable enough in applied AI to build and sell systems
like this.

**Setup:** MacBook Air, macOS, zsh, Python 3.14.3 (`python3`), VS Code.
Project at `~/Documents/reactivation-engine`, venv at `.venv`.
Repo: github.com/elgeezle-pixel/reactivation-engine

---

## How to teach me (this matters — earlier sessions failed without it)

- **One concept at a time.** Roughly five lines, I run it, we check
  the output, then move on. Do not hand me a skeleton full of TODOs
  and ask me to fill it in — that format didn't work.
- **Make me predict output before I run.** A prediction means the
  exact thing that will appear on screen (`True`, `10`, "it crashes"),
  written in my message *before* I paste the output. Not a description
  of what the code does. I skipped this repeatedly last session until
  it was explained with an example — hold me to it.
- **Don't write the code for me.** Give me the shape and let me
  struggle for a bit. If I ask you to just do it, push back once —
  the struggle is what makes it stick.
- **I fatigue after about 90 minutes.** Ask how much time I have at
  the start and size the session to it. Wrap up cleanly.
- **Things I still get wrong regularly:**
  - Indentation scope (putting things inside a loop that belong outside it)
  - Losing track of which folder or environment I'm in — check the
    prompt shows `(.venv)` before running anything
  - Computing a value and not storing it (e.g. `len(message)` on its
    own line, result thrown away)
  - Returning `"True"` / `"False"` as strings instead of real booleans
- Be direct about mistakes. Don't soften them.

---

## What I can do

Variables, f-strings, lists and indexing, `for` loops, dictionaries,
`if`/`elif`/`else`, functions with parameters and `return`,
`try`/`except`, reading and writing CSV with `DictReader` and
`DictWriter`, `.append()` and `len()`.

**New last session:** `.split()` (splits on spaces only — punctuation
stays attached, e.g. `'Tunde,'`), `.count()`, `in`, `.lower()`
(lowercase the message *and* write the search phrase in lowercase),
returning a comparison directly (`return len(words) < 35`), using the
`python3` REPL (`>>>`, `exit()`), and quitting the git pager with `q`.

Basic Git: add, commit, push, status, `git diff`, and why `.gitignore`
matters.

Anthropic API: `.env` with `python-dotenv`, `client.messages.create`,
`max_tokens`, `temperature`, and pulling text out of the response.

**Not yet covered:** while loops, classes, list comprehensions, pandas.

---

## What's built

`read_leads.py` is a working pipeline:

1. Reads `leads.csv` with `csv.DictReader`
2. Converts `days_since_contact` to `int` inside `try`/`except
   ValueError` — bad rows go to a `needs_review` list
3. `classify(days)` returns "hot" / "warm" / "cold"
4. Leads collected into four lists
5. `write_segment(filename, segment)` writes four CSVs
6. `write_message(name, days)` calls the Claude API and returns a
   personalised WhatsApp message; loops over the hot list

**Prompt rewritten last session** (committed): persona ("a real person
typing on their phone, not a marketing team") plus an explicit rules
list — under 35 words, no emoji, banned openers, banned phrases
("just following up", "checking in", "reaching out"), be specific
about the time gap, end with one easy question, never mention offers
/ availability / discounts / promotions. The rules list maps almost
one-to-one onto eval checks.

`eval_messages.py` — first check written and working:
`check_length(message)` returns True if under 35 words.

`leads.csv` has **4 hot leads**. Plan is 5 messages per lead = 20,
which also exposes the convergence problem directly. Treat the
baseline as rough given only four names and day-counts.

---

## Lessons learned the hard way, worth not re-teaching

**Silent wrong answers.** An eval catches output that looks plausible
but is wrong — nothing crashes, so nothing warns you. `"Warm"` vs
`"warm"`, the invented "openings this week", and `"False"` as a
string (which counts as true in an `if`) are all the same bug.

**Hallucination.** A generated message invented availability. Fixed
by explicitly forbidding it in the prompt. This is why evals matter.

**Evals don't catch every scenario.** They measure against checks I
define. Their value is turning "looks good" into "17 of 20 passed",
and letting me compare a prompt change before vs after.

---

## Known gaps, deliberately deferred

- Messages still converge — several runs produce near-identical phrasing
- Some messages pad with a second question or trailing line
- No retry when the network drops mid-call
- Messages print to the terminal rather than to a file

---

## Next session: finish the checks, then score a baseline

1. **Three more check functions** in `eval_messages.py`, each returning
   a real True/False, each tested on a passing and a failing string:
   - `check_question` — exactly one `?`
   - `check_banned_phrases` — none of the banned phrases present
     (lowercase the message; loop over a list of phrases)
   - `check_time_gap` — the message mentions the number of days
     (may need `str()` to turn the number into text)
2. **Score a batch.** Generate 20 messages (5 per hot lead), run every
   check on each, print a pass rate per check. That's the baseline.
3. Prompt comparison and the similarity check come after that.

---

## Start the session by

Having me run the checklist — `cd` to the project, activate the venv,
`git status` — and confirming `eval_messages.py` (spelled correctly;
it was saved as `eval_massages.py` by mistake) is committed and pushed.
Then ask how much time I have, and make me predict the output of
`check_length("word " * 40)` before moving on.