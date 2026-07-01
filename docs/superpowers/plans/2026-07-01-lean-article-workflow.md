# Lean Article Workflow Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the five-pass article-writing workflow with a quality-preserving three-pass workflow and provide compact machine-readable step routing.

**Architecture:** Keep the existing 11-step state machine and all publishing gates. Move normal-path writing instructions into three compact guides, retain detailed guides as diagnostic references, and add a read-only `context` command that tells an agent exactly what the current step needs without rereading the full workflow.

**Tech Stack:** Python 3 standard library, `unittest`, Markdown workflow documentation.

---

## File map

- Create `docs/editorial-guide.md`: normal-path title, introduction, humanization, ending, and disclaimer rules.
- Create `docs/final-review-guide.md`: independent source-fidelity and boundary review with minimal-edit semantics.
- Modify `docs/writing-guide.md`: compact first-pass draft rules only.
- Modify `docs/workflow.md`: three-pass routing and deterministic Step 3.
- Modify `AGENTS.md`: concise durable rules and on-demand workflow entry.
- Modify `README.md`: describe the three-pass workflow and unchanged outputs.
- Modify `scripts/workflow_state.py`: expose compact read-only context for the current step.
- Modify `tests/test_workflow_state.py`: cover context payloads and CLI JSON.
- Modify `tests/test_validate_workflow.py`: enforce documentation contracts.

### Task 1: Lock the new workflow contract with failing tests

**Files:**
- Modify: `tests/test_validate_workflow.py`
- Modify: `tests/test_workflow_state.py`

- [ ] **Step 1: Add failing documentation contract tests**

Add assertions that `docs/workflow.md` contains `三轮生成文章`, names `内容初稿轮`、`编辑终稿轮`、`独立质检与配图提示词轮`, declares Step 3 a deterministic gate, and routes the normal path to `editorial-guide.md` and `final-review-guide.md`. Assert that README says `三轮写作` and no longer advertises `五轮写作`.

- [ ] **Step 2: Add failing context tests**

Add tests with these expectations:

```python
context = workflow_state.workflow_context(self.root)
self.assertEqual("step_1", context["current_step"])
self.assertEqual(["docs/subtitle-guide.md"], context["guides"])
self.assertIn("source.cleaned.txt", context["outputs"])
```

After marking Step 1 passed, expect Step 2 context to contain exactly the four normal-path guides and the three named rounds. For Step 3, expect no guides and `mode == "deterministic"`.

- [ ] **Step 3: Run the focused tests and verify failure**

Run:

```bash
python3 -m unittest tests.test_workflow_state tests.test_validate_workflow -v
```

Expected: failures for missing `workflow_context`, missing three-pass guide names, and old README wording.

- [ ] **Step 4: Commit the failing tests**

```bash
git add tests/test_workflow_state.py tests/test_validate_workflow.py
git commit -m "test: define lean article workflow contract"
```

### Task 2: Add compact machine-readable workflow context

**Files:**
- Modify: `scripts/workflow_state.py`
- Test: `tests/test_workflow_state.py`

- [ ] **Step 1: Define immutable step routing**

Add a `STEP_CONTEXT` mapping whose entries contain `mode`, `guides`, `inputs`, `outputs`, and `completion_command`. Step 2 must use:

```python
{
    "mode": "three_pass_ai",
    "guides": [
        "docs/writing-guide.md",
        "docs/editorial-guide.md",
        "docs/final-review-guide.md",
        "docs/image-prompt-guide.md",
    ],
    "rounds": ["内容初稿轮", "编辑终稿轮", "独立质检与配图提示词轮"],
    "inputs": ["source.cleaned.txt"],
    "outputs": ["article.md", "cover_prompt.md"],
    "completion_command": "python3 scripts/workflow_state.py pass {article_dir} step_2",
}
```

Step 3 must have `mode: deterministic`, no guides, and the two existing validator commands.

- [ ] **Step 2: Implement `workflow_context`**

Return a deep copy of the current step entry, add `current_step`, `article_dir`, current `status`, and format `{article_dir}` in commands. Do not mutate state or routing constants.

- [ ] **Step 3: Add the `context` CLI command**

Parse `workflow_state.py context <article_dir>` and print UTF-8 JSON with `ensure_ascii=False` and two-space indentation. Unlike mutating commands, do not append `OK` after the JSON.

- [ ] **Step 4: Run focused tests**

```bash
python3 -m unittest tests.test_workflow_state -v
```

Expected: all workflow-state tests pass.

- [ ] **Step 5: Commit routing implementation**

