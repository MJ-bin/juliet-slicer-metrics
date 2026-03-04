#!/usr/bin/env python3
"""
signature-db의 각 JSON 파일로부터 bug_trace를 읽어,
가장 원소가 많은 sub-array(std_bug_trace)를 선택한 뒤,
해당 경로의 소스코드 라인들만 모아 슬라이스(.c) 파일로 저장한다.

사용법:
    python3 generate_slices.py
"""

import json
import os
import sys

# ── 경로 설정 ──────────────────────────────────────────────
SIGNATURE_DB_DIR = "/root/tracer/signature-db"
OUTPUT_DIR = "/root/infer-experiment/juliet-test-suite-c/slice"

# JSON 내 filename 에 기록된 원래 경로 → 컨테이너 경로로 치환
OLD_PREFIX = "/home/wooseok/workspace/"
NEW_PREFIX = "/root/"


def fix_path(original_path: str) -> str:
    """원본 경로의 prefix를 컨테이너 내부 경로로 교체."""
    if original_path.startswith(OLD_PREFIX):
        return original_path.replace(OLD_PREFIX, NEW_PREFIX, 1)
    return original_path


def read_source_line(filepath: str, line_number: int) -> str:
    """소스 파일에서 특정 줄을 읽어 반환. 실패 시 None을 반환."""
    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
        if 1 <= line_number <= len(lines):
            return lines[line_number - 1]
        else:
            return None
    except FileNotFoundError:
        return None
    except Exception:
        return None


def extract_std_bug_trace(bug_trace: list) -> list:
    """2차원 Jagged Array에서 원소 수가 가장 많은 1차원 배열을 반환."""
    if not bug_trace:
        return []
    return max(bug_trace, key=len)


def build_slice(std_bug_trace: list) -> str:
    """std_bug_trace의 각 원소에서 filename·line_number를 이용해 슬라이스 문자열을 생성."""
    slice_lines = []
    seen = set()  # (filepath, line_number) 중복 방지

    for node in std_bug_trace:
        filepath = fix_path(node["filename"])
        line_number = node["line_number"]

        key = (filepath, line_number)
        if key in seen:
            continue
        seen.add(key)

        source_line = read_source_line(filepath, line_number)
        if source_line is None:
            return None  # 파일이나 줄을 찾을 수 없으면 해당 슬라이스는 생성 취소
            
        slice_lines.append(source_line)

    return "".join(slice_lines)


def process_signature_db():
    """signature-db 전체를 순회하며 슬라이스 파일을 생성."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    dirs = sorted(
        d for d in os.listdir(SIGNATURE_DB_DIR)
        if os.path.isdir(os.path.join(SIGNATURE_DB_DIR, d))
    )

    total_slices = 0
    errors = 0

    for dir_name in dirs:
        dir_path = os.path.join(SIGNATURE_DB_DIR, dir_name)

        json_files = sorted(
            f for f in os.listdir(dir_path) if f.endswith(".json")
        )

        for json_file in json_files:
            json_path = os.path.join(dir_path, json_file)
            json_stem = os.path.splitext(json_file)[0]  # e.g. "1"

            try:
                with open(json_path, "r", encoding="utf-8") as fp:
                    data = json.load(fp)

                bug_trace = data.get("bug_trace", [])
                std_bug_trace = extract_std_bug_trace(bug_trace)

                if not std_bug_trace:
                    print(f"[SKIP] empty bug_trace: {json_path}")
                    continue

                slice_content = build_slice(std_bug_trace)

                if slice_content is None:
                    # 소스 코드를 찾을 수 없는 외부 데이터셋(sam2p 등)은 건너뜀
                    # print(f"[SKIP] Source not found for: {json_path}")
                    continue

                # 출력 파일명: slice_{디렉토리명}_{JSON파일명}.c
                output_filename = f"slice_{dir_name}_{json_stem}.c"
                output_path = os.path.join(OUTPUT_DIR, output_filename)

                with open(output_path, "w", encoding="utf-8") as fp:
                    fp.write(slice_content)

                total_slices += 1

            except Exception as e:
                print(f"[ERROR] {json_path}: {e}")
                errors += 1

    print(f"\nDone. {total_slices} slices generated, {errors} errors.")
    print(f"Output directory: {OUTPUT_DIR}")


if __name__ == "__main__":
    process_signature_db()
