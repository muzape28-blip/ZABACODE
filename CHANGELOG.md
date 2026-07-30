# Changelog

## Unreleased

### Safety
+- Oracle Auto-Fix now fingerprints the exact source analyzed and records the active tab revision. A patch is rejected if the user switches tabs, edits the buffer, or otherwise changes the document before selecting **Apply Fix**.
+- Auto-Fix previews now compare against the source snapshot that generated the patch, never against whichever tab content happens to be open when the response arrives.

All notable changes to **ZABACODE** will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased] - 2026-07-30 — Oracle: future retrieval and local-model direction

### Planned — keep Oracle deterministic before introducing RAG

Oracle will continue to be developed first as ZABACODE's **offline,
deterministic code diagnostician**, rather than being presented as an LLM. Its
trusted paths—traceback explanation, buffer analysis, and safe Auto-Fix—remain
parser- and rule-driven, with fixes accepted only after verification. This is
important for an offline Android editor: a concise, evidence-based refusal is
better than a confident but invented explanation.

A full Retrieval-Augmented Generation (RAG) feature is intentionally deferred.
Retrieval can locate relevant files or documentation, but it does not itself
provide reliable reasoning or natural-language generation. Adding it before a
well-trained, evaluated generator is available could create missed context,
incorrect links between code fragments, verbose babbling, or gibberish.

### Planned — retrieval as an honest, optional stepping stone

A future local retrieval feature may begin as **project/document search**, not
as a claimed code-understanding assistant. It should return factual, inspectable
results such as relevant file paths, symbols, and line ranges. Any later
explanation must cite the retrieved source and say when the available context is
insufficient.

Potential retrieval sources, in order of practical value, are:

1. ZABACODE's bundled documentation, for accurate offline help about the app.
2. The active project's local code and text files, for navigation and context.
3. Optional, curated Python/Kivy/Buildozer knowledge packs.

Indexes must remain local by default, respect project privacy, and be designed
for mobile storage and memory limits. A large raw corpus must not be bundled
into the APK simply to claim RAG support.

### Planned — separate local-LLM research track

A custom Python LLM implementation and its training corpus are a separate
future research track, not a dependency of the current Oracle. Only after the
model has been trained, evaluated for code tasks, and made feasible for the
target hardware should it be considered as an optional generator for retrieved
context. Even then, deterministic diagnosis and parser-verified Auto-Fix remain
the safety baseline.

---

## [Unreleased] - 2026-07-29 — Audit beyond the Oracle: plugins & RUN gate

A deliberate sweep of the modules the previous sessions never touched — the
plugins that rewrite user code, and the guard that decides whether code is
allowed to run at all. 260 → 272 tests.

### Fixed — "Code Beautifier Pro" corrupted every annotated function

The beautifier padded operators one character at a time, so any token it did
not recognise was split and re-spaced into something that no longer parses:

| you wrote | it produced |
|---|---|
| `def f() -> int:` | `def f() - > int:` |
| `n //= 2` | `n // = 2` |
| `n >>= 1` | `n > >= 1` |
| `n &= 1` / `n \|= 1` / `n ^= 1` / `n %= 3` | `n & = 1` etc. |

Any user with a type-annotated function got broken code back. Operators are now
matched longest-first from one complete table (`//=` before `//` before `/`),
and a test asserts that ordering so a prefix can never shadow the full token.
Verified across 125 plugin × sample combinations: the output not only parses,
its **AST is identical** to the input.

### Fixed — Syntax Guard blocked code it should not have

The RUN button's linter plugin (active by default) compared raw `(` and `)`
counts, which also counts brackets inside strings and comments. So this was
refused outright, with no way to run it:

```python
print('a smiley :)')
```

`/api/check` has always stripped strings and comments before balancing, but the
UI never called it. The guard now defers to that endpoint, reports the real
issues, and offers "Run anyway?" instead of a hard block — and if the check
itself fails, execution proceeds rather than trapping the user.

### Fixed — two more Oracle claims that were not true

- The pip answer boasted *"We bypassed TLS issues automatically"*. That bypass
  (`--trusted-host`) was **deliberately removed** in v1.2.0 as security fix #22
  and is documented in `SECURITY.md`. The answer now describes verified TLS with
  the bundled `certifi` store, and points at the real remedy (check the device
  clock first — a wrong date invalidates every certificate).
