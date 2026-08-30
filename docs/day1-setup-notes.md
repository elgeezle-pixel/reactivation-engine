# Day 1 — Environment Setup: What I Did and What I Broke

Project: **reactivation-engine** (Week 1 of 12)
Machine: MacBook Air, macOS, zsh shell, Python 3.14.3
Repo: github.com/elgeezle-pixel/reactivation-engine

---

## Part 1 — What Day 1 actually accomplished

Almost no Python was written. Day 1 built the *workspace*: a sealed
Python environment, a version-control repo, and a link between my
laptop and GitHub. This is a one-time tax per machine.

The finished state:

```
reactivation-engine/
├── .venv/              ← private Python for this project (not in Git)
├── .git/               ← version history (hidden)
├── .gitignore          ← list of things Git must ignore
├── README.md           ← what this project is
└── requirements.txt    ← list of installed packages
```

---

## Part 2 — The four concepts underneath it

### 1. The shell is literal

zsh takes what I type, splits it on spaces, and treats the **first
word** as a command name. It does not guess, autocorrect, or infer
intent. Every error I hit on Day 1 came back to this.

### 2. Virtual environments

`.venv` is a private copy of Python belonging to one project.
Installing pandas inside it cannot affect any other project.
Without it, every project shares one global Python, and eventually
two projects need different versions of the same library and one
of them breaks.

`source .venv/bin/activate` switches my terminal into it. The
`(.venv)` prefix on my prompt is the proof it worked. Inside the
venv, plain `python` works even though it doesn't otherwise on macOS.

### 3. VS Code needs the project folder open

VS Code's idea of "the project" is whatever folder is open. With no
folder open, it cannot find `.venv`, cannot offer it as an
interpreter, and creates new files in unpredictable places.

### 4. Git tracks what I tell it to

`.gitignore` lists what Git must never record. `.venv/` (thousands
of files), `.env` (API keys), `__pycache__/` (junk), and any real
client data. Setting this up *before* the first commit is the whole
point — removing files after they're committed is much harder.

---

## Part 3 — Every mistake, and the rule it taught

### Mistake 1 — `python--version`
```
zsh: command not found: python--version
```
Missing space. zsh looked for a command literally named
`python--version`.
**Rule:** read the error's quoted text. It names exactly what the
shell searched for, which exposes the typo.

### Mistake 2 — `python` doesn't exist on macOS
```
zsh: command not found: python
```
Apple removed the bare `python` command. Nothing was broken.
**Rule:** on this Mac, use `python3` and `pip3` outside a venv.
Inside an activated venv, plain `python` works.

### Mistake 3 — selected the global interpreter
The Select Interpreter list offered `/usr/local/bin/python3` and two
Apple system 3.9 installs, but not my `.venv` — because no folder
was open.
**Rule:** open the project folder first, then select the interpreter.
If `.venv` isn't listed, the folder isn't open (or hit refresh in
the picker dialog).

### Mistake 4 — nested duplicate folder
Ran `mkdir reactivation-engine` while already inside
`reactivation-engine`, creating a folder inside itself.
**Rule:** `pwd` prints where I am. Check before creating things.
`rmdir` removes an empty folder and safely refuses if it has contents.

### Mistake 5 — `source.venv/bin/activate`
```
zsh: no such file or directory: source.venv/bin/activate
```
Same missing space as Mistake 1. Also: I was *already* activated, so
the command wasn't needed.
**Rule:** check the prompt for `(.venv)` before re-running activate.

### Mistake 6 — pasted file contents into the terminal
Pasted the three `.gitignore` lines straight into zsh, which tried to
run them as commands.
**Rule:** file contents go in files. To create a file from the
terminal reliably:
```bash
cat > .gitignore << 'EOF'
.venv/
.env
__pycache__/
EOF
```
This means "write everything up to EOF into this file, right here."

### Mistake 7 — created a file inside `.venv`
Used the sidebar's new-file button while `.venv` was selected, so the
file landed inside it — then pasted README text into a file named
`.gitignore`. Two errors stacked.
**Rule:** the sidebar creates files inside whatever is *selected*.
Click the project name first, or use the terminal where `pwd` tells
me exactly where I am. Check the breadcrumb above the editor.

### Mistake 8 — pasted six commands at once
`git init`, `git add`, `git commit`, `git status` all ran together.
Earlier failures scrolled past unread.
**Rule:** one command at a time. Read the output before the next one.
This is the habit that would have prevented mistakes 6 and 7.

### Mistake 9 — repo name had a trailing hyphen
```
fatal: Authentication failed for
'https://github.com/elgeezle-pixel/reactivation-engine-.git/'
```
A stray character in the GitHub name field.
**Rule:** read error paths character by character. Fix a wrong remote
with `git remote set-url origin <correct-url>`, then confirm with
`git remote -v`.

### Mistake 10 — `brew: command not found`
Homebrew isn't part of macOS; it has to be installed. Same for `gh`.
**Rule:** "command not found" means not installed, or installed
somewhere not on PATH. `ls /usr/local/bin/<name>` distinguishes the
two.

### Mistake 11 — chased tooling instead of the goal
Spent a long stretch trying to install `gh` when the actual goal was
just to push. The push worked without it — a stored credential was
already present.
**Rule:** when a tool won't install, ask what it was *for*. There's
usually a second route. Don't debug the detour.

---

## Part 4 — Command reference

### Environment
```bash
python3 --version              # check Python (outside a venv)
python3 -m venv .venv          # create the environment
source .venv/bin/activate      # activate it
deactivate                     # leave it
which python                   # which Python am I using?
pip list                       # what's installed here?
pip install <package>
pip freeze > requirements.txt  # record installed packages
```

### Navigation
```bash
pwd            # where am I?
ls             # what's here?
ls -a          # include hidden files (.gitignore, .venv)
cd <folder>    # go in
cd ..          # go up one
```

### Git
```bash
git init                        # start tracking this folder
git status                      # what's changed? — run this constantly
git add .                       # stage everything not ignored
git commit -m "message"         # save a snapshot
git push                        # send to GitHub
git remote -v                   # what address am I pushing to?
git remote set-url origin <url> # fix a wrong address
```

### VS Code
- `Cmd + \`` — toggle terminal
- `Cmd + Shift + P` — command palette
- `Cmd + Shift + P` → `Python: Select Interpreter`
- File → Open Folder — defines the project

---

## Part 5 — Start-of-session checklist

Every time I sit down to work:

1. Open VS Code, confirm the **project folder** is open (sidebar shows it)
2. Open the terminal (`Cmd + \``)
3. Run `source .venv/bin/activate` — confirm `(.venv)` appears
4. Run `git status` — know what state I'm in before changing anything

Four steps, ten seconds, prevents most of Day 1's problems.

---

## Part 6 — The three habits worth keeping

1. **One command at a time.** Read the output before the next one.
2. **Read errors literally.** The message names exactly what the
   computer looked for and didn't find. It is not vague; I was
   skimming it.
3. **Know where I am.** `pwd` in the terminal, breadcrumb in the
   editor, `(.venv)` in the prompt. Most confusion is location
   confusion.

---

## Honest assessment of Day 1

Eleven errors in one setup session is normal, not slow. Every one was
environmental — none were about Python or logic. They came from three
recurring causes: missing spaces, not knowing which folder I was in,
and running commands in batches so failures went unread.

None of these will recur once the checklist in Part 5 is automatic.
