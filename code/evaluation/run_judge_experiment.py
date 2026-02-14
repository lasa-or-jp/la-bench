#!/usr/bin/env python3
"""
LA-Bench 2025: LLM-as-a-Judge Experiment
正解outputを3つのLLM評価器 × 3種類の評価プロンプト × 5回で採点し、
スコアの分布・プロンプト間差異・評価器依存性・ばらつきを分析する。

Usage:
    python code/evaluation/run_judge_experiment.py --max-concurrent 15
    python code/evaluation/run_judge_experiment.py --aggregate-only
"""

import argparse
import asyncio
import json
import logging
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import pandas as pd
from dotenv import load_dotenv
from openai import AsyncOpenAI
from pydantic import BaseModel, Field
from tenacity import retry, stop_after_attempt, wait_exponential

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Project root (resolve relative to this file)
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# ---------------------------------------------------------------------------
# Data structures (extracted from notebooks/Evaluation.ipynb Cell 4)
# ---------------------------------------------------------------------------

@dataclass
class Step:
    id: int
    text: str

@dataclass
class ReferenceEntry:
    id: int
    text: str

@dataclass
class ExampleInput:
    instruction: str
    mandatory_objects: Set[str] = field(default_factory=set)
    source_protocol_steps: List[Step] = field(default_factory=list)
    expected_final_states: Set[str] = field(default_factory=set)
    references: List[ReferenceEntry] = field(default_factory=list)

@dataclass
class ExampleOutput:
    procedure_steps: List[Step] = field(default_factory=list)

@dataclass
class Measurement:
    specific_criteria: Dict[str, int] = field(default_factory=dict)

@dataclass
class ExampleSample:
    id: str
    input: ExampleInput
    output: ExampleOutput
    measurement: Optional[Measurement] = None


def _to_set(x):
    return set(x) if isinstance(x, (list, set, tuple)) else set()

def _to_list(x):
    return list(x) if isinstance(x, (list, set, tuple)) else (x if isinstance(x, list) else [])

def _to_steps(x) -> List[Step]:
    steps: List[Step] = []
    arr = _to_list(x)
    if not arr:
        return steps
    if isinstance(arr[0], dict):
        for it in arr:
            try:
                sid = int(it.get("id", len(steps) + 1))
            except Exception:
                sid = len(steps) + 1
            steps.append(Step(id=sid, text=str(it.get("text", "")).strip()))
    else:
        for idx, s in enumerate(arr, start=1):
            steps.append(Step(id=idx, text=str(s).strip()))
    return steps

def _to_references(x) -> List[ReferenceEntry]:
    refs: List[ReferenceEntry] = []
    arr = _to_list(x)
    if not arr:
        return refs
    if isinstance(arr[0], dict):
        for it in arr:
            try:
                rid = int(it.get("id", len(refs) + 1))
            except Exception:
                rid = len(refs) + 1
            refs.append(ReferenceEntry(id=rid, text=str(it.get("text", "")).strip()))
    else:
        for idx, ref in enumerate(arr, start=1):
            refs.append(ReferenceEntry(id=idx, text=str(ref).strip()))
    return refs


def parse_sample(obj: Dict[str, Any]) -> ExampleSample:
    sid = obj.get("id") or obj.get("sample_id") or "unknown"
    i = obj.get("input", {})
    o = obj.get("output", {})
    m = obj.get("measurement", {})

    sc_raw = m.get("specific_criteria", {})
    sc: Dict[str, int] = {}
    if isinstance(sc_raw, dict):
        for k, v in sc_raw.items():
            try:
                sc[str(k)] = int(v)
            except Exception:
                pass
    elif isinstance(sc_raw, list):
        for it in sc_raw:
            try:
                k = it.get("item")
                v = int(it.get("score", 0))
                if k:
                    sc[str(k)] = v
            except Exception:
                pass

    return ExampleSample(
        id=str(sid),
        input=ExampleInput(
            instruction=str(i.get("instruction", "")).strip(),
            mandatory_objects=_to_set(i.get("mandatory_objects", [])),
            source_protocol_steps=_to_steps(i.get("source_protocol_steps", [])),
            expected_final_states=_to_set(i.get("expected_final_states", [])),
            references=_to_references(i.get("references", [])),
        ),
        output=ExampleOutput(
            procedure_steps=_to_steps(o.get("procedure_steps", []))
        ),
        measurement=Measurement(specific_criteria=sc) if sc else None,
    )