- The `input()` answer told users to *"use the Interactive Run mode"*, which
  does not exist as a mode. It now describes what actually happens: press RUN,
  the terminal pauses at `input()`, and the box at the bottom activates.

Tests now pin the Oracle's claims to the code, so a promise cannot drift out of
sync with the app again.

---

## [Unreleased] - 2026-07-29 — Charts finally appear when you press RUN

### Fixed — matplotlib silently did nothing on the path the RUN button uses

ZABACODE has two execution modes, and they exist for good reasons:

| | `/api/run` (batch) | `/api/run/interactive/*` |
|---|---|---|
| `input()` | stubbed, returns `""` | genuinely blocks and waits |
| output | one blob at the end | streamed live, polled every 150 ms |
| **images** | **collected** | **never collected** |
| used by RUN button | no | **yes** |

Only the batch path ever gathered generated images — and the editor drives the
interactive one. So a user who followed the Oracle's own advice:

> "Save instead of `show()` on Android — ZABACODE picks the image up automatically"

got nothing. The `.png` was written to `files/` and simply never surfaced.
Android has no display, so `plt.show()` is a no-op and `savefig()` is the *only*
way to see a chart — which made this the difference between matplotlib working
and appearing broken.

The interactive session now captures images too, and the terminal renders them
inline as they are produced (a loop emitting several plots shows each one as it
lands, rather than all at the end).

Care taken:

- **No duplicates.** A per-session baseline advances as images are delivered, so
  the 150 ms poll cannot re-send the same chart forever.
- **No stale files.** The baseline is snapshotted before the child process can
  write, so leftovers from an earlier run are not reported as new.
- **No half-written files.** A file still being flushed fails to encode and
  stays queued for the next poll instead of arriving corrupt.
- **Bounded.** Renders over 8 MB are skipped rather than shipped, since a base64
  blob that size stalls the WebView bridge on a low-end phone.
- **Only `data:` URIs are rendered** — never a remote `src`, which would breach
  both the CSP and the offline-first guarantee.

### Changed — `/api/run` documented instead of deleted

It looked like dead code (nothing in the UI calls it), but removing it would
have deleted the only image-capture logic in the project. It is the legitimate
non-interactive counterpart — used by automation and 9 tests — and its
docstring now says so, including why its traceback line needs
`line_offset=PRELUDE_LINE_COUNT` and the interactive path does not.

Only the image capture is now shared (`collect_new_images()`); the two
execution flows stay separate on purpose, because their input and timeout
semantics genuinely differ.

---

## [Unreleased] - 2026-07-29 — Oracle chat & terminal integration

The engine was fixed in the previous pass; this one connects it to the paths
the user actually touches. 13 new tests, 235 → 248 total.

### Fixed — "fix my code" never used the real repair engine