```bash
git add scripts/workflow_state.py tests/test_workflow_state.py
git commit -m "feat: expose compact workflow context"
```

### Task 3: Create the three normal-path writing guides

**Files:**
- Modify: `docs/writing-guide.md`
- Create: `docs/editorial-guide.md`
- Create: `docs/final-review-guide.md`
- Modify: `tests/test_validate_workflow.py`

- [ ] **Step 1: Rewrite `writing-guide.md` for pass one only**

Keep content-type recognition, subtitle-only factual boundaries, Chinese localization, core-judgment structure, concrete openings, and image markers. Remove instructions that ask this pass to generate formal title candidates, humanize the full article, write the ending, or generate image prompts.

- [ ] **Step 2: Create `editorial-guide.md`**

Include the hard requirements currently spread across title, humanizer, ending, and final-writing-check guides: varied title paths, title-source fidelity, fixed frontmatter, natural introduction, no AI templates, paragraph rhythm, author judgment, disclaimer and low-pressure follow prompt. Point to detailed guides only as diagnostic references.

- [ ] **Step 3: Create `final-review-guide.md`**

Define an independent checklist over source and candidate article. Require `PASS` semantics when the article is valid, minimal local edits when invalid, mandatory source reread for health/medical/legal/financial content, atomic promotion to `article.md`, and no full-article output in conversational responses.

- [ ] **Step 4: Run documentation contract tests**

```bash
python3 -m unittest tests.test_validate_workflow.ValidatorTests.test_workflow_documents_define_required_gates tests.test_validate_workflow.ValidatorTests.test_title_guide_prioritizes_source_fidelity_and_varied_paths -v
```

Expected: both tests pass and detailed title-guide compatibility remains intact.

- [ ] **Step 5: Commit the guide layer**

```bash
git add docs/writing-guide.md docs/editorial-guide.md docs/final-review-guide.md tests/test_validate_workflow.py
git commit -m "docs: consolidate normal article writing into three passes"
```

### Task 4: Replace the workflow entry and public documentation

**Files:**
- Modify: `AGENTS.md`
- Modify: `docs/workflow.md`
- Modify: `README.md`
- Test: `tests/test_validate_workflow.py`

- [ ] **Step 1: Make AGENTS concise**

Keep the role and health boundary. Replace `@docs/workflow.md` with an instruction to read `docs/workflow.md` only for article-production tasks and to use `workflow_state.py context` when resuming an existing article.

- [ ] **Step 2: Rewrite workflow routing**

Preserve global hard gates, file contracts, state commands, Step 7 approval, publication rules, and final cleanup. Replace five Step 2 rounds with the three rounds. Make Step 3 run only article and prompt validators and then pass the state.

- [ ] **Step 3: Update README**

Describe three-pass writing and deterministic Step 3. Keep all final assets, skill dependencies, image generation, WeChat draft creation, and Xiaohongshu outputs unchanged.

- [ ] **Step 4: Run documentation tests**

```bash
python3 -m unittest tests.test_validate_workflow -v
```

Expected: all validator tests pass.

- [ ] **Step 5: Commit workflow documentation**

```bash
git add AGENTS.md docs/workflow.md README.md tests/test_validate_workflow.py
git commit -m "docs: switch article production to three-pass workflow"
```

### Task 5: Full regression and context-size verification

**Files:**
- Modify if needed: files changed in Tasks 1-4

- [ ] **Step 1: Run the complete Python test suite**

```bash
python3 -m unittest discover -s tests -v
```

Expected: all tests pass.

- [ ] **Step 2: Run project validators**

```bash
python3 scripts/validate_workflow.py skills skills.lock.json
python3 scripts/workflow_state.py context /tmp/nonexistent-article
```

Expected: skill validation prints `OK`; context reports a missing state error and exits non-zero without modifying files.

- [ ] **Step 3: Verify documentation consistency and size**

```bash
rg -n "五轮|标题与导语复核|@docs/workflow" AGENTS.md README.md docs/workflow.md docs/writing-guide.md docs/editorial-guide.md docs/final-review-guide.md
wc -c AGENTS.md docs/workflow.md docs/writing-guide.md docs/editorial-guide.md docs/final-review-guide.md
git diff --check
```

Expected: no stale normal-path wording, no whitespace errors, and the normal-path instruction set is materially smaller than the former workflow plus five Step 2 guides.

- [ ] **Step 4: Commit any final consistency fixes**

```bash
git add AGENTS.md README.md docs scripts tests
git commit -m "chore: verify lean article workflow"
```