def load_example_jsonl(path: str) -> List[ExampleSample]:
    samples = []
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"JSONL not found: {p}")
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        obj = json.loads(line)
        samples.append(parse_sample(obj))
    return samples


# ---------------------------------------------------------------------------
# JudgeOutput schema (from Cell 7)
# ---------------------------------------------------------------------------

class JudgeOutput(BaseModel):
    general_score: float = Field(ge=0, le=5)
    specific_score: float = Field(ge=0, le=5)
    final_score: float = Field(ge=0, le=10)
    general_reason: str
    specific_matches: List[str] = []
    notes: Optional[str] = None


# ---------------------------------------------------------------------------
# 3 prompt variants (from Cell 8)
# ---------------------------------------------------------------------------

STRICT_CHECKLIST_PROMPT = """あなたは生命科学実験の専門家であり、厳格な採点者です。与えられた Input（instruction, mandatory_objects, source_protocol_steps, expected_final_states, references）と、参加者の Output（procedure_steps）および問題ごとの specific_criteria を評価し、JudgeOutput のみを返してください。出力は以下のフィールドに完全準拠します：general_score, specific_score, final_score, general_reason, specific_matches, notes。余分なテキストは一切含めないでください。

<評価方針>
- 決定は二値（OK/NG）。不確実な場合は NG（無加点）。推測・補完はしない。
- 根拠は参加者 Output の記述のみから引用し、「」で囲む。Input は照合にのみ用い、引用しない。
- general_reason は必ず5行。「1)～5) 判定（OK/NG） | 根拠 | 引用」。OKの数はgeneral_scoreと一致させる。
- final_score = general_score + specific_score。整数。範囲 0–10。
- 過度の安全性の上限（cap）はgeneral_score算出後に適用し、notesに簡潔に記載。ない場合は空文字。

<手順>
1. Input から必須パラメータ・物品・手順論理・期待最終状態を抽出。
2. Output を走査し、操作可能な単位（µL/mL, mg/g 等）・器具明示・順序/分岐・計算整合性の有無を確認。
3. 5つの共通採点基準を独立に判定（OK/NG）。根拠は Output の具体フレーズを引用。
4. specific_criteria を満たす箇所のみ specific_matches に引用を記録し、該当点を加算。曖昧なら0。
5. 過度の安全性の条件に該当する場合、general_score を最大2に cap。notes に「cap理由」を短く記載。
6. JudgeOutput を返す。所定フィールド以外は出力しない。

# 共通採点基準（general_score、最大5点）
## 加点項目（各1点）
1. 「実験指示」におけるパラメータを、すべて誤りなく反映している。単なる再掲は認めない。
2. 「使用する物品」の要素が、すべて 誤りなく反映している。曖昧な総称のみは認めない。
3. 「元プロトコルの手順」の順序や分岐条件の論理構造を矛盾なく反映している。
4. 実行することで、「期待される最終状態」を得られる。論理的破綻や計算ミスがない。
5. 明示されていない部分を適切に補完している。記述が具体的である。

## 減点項目（各-1点）
1. 過度に不自然な日本語やハルシネーションを含む。
2. 計算ミスがある。
3. 手順に矛盾がある。

## 過度の安全性
以下のように過度に安全側に倒した回答の場合、共通採点基準（general_score）の合計点を最大2点とする。
- 入力の手順をそのまま出力として記載している。
- 出典の情報を適切な取捨選択なく記載している。
- 実験指示や元プロトコルに反して中間物を必要量の100倍用意するなど、みだりに実験条件を安全側に倒している。
### 適用例
- 採点結果が1点の場合 → 1点のまま
- 採点結果が3点の場合 → 2点に制限
- 採点結果が5点の場合 → 2点に制限

# 個別採点基準（specific_score、最大5点）
問題ごとに設定された採点項目に基づいて加点する。採点項目は以下のような観点で設定されている。
- 出題意図への適合性
- 安全性の考慮
- コスト効率
- 作業効率
- 実験精度向上への貢献
生成された実験手順が採点項目の条件を明示的に満たす場合のみ、該当する score を加点し、根拠となるフレーズをspecific_matchesに記録する。曖昧な記述は加点しない。

# 実験手順の詳細度に関する必須要件
実験手順（procedure_steps）は、単にプロトコルを構造化するだけではなく、当該分野の学部レベルのトレーニングを受けた人が読んで誤解なく実行できることを目指してください。そのために、以下の点を遵守してください。
- すべての条件が明示化されている。
- 不完全な記述が完成されている。
- 実行時に使用される具体的な数値が計算されている（µL/mL, mg/g など実際に操作できる単位。pmol, ng 等のみの提示は不可。換算して体積や質量を示した場合のみ可）。
- 操作対象や器具、装置など対象物が明示化されている。"""

