---
title: Graveyard Shift
emoji: 🕯️
colorFrom: purple
colorTo: green
sdk: docker
app_port: 7860
license: apache-2.0
---

# Graveyard Shift

**A séance for your codebase’s deleted functions.**

Explore an original miniature Git history, question a ghost with an open-weight code model, expose a renamed function, and run a regression that fails before recovering an old fix.

[Live app](https://shivampandit-graveyard-shift.hf.space/) · [Source](https://github.com/panditshivam/graveyard-shift)

## What actually runs

- Git + Python AST extraction reads four authored commits. Two old function names disappear: one has an exact normalized-body match under a new name; the other is removed during a rewrite.
- Qwen2.5-Coder-1.5B-Instruct selects one of the supplied evidence records using constrained generation on the server CPU. Its immutable revision is `2e1fd397ee46e1388853d2af2c993145b0f1098a`. It receives facts and snippets from the selected function, deletion commit and current body. Its generated selection is constrained to E0 (not established), E1, E2 or E3. The visible answer is the exact selected record text, not model-written prose. Greetings are scripted.
- Only an existing record or explicit unknown selection can be returned. The model can still select an irrelevant record; this is not a semantic accuracy guarantee. Read the exact source. Developer intent is not established by deletion alone.
- The ritual executes our fixed authored regression fixture in fresh temporary directories. The rewrite has two failing cases (one assertion failure and one error); recovering the final-attempt boundary makes all three tests pass. Actual return codes and output are displayed.
- Motion and original synthesized sound are optional. The quiet route preserves the experience. A device-local speech voice is offered only when the browser reports an English local voice; it is not ElevenLabs.

The UI shows actual server job state, events and elapsed time. It does not animate a fabricated model response or substitute a timer for a test result.

## Run locally

Use Python 3.12, Git and enough memory/disk for the model and its runtime. The published hosted configuration is CPU Basic; model loading and CPU generation can be slow. No external inference API key is needed.

```sh
python -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m unittest -v test_core
.venv/bin/python server.py
```

Open `http://localhost:7860`. The first model request downloads the pinned weights unless already cached. The Docker image downloads them during its build.

The read-only CLI can inspect a local Python repository without importing its code:

```sh
python history.py /path/to/repository --limit 100
```

Keep that output private when inspecting private history. The CLI follows only a bounded first-parent history, not every branch. Renames with changed bodies, ambiguous copies, splits/merges and unsupported syntax can remain unresolved. A body match is a heuristic lineage candidate, not a universal identity proof.

## Public data and execution boundary

The hosted app accepts no repository uploads, patches, URLs to fetch, shell commands or arbitrary executable code. It uses only the authored fixture from `fixture.py`. Those fixed commits and timestamps are demonstration data, not actual maintainer history. Test execution uses isolated temporary directories, a stripped environment, Python isolation flags and a wall-time bound. It is **not** an OS security sandbox and does not establish safe execution of untrusted repositories.

Questions go to the hosting server. Do not paste private code. The app holds bounded jobs in memory; restarts lose them. No partner telemetry or cloud voice service is configured. The stylesheet loads Google Fonts; this hosted app is not claimed to be offline. The local history CLI itself does not call the model or network.

## Open components and credits

Application and original fixture: Apache-2.0, copyright panditshivam. Model weights: [Qwen2.5-Coder-1.5B-Instruct](https://huggingface.co/Qwen/Qwen2.5-Coder-1.5B-Instruct), Apache-2.0. Inference: Hugging Face Transformers and PyTorch. Git and Python provide inspectable source-history extraction and tests. Font families DM Sans and Space Mono are served by Google Fonts under their respective open font licences.

This project does not claim Gemma, TabPFN, Tinker, Temporal, Mastra, Arduino, DigitalOcean or integrations from Ghostlight. GitHub Actions checks this repository’s authored fixture and syntax; it is not a claim that Copilot wrote the code.
