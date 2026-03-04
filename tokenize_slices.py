#!/usr/bin/env python3
"""
슬라이스 파일들을 CodeBERT 토크나이저로 토큰화하고,
토큰 개수 분포를 scienceplots 그래프로 출력한다.

사용법:
    python3 tokenize_slices.py
"""

import csv
import os

import matplotlib
matplotlib.use("Agg")  # GUI 없는 환경용
import matplotlib.pyplot as plt
import scienceplots

from transformers import RobertaTokenizer

# ── 경로 설정 ──────────────────────────────────────────────
SLICE_DIR = "/root/infer-experiment/juliet-test-suite-c/slice"
OUTPUT_CSV = "/root/infer-experiment/juliet-test-suite-c/slice_token_counts.csv"
OUTPUT_PLOT = "/root/infer-experiment/juliet-test-suite-c/slice_token_distribution.png"

# ── 토크나이저 로드 ────────────────────────────────────────
tokenizer = RobertaTokenizer.from_pretrained("microsoft/codebert-base")
MAX_LENGTH = 512
CONTENT_TOKEN_LIMIT = MAX_LENGTH - 2  # [CLS], [SEP] 제외 실제 코드 토큰 제한


def tokenize(code: str, max_length: int = MAX_LENGTH) -> list:
    """
    소스코드 문자열을 토큰 ID 리스트로 변환.
    [CLS] + code_tokens + [SEP] + [PAD...]  →  총 max_length개
    """
    code_tokens = tokenizer.tokenize(str(code))[:max_length - 2]
    tokens = [tokenizer.cls_token] + code_tokens + [tokenizer.sep_token]
    token_ids = tokenizer.convert_tokens_to_ids(tokens)
    token_ids += [tokenizer.pad_token_id] * (max_length - len(token_ids))
    return token_ids


def count_code_tokens(code: str) -> int:
    """원본 코드의 토큰 개수(특수 토큰 제외)를 반환."""
    return len(tokenizer.tokenize(str(code)))


def process_slices():
    """슬라이스 디렉토리를 순회하며 토큰 개수를 기록."""
    slice_files = sorted(
        f for f in os.listdir(SLICE_DIR) if f.endswith(".c")
    )

    results = []  # (filename, code_token_count, input_token_count, exceeds_510)
    over_limit_count = 0

    for i, filename in enumerate(slice_files, 1):
        filepath = os.path.join(SLICE_DIR, filename)
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            code = f.read()

        code_token_count = count_code_tokens(code)
        exceeds_510 = code_token_count > CONTENT_TOKEN_LIMIT
        input_token_count = min(code_token_count, CONTENT_TOKEN_LIMIT) + 2

        if exceeds_510:
            over_limit_count += 1

        results.append((filename, code_token_count, input_token_count, exceeds_510))

        if i % 500 == 0:
            print(f"  [{i}/{len(slice_files)}] processed...")

    print(f"\nTotal: {len(results)} slices tokenized.")
    print(f"Over {CONTENT_TOKEN_LIMIT} code tokens: {over_limit_count}")
    return results


def save_csv(results):
    """토큰 개수를 CSV로 저장."""
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "filename",
            "code_token_count",
            "input_token_count_with_special",
            "exceeds_510"
        ])
        for filename, code_token_count, input_token_count, exceeds_510 in results:
            writer.writerow([filename, code_token_count, input_token_count, exceeds_510])
    print(f"CSV saved: {OUTPUT_CSV}")


def plot_distribution(results):
    """토큰 개수 분포 히스토그램을 생성."""
    token_counts = [code_token_count for _, code_token_count, _, _ in results]

    plt.style.use(["science", "no-latex"])
    fig, ax = plt.subplots(figsize=(8, 5))

    ax.hist(token_counts, bins=50, edgecolor="black", alpha=0.7)
    ax.set_xlabel("Token Count")
    ax.set_ylabel("Number of Slices")
    ax.set_title("Token Count Distribution of Vulnerability Slices")

    # 통계 정보 표시
    avg = sum(token_counts) / len(token_counts)
    median = sorted(token_counts)[len(token_counts) // 2]
    stats_text = f"Total: {len(token_counts)}\nMean: {avg:.1f}\nMedian: {median}"
    ax.text(0.95, 0.95, stats_text, transform=ax.transAxes,
            fontsize=9, verticalalignment="top", horizontalalignment="right",
            bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.5))

    fig.tight_layout()
    fig.savefig(OUTPUT_PLOT, dpi=200)
    print(f"Plot saved: {OUTPUT_PLOT}")
    plt.close(fig)


if __name__ == "__main__":
    print("Loading tokenizer...")
    print(f"Reading slices from: {SLICE_DIR}\n")

    results = process_slices()
    save_csv(results)
    plot_distribution(results)