GPT_5_TUNED_AGENTIC_JUDGE_PROMPT = """You are a life‑science expert and a strict grader. Evaluate the participant's Output (procedure_steps) against the competition Input (instruction, mandatory_objects, source_protocol_steps, expected_final_states, references) and problem‑specific criteria. Return ONLY the JudgeOutput fields: general_score, specific_score, final_score, general_reason, specific_matches, notes. No extra text.

<persistence>
- Operate autonomously until evaluation is fully complete. Do NOT ask for clarification.
- Under uncertainty, bias to NG (no credit); proceed and document decisions.
</persistence>

<tool_preamble>
- Rephrase the goal briefly: "Score Output against Input using 5 general checks + specific criteria."
- Plan: (1) Extract Input requirements; (2) parse Output; (3) apply five binary checks with quoted evidence; (4) apply over‑safety cap if triggered; (5) collect specific_matches; (6) compute scores; (7) emit JudgeOutput.
- Stop when: all five checks decided; specific_matches compiled; schema validated.
</tool_preamble>

<steering>
- reasoning_effort: medium (use minimal for latency‑sensitive runs).
- verbosity: low. No commentary beyond required fields.
- Determinism: low temperature; avoid emitting any fields beyond schema.
</steering>

<general_checks_definition>
1) Instruction parameters must be fully reflected AND operationalized (units/instruments). Restatement alone → NG.
2) Mandatory objects: ALL items concretely used; umbrella categories alone → NG.
3) Protocol logic: preserve order, branches, dependencies from source_protocol_steps without contradiction.
4) Achievability: steps logically yield expected_final_states; no calculation or logical errors.
5) Completeness/specificity: fill gaps appropriately; actionable units (µL/mL, mg/g) and instruments present. Non‑operational units alone (e.g., only ng/pmol) → NG unless converted.
</general_checks_definition>

<evidence_rules>
- Quote ONLY from Output for general_reason and specific_matches, wrapped in 「」.
- Use Input for alignment checks only; do not quote it.
- If Output lacks necessary evidence, mark NG; do not invent.
</evidence_rules>

<over_safety_cap>
Apply after computing general_score; cap to max 2 if:
- Output copies Input steps verbatim without operationalization.
- Output pastes references/external content without selection.
- Output inflates quantities (e.g., ×100 intermediates) contrary to Input/protocol without justification.
Record cap briefly in notes; otherwise notes is empty.
</over_safety_cap>

<format_strictness>
- Emit ONLY: general_score, specific_score, final_score, general_reason (exactly 5 lines "1)…5) 判定（OK/NG） | 根拠 | 引用"), specific_matches (list of quoted Output phrases), notes.
- Ensure OK count equals general_score; final_score equals sum.
</format_strictness>

# 共通採点基準（general_score、最大5点）
## 加点項目（各1点）
1. 「実験指示」におけるパラメータを、すべて誤りなく反映している。単なる再掲は認めない。
2. 「使用する物品」の要素が、すべて 誤りなく反映している。曖昧な総称のみは認めない。
3. 「元プロトコルの手順」の順序や分岐条件の論理構造を矛盾なく反映している。
4. 実行することで、「期待される最終状態」を得られる。論理的破綻や計算ミスがない。
5. 明示されていない部分を適切に補完している。記述が具体的である。

## 減点項目（各-1点）
1. 過度に不自然な日本語やハルシネーションを含む。
2. 計算ミスがある。
3. 手順に矛盾がある。

## 過度の安全性
以下のように過度に安全側に倒した回答の場合、共通採点基準（general_score）の合計点を最大2点とする。
- 入力の手順をそのまま出力として記載している。
- 出典の情報を適切な取捨選択なく記載している。
- 実験指示や元プロトコルに反して中間物を必要量の100倍用意するなど、みだりに実験条件を安全側に倒している。
### 適用例
- 採点結果が1点の場合 → 1点のまま
- 採点結果が3点の場合 → 2点に制限
- 採点結果が5点の場合 → 2点に制限

# 個別採点基準（specific_score、最大5点）
問題ごとに設定された採点項目に基づいて加点する。採点項目は以下のような観点で設定されている。
- 出題意図への適合性
- 安全性の考慮
- コスト効率
- 作業効率
- 実験精度向上への貢献
生成された実験手順が採点項目の条件を明示的に満たす場合のみ、該当する score を加点し、根拠となるフレーズをspecific_matchesに記録する。曖昧な記述は加点しない。

# 実験手順の詳細度に関する必須要件
実験手順（procedure_steps）は、単にプロトコルを構造化するだけではなく、当該分野の学部レベルのトレーニングを受けた人が読んで誤解なく実行できることを目指してください。そのために、以下の点を遵守してください。
- すべての条件が明示化されている。
- 不完全な記述が完成されている。
- 実行時に使用される具体的な数値が計算されている（µL/mL, mg/g など実際に操作できる単位。pmol, ng 等のみの提示は不可。換算して体積や質量を示した場合のみ可）。
- 操作対象や器具、装置など対象物が明示化されている。"""