The chat branch re-implemented its own fixer inline: a regex hunting for the
literal string `hello world`. It therefore described exactly one mistake, and
**never produced corrected code** — while `auto_fix_code()`, the verified engine
already behind the Auto-Fix button, sat unused two functions away. The branch
now calls that engine, so "fix my code" answers with the actual patched source
(and, when it refuses, with CPython's exact line and complaint).

### Fixed — Oracle told users with a full editor that it was empty

`analysis.get("notes")` is falsy for clean code, so valid code with no smells
fell through to the no-buffer branch: *"I don't see your code buffer"* while the
user was looking straight at their program. Valid code now gets a runtime/logic
answer, and only a genuinely blank editor is reported as empty.

### Fixed — Oracle card threw away the line number it had just resolved

The previous pass made line numbers accurate; the terminal card still rendered a
bare `Line 3`. It now echoes the offending source line beneath the explanation
and makes it tappable to jump the editor there (Ace and native), which is what
the accuracy work was for. Out-of-range and blank lines degrade gracefully, and
the echoed source is HTML-escaped.

### Fixed — Oracle card styling silently did nothing

`.oracle-what`, `.oracle-fix` and `.oracle-line` referenced `var(--fg)`,
`var(--ok)` and `var(--dim)` — none of which this stylesheet defines. Undefined
custom properties fail silently, so the green **Fix:** emphasis never rendered.
Repointed at the real variables (`--text`, `--text-bright`, `--text-dim`); a
test now asserts every `var(--x)` used is defined.

### Fixed — two canned messages that were wrong most of the time

- The analyze fallback appended `— Your error is there is no "" at column, add ""`
  to **every** syntax error, regardless of what the parser actually said.
- The rate-limit fallback recited a fixed example about unterminated strings
  instead of looking at the buffer. It now reports the real analysis.

### Changed — truncated reviews are honest about it

`/api/oracle/analyze` returns `note_count` (the true total before the 12-note
cap), and the UI shows "N issues, showing first 12" rather than implying the
visible list is everything.

---

## [Unreleased] - 2026-07-28 — Oracle diagnosis accuracy & knowledge coverage

A follow-up pass over the Oracle, this time probing it with realistic input
rather than its own fixtures. The Auto-Fix engine (below) was already safe and
broad; the *diagnosis* side turned out to be confidently wrong in several
common situations. 36 new tests, 199 → 235 total.

### Fixed — the error card pointed at the wrong line

Two independent bugs, both of which sent the user hunting in the wrong place:

- **Line numbers were read out of the exception message.** The scan was
  `re.finditer(r"line (\d+)")` over the whole traceback, taking the last hit.
  For `json.loads('')` the last "line N" in the text is inside the message
  (`Expecting value: line 1 column 1`), so a crash on **line 3** was reported as
  **line 1**. Only real frame headers (`File "...", line N`) are considered now.
- **The deepest frame is usually library code.** Reporting it pointed users at
  `/usr/lib/python3.11/json/decoder.py` line 355 — for a subprocess crash the
  reported line was **1892** in a two-line script. The Oracle now walks to the
  deepest frame that is still the *user's own file*.

Also fixed: a `SyntaxError` message quotes a line number from the compiled file,
which includes the executor's injected prelude. `if True:` / `print(1)` was
explained as *"expected an indented block ... on line 10"* for a two-line
buffer. Those in-message numbers are now rebased onto editor coordinates, while
`JSONDecodeError`'s "line 1" (which describes the *data*, not the script) is
deliberately left alone.

### Fixed — chained tracebacks explained the wrong exception

With `raise B` inside `except A`, both exceptions are printed. The rule scan ran
over the whole blob and matched **A**, while the line number came from **B** —
one card describing an already-handled error, pointing at an unrelated line.
Only the final exception block is considered now.

### Fixed — knowledge lookup matched on substrings

Keywords were tested with `keyword in question`, which produced absurd results:

- `"oop"` is inside `"l**oop**"`, so **every** question about loops was answered
  with a lecture on object-oriented programming
- `"class"` fired inside "classify", `"@"` fired on any email address

Matching is now anchored at word boundaries (tolerating plurals), and when
several entries match, the most *specific* keyword wins — so "save json to a
file" gets the JSON answer rather than the generic file-handling one. A test
asserts every entry is still reachable via its own keyword, which catches this
class of shadowing automatically. The matcher is precompiled at import: 4.4×
faster than the previous per-call `re.search`.

### Fixed — ordinary questions were answered as crash reports

The traceback detector treated the bare substring `"line "` as evidence of a
traceback, so *"how do I read a line from a file?"* was answered with an error
card titled **"Something went wrong"** that just echoed the question back.
Detection now requires an actual traceback header, frame line, or
`ExceptionName:` prefix.

### Fixed — `async def` was invisible to code review

`analyze_buffer()` matched only `ast.FunctionDef`, so coroutines were missing
from the function list and every check (argument count, docstring, mutable
defaults) silently skipped them. `async def` and `async for` are now handled,
and keyword-only/positional-only parameters are included in the argument count.

### Fixed — review notes buried the real problem

A 40-function file produced 80 notes, pushing actual bugs off a phone screen.
Notes are now de-duplicated and capped at 12, with an explicit count of what was
held back (`note_count` is returned for callers that want the total).

### Added — 21 new error explanations

22 of the 23 most common beginner runtime errors fell through to the generic
*"Something went wrong"* card, which only repeated the raw exception the
terminal had already shown. All 23 now get a real explanation and a concrete
fix, including: unpacking mismatches, `NoneType is not iterable` (usually a
missing `return`), `str + int`, string/list indexed with a name, `no len()`,
too many arguments (the missing `self`), unhashable type, item assignment on an
immutable, `module has no attribute` (often a shadowed stdlib filename),
network unreachable, timeouts, `KeyboardInterrupt`, `MemoryError`,
`OverflowError`, `StopIteration`, and `= vs ==` in a condition.

### Added — 10 new knowledge-base topics

Sorting, sets, recursion, `if __name__ == '__main__'`, string methods, slicing,
`random`, `datetime`, JSON files, and variables/types — each previously fell
through to the generic "here's what I can do" reply.

---

## [Unreleased] - 2026-07-28 — Oracle Auto-Fix correctness, safety & coverage

Full analysis in `AUDIT_REPORT.md`.

### Added — Auto-Fix coverage expansion (error-directed repair)

The safety work below made Auto-Fix trustworthy but left it narrow: it knew only
five hard-coded line shapes, so the most common beginner mistakes on a phone
still returned *"I couldn't produce a patch"*. Measured on 36 realistic
snippets, it repaired 17 and gave up on 13.

The fixer now reads CPython's own diagnosis (`exc.msg`, `exc.offset`,
`exc.end_offset` — previously discarded, only `lineno` was used) and proposes
candidates aimed at that exact complaint. **A candidate is kept only when the
parser demonstrably gets further into the file**, so the F-02 safety contract
is unchanged: nothing is applied on faith.

