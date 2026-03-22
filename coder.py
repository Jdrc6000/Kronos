from pathlib import Path

main_path = Path(__file__).parent
txt_path = main_path / "coded.txt"

total_raw_loc = 0
total_clean_loc = 0
collected = []

def count_clean_lines(text: str, suffix: str):
    lines = text.splitlines()
    clean_count = 0

    in_block_comment = False
    active_block_end = None

    if suffix == ".py":
        single_comment = "#"
        block_pairs = [("'''", "'''")]
    elif suffix == ".js":
        single_comment = "//"
        block_pairs = [("/*", "*/")]
    elif suffix == ".css":
        single_comment = None
        block_pairs = [("/*", "*/")]
    elif suffix == ".html":
        single_comment = None
        block_pairs = [("<!--", "-->")]
    elif suffix in (".yaml", ".txt", ".yml", "Dockerfile"):
        single_comment = "#"
        block_pairs = []
    else:
        single_comment = ""
        block_pairs = []

    cleaned_lines = []

    for line in lines:
        stripped = line.strip()

        if not stripped:
            continue

        if in_block_comment:
            if active_block_end and active_block_end in stripped:
                in_block_comment = False
                active_block_end = None
            continue

        block_started = False
        for start, end in block_pairs:
            if start in stripped:
                if end in stripped and stripped.index(start) < stripped.index(end):
                    before = line.split(start)[0].rstrip()
                    if before.strip():
                        cleaned_lines.append(before)
                        clean_count += 1
                else:
                    in_block_comment = True
                    active_block_end = end
                block_started = True
                break

        if block_started:
            continue

        if single_comment and stripped.startswith(single_comment):
            continue

        cleaned_lines.append(line)  # ← preserve indentation
        clean_count += 1

    return clean_count, cleaned_lines

for file_path in sorted(main_path.rglob("*")):
    if file_path.name in {txt_path.name, "coder.py", ".bin", ".exe", "iso", ".orion"}:
        continue
    if file_path.is_dir():
        continue
    if any(part in {"venv", ".git", ".o"} for part in file_path.parts):
        continue

    try:
        content_text = file_path.read_text(encoding="utf-8")
    except Exception as e:
        print(f"Skipping {file_path}: {e}")
        continue

    raw_loc = content_text.count("\n") + 1
    clean_loc, cleaned_lines = count_clean_lines(content_text, file_path.suffix.lower())

    total_raw_loc += raw_loc
    total_clean_loc += clean_loc

    collected.append(
        f"--- {file_path.relative_to(main_path)} ---\n"
        + "\n".join(cleaned_lines)
        + "\n\n"
    )

    print(
        f"({file_path.parent.name}) {file_path.name} "
        f"RAW: {raw_loc} CLEAN: {clean_loc}"
    )

print(f"\nTOTAL RAW LOC: {total_raw_loc}")
print(f"TOTAL CLEAN LOC: {total_clean_loc}")

txt_path.write_text("".join(collected), encoding="utf-8")