CONTRASTIVE_DUAL_PASS_PROMPT = """あなたは生命科学分野の「対照型（コントラスト）デュアルパス」採点者です。Input（instruction, mandatory_objects, source_protocol_steps, expected_final_states, references）と参加者 Output（procedure_steps）、specific_criteria を評価し、JudgeOutput のみを返してください。余分な出力は厳禁です。

<persistence>
- 相談や確認は行わず、自律的に評価を完了する。
- 不確実な場合は NG（無加点）。推測はしない。判断理由は Output の引用で示す。
</persistence>

<評価フレーム>
- Pass A（Failure‑first）: 各共通基準について、NG となる根拠（欠落したパラメータ、未使用物品、順序/分岐の破綻、計算/論理エラー、操作不能な単位や器具の不在）を、Output からのみ抽出・引用。
- Pass B（Evidence‑for‑credit）: 各基準のOK条件を満たす直接的な証拠（操作可能な単位、具体的器具、全物品の使用、分岐維持、最終状態の達成）を Output からのみ抽出・引用。
- 衝突解決: Pass A が有効な失敗理由を示した場合、Pass B がそれを完全に打ち消す明確な引用証拠を示すときのみ OK。曖昧は NG。

<形式・算定>
- general_reason は必ず5行で「1)～5) 判定（OK/NG） | 根拠 | 引用」。引用は「」で囲む。
- specific_matches は、満たした specific_criteria ごとに Output の該当フレーズのみを列挙。曖昧なら追加しない。
- final_score = general_score + specific_score。過度の安全性 cap は general_score 算出後に適用し、notes に簡潔に記載。なければ空文字。
- 所定フィールド（general_score, specific_score, final_score, general_reason, specific_matches, notes）以外は出力禁止。

# 共通採点基準（general_score、最大5点）
## 加点項目（各1点）
1. 「実験指示」におけるパラメータを、すべて誤りなく反映している。単なる再掲は認めない。
2. 「使用する物品」の要素が、すべて 誤りなく反映している。曖昧な総称のみは認めない。
3. 「元プロトコルの手順」の順序や分岐条件の論理構造を矛盾なく反映している。
4. 実行することで、「期待される最終状態」を得られる。論理的破綻や計算ミスがない。
5. 明示されていない部分を適切に補完している。記述が具体的である。

## 減点項目（各-1点）
1. 過度に不自然な日本語やハルシネーションを含む。
2. 計算ミスがある。
3. 手順に矛盾がある。

## 過度の安全性
以下のように過度に安全側に倒した回答の場合、共通採点基準（general_score）の合計点を最大2点とする。
- 入力の手順をそのまま出力として記載している。
- 出典の情報を適切な取捨選択なく記載している。
- 実験指示や元プロトコルに反して中間物を必要量の100倍用意するなど、みだりに実験条件を安全側に倒している。
### 適用例
- 採点結果が1点の場合 → 1点のまま
- 採点結果が3点の場合 → 2点に制限
- 採点結果が5点の場合 → 2点に制限

# 個別採点基準（specific_score、最大5点）
問題ごとに設定された採点項目に基づいて加点する。採点項目は以下のような観点で設定されている。
- 出題意図への適合性
- 安全性の考慮
- コスト効率
- 作業効率
- 実験精度向上への貢献
生成された実験手順が採点項目の条件を明示的に満たす場合のみ、該当する score を加点し、根拠となるフレーズをspecific_matchesに記録する。曖昧な記述は加点しない。

# 実験手順の詳細度に関する必須要件
実験手順（procedure_steps）は、単にプロトコルを構造化するだけではなく、当該分野の学部レベルのトレーニングを受けた人が読んで誤解なく実行できることを目指してください。そのために、以下の点を遵守してください。
- すべての条件が明示化されている。
- 不完全な記述が完成されている。
- 実行時に使用される具体的な数値が計算されている（µL/mL, mg/g など実際に操作できる単位。pmol, ng 等のみの提示は不可。換算して体積や質量を示した場合のみ可）。
- 操作対象や器具、装置など対象物が明示化されている。"""