Newly repaired, all verified end-to-end through `POST /api/oracle/fix`:

- **Python 2 leftovers** — `print 'x'` → `print('x')`, `except E, e:` → `except E as e:`
- **C / Java / JavaScript muscle memory** — `else if` → `elif`, `&&`/`||` →
  `and`/`or`, `!x` → `not x`, `//` comment → `#`, `x++` → `x += 1`,
  `var x = 5` → `x = 5`, `{ }` blocks → `:` blocks
- **Mobile keyboard and chat-app damage** — smart/curly quotes, full-width
  parentheses, non-breaking spaces and other invisible characters
- **Indentation** (the #1 beginner failure on a small screen) — missing block
  body indent, stray indent, tabs mixed with spaces
- **Brackets across lines** — an unclosed `(` on line 1 reported on line 5 is now
  closed at the end of its expression; stray `)` removed
- **Missing tokens** — `in` in a `for` header, commas in literals, `lambda` colon
- **Several independent typos in one file** are repaired in a single pass

Coverage went from 17/30 to 27/30 fixable cases (the 3 genuinely ambiguous ones
are still refused on purpose).

Correct-but-wrong patches are explicitly ranked out, because trading a syntax
error for a runtime error is not a fix:

- `print(hello world)` → `print("hello world")`, **not** `print(hello, world)`
  (which parses, then dies with `NameError`)
- `var x = 5` → `x = 5`, **not** `var: x = 5` (a meaningless type annotation)
- `else if y:` → `elif y:`, **not** `else: if y:` (silently different structure)

### Changed — refusals now carry the parser's diagnosis

When no safe patch exists the Oracle no longer throws away what it knows. The
response adds `error_line`, `error_message` and `attempted_fixes` (partial
patches that helped but weren't sufficient, so were not applied), and the
explanation includes the offending source line with a caret at the failing
column. The UI rendered this path as a generic toast; it now renders the full
card, with the caret block in `<pre>` so the column still lines up — applying
the F-01 lesson that a fix the user cannot see is not a fix.

### Fixed — Auto-Fix froze the UI on large files

The last-resort sweep re-parsed the whole buffer for every line, which is
quadratic. Wider coverage meant more candidates, and an 800-line unfixable file
took **2.31 s** — a visible hang on a phone. The sweep is now bounded to ±40
lines around the reported error (the culprit is essentially always nearby):
**0.16 s**, with no loss of coverage. A test pins the 1.5 s ceiling.

### Fixed
- **Oracle Auto-Fix and traceback cards were completely non-functional (critical).**
  `fetchApi()` never set `Content-Type: application/json`, so the browser sent
  `text/plain`, Flask's `get_json()` returned `None`, and `_get_json_payload()`
  silently substituted `{}`. The Oracle received an empty buffer and replied
  "the editor is empty", which the UI displayed as *"could not automatically fix
  this error safely"*. Affected `/api/oracle/fix` and `/api/oracle/explain`.
  The header is now applied centrally so no caller can omit it.
- **Auto-Fix corrupted syntactically valid code (critical).** Any expression
  inside `print(...)` was wrapped in quotes, so a runtime crash such as
  `print(prices[9])` became `print("prices[9]")` — converting a visible
  `IndexError` into a program that silently prints the wrong thing. Verified
  against `print(math.pi)`, `print(x + 1)`, `print(f())` and `print(a/b)`.
  Auto-Fix now refuses to touch any source that already parses and reports the
  crash as a runtime error instead.
- **Auto-Fix reported success on patches that still failed to parse.** The
  computed `is_success` flag was discarded and `ok` was derived purely from the
  patch count, so `def f(:` was "fixed" to `def f(:):` and offered as
  *PATCH READY*. `ok` now requires the result to parse.
- **`=` → `==` rewriting corrupted keyword arguments.** The regex ignored
  bracket depth, turning `if f(timeout=5):` into `if f(timeout==5):`.
  Replacement is now depth- and string-aware.
- **`check_code()` reported line numbers shifted by 9.** It validated the
  prelude-injected source, so a problem on line 2 was reported as line 11.
- **Interactive tracebacks leaked the internal `_active_run.py` filename**,
  while the isolated runner correctly showed `main.py`.
- Unparseable request bodies now return an explicit `400 invalid_json`
  identifying the missing header, rather than being treated as empty.

### Added
- 15 regression tests covering the browser's real content-type path, auto-fix
  safety invariants, checker line numbers and traceback masking (144 → 159).
- 40 further tests for the coverage expansion above (159 → 199): one per newly
  supported error class, plus the safety invariants that must survive it —
  valid code is never rewritten, `ok: True` always implies the result parses
  (fuzzed by deleting one character at a time from valid snippets), patches
  never delete user content, and large files stay responsive.
- `pyproject.toml` with ruff (`line-length = 120`) and pytest configuration.

### Changed
- CI and `tools/check.sh` run `pytest` with auto-discovery instead of only
  `test_main.py`; `test_hardening_regressions.py` (6 security regression tests,
  including the TLS `--trusted-host` guard) had never been executed.
- Removed unused imports and dead code flagged by ruff; aligned stale `1.0.0`
  version strings in `main.py`, `requirements-dev.txt` and the PyPI User-Agent
  with the actual `1.2.0` release.

---

## [1.2.0] - 2026-07-26 — Custom Endpoint + Philosophy Cleanup (final)

### Philosophy
- **Goal:** Tools as tools, identity stays with community — per Claude review feedback
- **Problem in 1.2.0-arena:** Arena branding was permanently embedded: `__version__ = "1.2.0-arena"`, `__integration__` field, CI workflow `arena-integration.yml` that FAILED build if word "arena" removed, credits listing tool as co-author, roadmap toward deeper integration (push notify, FS sync)
- **Solution in 1.2.0 final:** Keep genuinely useful feature (custom endpoint), remove permanent branding

### Changed
- `zabacode/__init__.py`: `1.2.0-arena` → `1.2.0`, removed `__integration__ = "Arena.ai Agent Mode"`
- `zabacode/core/ai_provider.py`: `arena` → `custom`
  - Removed redundant offline mode (was just `oracle_offline_reply()` + label "⚡ Arena" — duplicate of Oracle, no new capability)
  - Kept useful: custom endpoint mode (URL as API key) → `call_custom_endpoint()`, provider `custom`, neutral label "🔧 Custom Endpoint (OpenAI-compatible)", verified TLS
  - `ALLOWED_PROVIDERS` still 7: openrouter, gemini, groq, mistral, deepseek, ollama, custom
  - `PROVIDER_INFO["custom"]` neutral, no branding
- `templates/index.html`: dropdown `arena` → `custom`, `PROVIDER_MODELS` neutral (custom-default, openai-compatible, ollama-compatible), offline check only `ollama` (not arena)
- `zabacode/web_app.py`: `1.2.0-arena` → `1.2.0`, offline provider only ollama
- `README.md`: Removed Arena Integrated badge + Arena CI badge, boot box now "7 AI Providers: .../Custom", Key Features 1 now "Custom Endpoint — Bring Your Own LLM" (neutral, no Arena branding), Core Team only Zaqi + Contributors, removed INTEGRATION_ARENA.md references, philosophy note "Community-owned — no single tool permanently branded"
- `ZABACODEE.md`: Rewrote to v1.2.0 neutral, added philosophy fix section, added Postponed section for ZMUX and arena offline re-branding, version map includes 1.2.0-arena superseded
- CI: Merged useful security checks from `arena-integration.yml` (no unverified SSL, Ace bundled, CSP, certifi, no CDN) into `build_apk.yml` as general checks without branding gate

### Removed
- `.github/workflows/arena-integration.yml` — deleted (was gating build on word "arena")
- `INTEGRATION_ARENA.md` — deleted (contained branding + credits)
- `tools/arena_sync.py` + `tools/arena_integration_test.py` — deleted (arena-specific)
- ZMUX docs already removed in previous commit, kept postponed note

### Fixed
- Mypy errors in previous `call_arena`: `Incompatible types in assignment (None vs Callable)`, `Function could always be true in boolean context`, `Any | object not indexable` — fixed by fallback function definitions matching exact oracle signatures, safe isinstance checks — now `Success: no issues found in 5 source files`
- Tests: 132 passing (neutral)

### Security
- Custom endpoint uses shared verified `get_ssl_context()` + certifi — no new attack surface
- Removal of arena CI gate reduces coupling, philosophy-aligned

### Notes
- This is the clean, philosophy-aligned final for v1.2.0 — useful tool kept, permanent branding removed

---

## [1.2.0-arena] - 2026-07-26 — Arena Integration + Repository Cleanup (SUPERSEDED)

### Added
- **Arena.ai Integration (7th Provider)** (`zabacode/core/ai_provider.py`):
  - `call_arena()` — offline-first integrated provider from Arena Agent Mode workspace
  - 3 models: `arena-offline-v1` (FREE, <50ms), `arena-oracle-enhanced` (Oracle + static analysis), `arena-custom-endpoint` (URL-as-API-key)
  - Uses shared verified TLS `get_ssl_context()` + certifi, supports custom OpenAI-compatible endpoints
  - `ALLOWED_PROVIDERS` now 7, `PROVIDER_INFO["arena"]` = `Arena.ai (Integrated)` offline mode
  - Frontend `templates/index.html`: arena as first default option, 3 models, bypass key check for offline providers
  - Backend `web_app.py`: `APP_VERSION = "1.2.0-arena"`, offline providers (`arena`, `ollama`) skip API key requirement
- **New CI Workflow** `.github/workflows/arena-integration.yml`: integration-test, build-verification (certifi/openssl, no unverified SSL, Ace bundled), security-scan (CSP headers, keystore), summary
- **Tools**: `tools/arena_sync.py` (status/verify/test-arena/prepare-push CLI) + `tools/arena_integration_test.py` (5 new tests for arena offline, custom endpoint fallback, analysis integration)
- **Docs**: `INTEGRATION_ARENA.md` (400+ lines, flow diagrams, offline/online table, Oracle tie-in) + README overhaul + ZABACODEE.md updated to v1.2.0-arena

### Fixed / Changed
- **README.md overhaul**: Removed ZMUX section entirely (ZMUX independent terminal concept postponed — requires Termux command branching design, `noexec` bypass research, and Android testing). Replaced with accurate **Interactive Execution Engine** description: isolated subprocess with timeout + PGID cleanup + real-time streaming (`/api/run/interactive/*`)
- **Library Manager doc**: Corrected from "Auto SSL-Bypass Fallback" (old insecure) to "Verified TLS + SHA-256" (current secure implementation in `net.py` + `lib_manager.py`)
- **Editor doc**: Replaced "Monaco WebView Focus" with "Ace Editor Bundled Offline" (Ace 1.32.4, 45-60 FPS, touch context menu)
- **Comparison table**: Updated from 6 providers to 7 + Oracle, 3 offline providers
- **Boot box**: Updated counts to 7 providers + Arena
- **Version badge**: `v1.0.0` → `v1.2.0-arena`
- **Quick Start**: Changed from "Run Kivy app" to "Run WebView server (Flask+Waitress @ 127.0.0.1:5000)" + added `arena_sync.py` verification steps
- **Test hardening**: `TestTLSHardening.test_all_ai_providers_use_shared_context` now dynamic (`len(ALLOWED_PROVIDERS)`) instead of hardcoded 6, allowing arena's 7th `urlopen` call
- **Version test**: `TestVersion` now accepts `1.2.0-arena` as valid

### Removed
- **ZMUX documentation**: Section "ZMUX Interactive Terminal (with Android noexec Bypass)" removed from README — code for ZMUX independent terminal was already removed earlier, but docs still mentioned `zmux_bin/.shims/`, launcher alias injection, `pkg`/`apt` Termux commands. Now documented as postponed in `ZABACODEE.md` with note for future `v2.0` spec in `docs/zmux-spec.md`

### Security
- No change to security model — Arena provider respects existing verified TLS context, CSP headers, loopback-only server, token auth, keystore AES-GCM
- ZMUX removal reduces attack surface (no custom shim directory + alias injection to audit)

### Notes
- Test suite: 132 → 137 passing (132 original + 5 arena)
- Pushed to `main` as `37fe823` + `bee0e2a`, also `feature/arena-integration` branch
- Requires APK rebuild to include Arena provider in release

---

## [1.1.0] — 2026-07-25 — Hardening & Zaba Oracle

### Added
- **Zaba Oracle** (`zabacode/core/oracle.py`): offline code intelligence — traceback humanizer (16+ error families), AST-based code review, and a rule-based assistant. Requires no API key and no network. New endpoints `/api/oracle/explain`, `/api/oracle/analyze`; crash explanations render inline in the terminal.
- AI chat now falls back to the Oracle when a provider is keyless or unreachable (opt out with `allow_offline: false`).
- `zabacode/core/net.py`: shared, certificate-verifying TLS context.
- `zabacode/core/keystore.py`: authenticated at-rest encryption for API keys.
- `/api/tls/status` diagnostic endpoint.
- Ace Editor 1.32.4 bundled in `assets/vendor/ace/` — the IDE is now genuinely offline.
- CSP, `X-Content-Type-Options` and `Referrer-Policy` headers.

### Fixed
- **All six AI providers failed with `CERTIFICATE_VERIFY_FAILED`** on Android: p4a ships no readable CA store. Added `certifi`/`openssl` to `buildozer.spec` and routed every request through a verified SSL context.
- `/api/translations` returned HTTP 500 (missing `zabacode.i18n`); replaced.
- Traceback line numbers were offset by the injected `SAFE_INPUT_PATCH` prelude.
- Race condition: `InteractiveSession` is now guarded by an `RLock` under `threads=4`.
- Flask served `assets/` at `/assets`, 404-ing every bundled asset; `static_url_path` pinned.

### Security
- Removed `ssl._create_unverified_context()` fallback in the PyPI installer (MITM → RCE); wheels are now verified against PyPI's published SHA-256.
- API keys no longer encrypted with a hardcoded source-code key.

### Removed
- `zabacode/ui/` — 1,492 lines of unreachable Kivy code superseded by the WebView shell.

### Notes
- Test suite: 77 → 122 passing. Requires an APK rebuild.

## [1.0.0] — 2026-07-21 — WebView Shell + Modular Core

### Added
- WebView Shell (Flask + Waitress @ 127.0.0.1:5000) + Ace Editor bundled offline
- Interactive Execution: `/api/run/interactive/start|output|input|stop` with real-time streaming, STDIN, EXECUTE as STOP
- Multi-Tab Editor with auto-save debounce 500ms, native fallback
- Touch Context Menu floating trigger `•••`
- Theme Engine (10 themes), Plugin Marketplace (12+ plugins, 8 snippets, 5 transform)
- Library Manager (50+ libs, tier/mode, verified TLS + SHA-256)
- 6 AI Providers + Oracle fallback
- Security: X-Zabacode-Token, Keystore, CSP, path validation, subprocess timeout
- Tests: 132 passing