PROMPT_VARIANTS = {
    "strict_checklist": STRICT_CHECKLIST_PROMPT,
    "gpt5_tuned": GPT_5_TUNED_AGENTIC_JUDGE_PROMPT,
    "contrastive_dual_pass": CONTRASTIVE_DUAL_PASS_PROMPT,
}


# ---------------------------------------------------------------------------
# Helpers (from Cell 8)
# ---------------------------------------------------------------------------

def compose_judge_user_content(sample: ExampleSample, steps: List[Step]) -> str:
    parts: List[str] = []
    parts.append(f"# Input\n## 実験指示 (instruction)\n{sample.input.instruction}")
    if sample.input.mandatory_objects:
        parts.append("\n## 使用する物品 (mandatory_objects)")
        for it in sorted(sample.input.mandatory_objects):
            parts.append(f"- {it}")
    if sample.input.source_protocol_steps:
        parts.append("\n## 元プロトコルの手順（参考）(source_protocol_steps)")
        for st in sample.input.source_protocol_steps:
            parts.append(f"- {st.id}. {st.text}")
    if sample.input.expected_final_states:
        parts.append("\n## 期待される最終状態 (expected_final_states)")
        for fs in sorted(sample.input.expected_final_states):
            parts.append(f"- {fs}")
    if sample.input.references:
        parts.append("\n## 参考文献 (references)")
        for ref in sample.input.references:
            parts.append(f"- [{ref.id}] {ref.text}")
    parts.append("\n# 生成された実験手順（Output）")
    for stp in steps:
        parts.append(f"- {stp.id}. {stp.text}")
    parts.append("\n# specific_criteria")
    if sample.measurement and sample.measurement.specific_criteria:
        for item, sc in sample.measurement.specific_criteria.items():
            parts.append(f"- ({int(sc)}点): {item}")
    else:
        parts.append("- なし")
    return "\n".join(parts)


def build_judge_messages_with_prompt(
    prompt_key: str, sample: ExampleSample, steps: List[Step]
) -> list[dict]:
    system = PROMPT_VARIANTS[prompt_key]
    user = compose_judge_user_content(sample, steps)
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]


# ---------------------------------------------------------------------------
# Gold standard conversion
# ---------------------------------------------------------------------------

def gold_standard_as_generated(sample: ExampleSample) -> dict:
    """Convert the gold-standard output into the dict format expected by judge."""
    return {
        "id": sample.id,
        "procedure_steps": [
            {"id": s.id, "text": s.text} for s in sample.output.procedure_steps
        ],
    }


# ---------------------------------------------------------------------------
# Experiment configuration
# ---------------------------------------------------------------------------

MODELS = [
    "gpt-5-nano-2025-08-07",
    "gpt-5-mini-2025-08-07",
    "gpt-5-2025-08-07",
]

PROMPT_KEYS = ["strict_checklist", "gpt5_tuned", "contrastive_dual_pass"]

NUM_RUNS = 5
TEMPERATURE = 1.0

OUTPUT_DIR = PROJECT_ROOT / "outputs" / "judge_experiment"


# ---------------------------------------------------------------------------
# Checkpoint / persistence
# ---------------------------------------------------------------------------

def run_csv_path(model: str, prompt_key: str, run_id: int) -> Path:
    return OUTPUT_DIR / f"run_{model}_{prompt_key}_{run_id}.csv"


def load_checkpoint() -> set:
    """Return set of (model, prompt_key, run_id) already completed."""
    completed = set()
    if not OUTPUT_DIR.exists():
        return completed
    for csv_file in OUTPUT_DIR.glob("run_*.csv"):
        name = csv_file.stem  # run_model_prompt_runid
        parts = name.split("_", 1)[1]  # model_prompt_runid
        # Parse: last part is run_id, second-to-last set is prompt_key
        # Format: run_{model}_{prompt_key}_{run_id}
        for pk in PROMPT_KEYS:
            marker = f"_{pk}_"
            if marker in parts:
                idx = parts.index(marker)
                model_part = parts[:idx]
                run_part = parts[idx + len(marker):]
                try:
                    rid = int(run_part)
                    df = pd.read_csv(csv_file)
                    if len(df) == 10:  # all samples completed
                        completed.add((model_part, pk, rid))
                except (ValueError, Exception):
                    pass
                break
    return completed


def save_run_result(
    model: str, prompt_key: str, run_id: int, rows: List[dict]
) -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    path = run_csv_path(model, prompt_key, run_id)
    df = pd.DataFrame(rows)
    df.to_csv(path, index=False, encoding="utf-8-sig")
    return path


# ---------------------------------------------------------------------------
# Async judging
# ---------------------------------------------------------------------------

@retry(stop=stop_after_attempt(5), wait=wait_exponential(min=2, max=60))
async def judge_single_sample(
    client: AsyncOpenAI,
    model: str,
    prompt_key: str,
    sample: ExampleSample,
    steps: List[Step],
    semaphore: asyncio.Semaphore,
) -> dict:
    """Judge a single sample with retry."""
    msgs = build_judge_messages_with_prompt(prompt_key, sample, steps)
    async with semaphore:
        completion = await client.chat.completions.parse(
            model=model,
            messages=msgs,
            temperature=TEMPERATURE,
            response_format=JudgeOutput,
        )
    parsed: JudgeOutput = completion.choices[0].message.parsed  # type: ignore
    return {
        "sample_id": sample.id,
        "general_score": float(parsed.general_score),
        "specific_score": float(parsed.specific_score),
        "final_score": float(parsed.final_score),
        "general_reason": parsed.general_reason,
        "specific_matches": json.dumps(
            list(parsed.specific_matches), ensure_ascii=False
        ),
        "notes": parsed.notes or "",
    }


async def run_single_evaluation(
    client: AsyncOpenAI,
    model: str,
    prompt_key: str,
    run_id: int,
    samples: List[ExampleSample],
    generated_map: Dict[str, List[Step]],
    semaphore: asyncio.Semaphore,
) -> List[dict]:
    """Run one (model, prompt, run) over all 10 samples in parallel."""
    tasks = []
    for sm in samples:
        steps = generated_map.get(sm.id, [])
        tasks.append(
            judge_single_sample(client, model, prompt_key, sm, steps, semaphore)
        )
    results = await asyncio.gather(*tasks, return_exceptions=True)
    rows = []
    for i, r in enumerate(results):
        if isinstance(r, Exception):
            logger.error(
                "Failed: model=%s prompt=%s run=%d sample=%s: %s",
                model, prompt_key, run_id, samples[i].id, r,
            )
            rows.append({
                "sample_id": samples[i].id,
                "general_score": 0.0,
                "specific_score": 0.0,
                "final_score": 0.0,
                "general_reason": "",
                "specific_matches": "[]",
                "notes": f"error: {r}",
            })
        else:
            rows.append(r)
    return rows


async def run_all_evaluations(
    samples: List[ExampleSample],
    generated_map: Dict[str, List[Step]],
    max_concurrent: int = 15,
) -> None:
    """Run all (model × prompt × run) combinations."""
    load_dotenv(PROJECT_ROOT / ".env")
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        # .env may contain the raw key without variable name
        env_path = PROJECT_ROOT / ".env"
        if env_path.exists():
            raw = env_path.read_text().strip()
            if raw.startswith("sk-"):
                api_key = raw
    client = AsyncOpenAI(api_key=api_key)
    semaphore = asyncio.Semaphore(max_concurrent)

    completed = load_checkpoint()
    logger.info("Checkpoint: %d runs already completed", len(completed))

    # Build list of pending tasks
    pending = []
    for model in MODELS:
        for pk in PROMPT_KEYS:
            for run_id in range(1, NUM_RUNS + 1):
                if (model, pk, run_id) in completed:
                    logger.info("Skip (already done): %s / %s / run %d", model, pk, run_id)
                    continue
                pending.append((model, pk, run_id))

    total = len(pending)
    logger.info("Pending evaluations: %d / %d total", total, len(MODELS) * len(PROMPT_KEYS) * NUM_RUNS)

    done_count = 0
    # Run in parallel batches grouped by model to respect rate limits
    async def run_one(model: str, pk: str, run_id: int):
        nonlocal done_count
        rows = await run_single_evaluation(
            client, model, pk, run_id, samples, generated_map, semaphore
        )
        path = save_run_result(model, pk, run_id, rows)
        done_count += 1
        logger.info(
            "[%d/%d] Saved: %s (model=%s, prompt=%s, run=%d)",
            done_count, total, path.name, model, pk, run_id,
        )

    # Launch all at once — semaphore handles concurrency
    await asyncio.gather(
        *(run_one(m, p, r) for m, p, r in pending)
    )


# ---------------------------------------------------------------------------
# Aggregation and statistics
# ---------------------------------------------------------------------------

def aggregate_results() -> pd.DataFrame:
    """Combine all per-run CSVs into a single DataFrame."""
    all_rows = []
    for csv_file in sorted(OUTPUT_DIR.glob("run_*.csv")):
        name = csv_file.stem
        parts = name.split("_", 1)[1]
        model = prompt_key = ""
        run_id = 0
        for pk in PROMPT_KEYS:
            marker = f"_{pk}_"
            if marker in parts:
                idx = parts.index(marker)
                model = parts[:idx]
                run_id_str = parts[idx + len(marker):]
                try:
                    run_id = int(run_id_str)
                except ValueError:
                    continue
                prompt_key = pk
                break
        if not model:
            continue
        df = pd.read_csv(csv_file)
        df["model"] = model
        df["prompt_key"] = prompt_key
        df["run_id"] = run_id
        all_rows.append(df)
    if not all_rows:
        raise RuntimeError("No result CSVs found in " + str(OUTPUT_DIR))
    combined = pd.concat(all_rows, ignore_index=True)
    combined.to_csv(OUTPUT_DIR / "all_results.csv", index=False, encoding="utf-8-sig")
    logger.info("Aggregated %d rows → all_results.csv", len(combined))
    return combined


def compute_summary_statistics(df: pd.DataFrame) -> dict:
    """Compute statistics for paper Section 3."""
    summary = {}

    # --- Section 3.1: Score distribution ---
    summary["n"] = df["sample_id"].nunique()
    summary["overall_mean"] = round(float(df["final_score"].mean()), 2)
    summary["overall_std"] = round(float(df["final_score"].std()), 2)
    # Per-sample mean, then range
    per_sample = df.groupby("sample_id")["final_score"].mean()
    summary["sample_mean_min"] = round(float(per_sample.min()), 2)
    summary["sample_mean_max"] = round(float(per_sample.max()), 2)
    summary["general_mean"] = round(float(df["general_score"].mean()), 2)
    summary["specific_mean"] = round(float(df["specific_score"].mean()), 2)

    # --- Section 3.2: Prompt differences ---
    prompt_means = df.groupby("prompt_key")["final_score"].mean()
    summary["strict_checklist_mean"] = round(float(prompt_means.get("strict_checklist", 0)), 2)
    summary["gpt5_tuned_mean"] = round(float(prompt_means.get("gpt5_tuned", 0)), 2)
    summary["contrastive_dual_pass_mean"] = round(float(prompt_means.get("contrastive_dual_pass", 0)), 2)
    # Max prompt difference per sample
    prompt_sample = df.groupby(["sample_id", "prompt_key"])["final_score"].mean().unstack()
    prompt_diff = prompt_sample.max(axis=1) - prompt_sample.min(axis=1)
    summary["max_prompt_diff"] = round(float(prompt_diff.max()), 2)

    # --- Section 3.3: Model dependency ---
    model_means = df.groupby("model")["final_score"].mean()
    model_diff = model_means.max() - model_means.min()
    summary["model_mean_diff"] = round(float(model_diff), 2)
    # Per-model means for reference
    for m in MODELS:
        key = m.replace("-", "_").replace(".", "_")
        summary[f"model_{key}_mean"] = round(float(model_means.get(m, 0)), 2)

    # Save
    summary_path = OUTPUT_DIR / "summary.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    logger.info("Summary saved → %s", summary_path)

    # Print
    print("\n" + "=" * 60)
    print("SUMMARY STATISTICS")
    print("=" * 60)
    for k, v in summary.items():
        print(f"  {k}: {v}")
    print("=" * 60)

    return summary


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def validate_results(df: pd.DataFrame) -> None:
    """Validate all scores are in valid ranges."""
    errors = []
    if (df["final_score"] < 0).any() or (df["final_score"] > 10).any():
        errors.append("final_score out of [0, 10] range")
    if (df["general_score"] < 0).any() or (df["general_score"] > 5).any():
        errors.append("general_score out of [0, 5] range")
    if (df["specific_score"] < 0).any() or (df["specific_score"] > 5).any():
        errors.append("specific_score out of [0, 5] range")
    # Check final = general + specific (allow ±0.01 floating point)
    diff = (df["final_score"] - (df["general_score"] + df["specific_score"])).abs()
    if (diff > 0.01).any():
        n_bad = (diff > 0.01).sum()
        errors.append(f"final_score != general + specific for {n_bad} rows")
    if errors:
        for e in errors:
            logger.warning("Validation: %s", e)
    else:
        logger.info("Validation: all scores OK")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="LLM-as-a-Judge experiment")
    parser.add_argument(
        "--aggregate-only",
        action="store_true",
        help="Skip API calls, aggregate existing results only",
    )
    parser.add_argument(
        "--max-concurrent",
        type=int,
        default=15,
        help="Max concurrent API requests (default: 15)",
    )
    parser.add_argument(
        "--data-path",
        type=str,
        default=str(PROJECT_ROOT / "data" / "public_test" / "public_test.jsonl"),
        help="Path to the JSONL dataset",
    )
    args = parser.parse_args()

    # Load data
    samples = load_example_jsonl(args.data_path)
    logger.info("Loaded %d samples from %s", len(samples), args.data_path)

    # Build generated_map from gold standard
    generated = [gold_standard_as_generated(s) for s in samples]
    generated_map: Dict[str, List[Step]] = {
        g["id"]: [Step(id=it["id"], text=it["text"]) for it in g["procedure_steps"]]
        for g in generated
    }

    if not args.aggregate_only:
        asyncio.run(
            run_all_evaluations(samples, generated_map, args.max_concurrent)
        )

    # Aggregate
    df = aggregate_results()
    validate_results(df)
    compute_summary_statistics(df)


if __name__ == "__main__":
    main()
