import zipfile
import re
import os
import json
from bs4 import BeautifulSoup

# 스타일 정보 추출 (section0.xml 내부 charPr 기준)
def extract_inline_styles(soup):
    style_map = {}
    for char in soup.find_all("hp:charPr"):
        style_id = char.get("id")
        if style_id:
            style_map[style_id] = {
                "bold": char.get("bold") == "true",
                "italic": char.get("italic") == "true",
                "fontSize": int(char.get("height", 0)),
                "offset": int(char.get("offset", 0)) if char.get("offset") else 0
            }
    return style_map

# 병합
def merge_runs(runs):
    if not runs:
        return []
    merged = [runs[0]]
    for run in runs[1:]:
        last = merged[-1]
        if all(run.get(k) == last.get(k) for k in ["format", "detail", "mode", "style", "textStyle"]):
            last["text"] += run["text"]
        else:
            merged.append(run)
    return merged

# HWPX 파싱 전체 과정
def parse_hwpx_to_json_blocks(hwpx_path, output_dir="output"):
    with zipfile.ZipFile(hwpx_path, 'r') as z:
        section_xml = z.read('Contents/section0.xml')

    section_soup = BeautifulSoup(section_xml, 'xml')
    style_map = extract_inline_styles(section_soup)

    paragraphs = []
    for p in section_soup.find_all('hp:p'):
        runs = []
        for run in p.find_all('hp:run'):
            charPr_id = run.get("charPrIDRef")
            style = style_map.get(charPr_id, {})
            offset = style.get("offset", 0)
            text_style = "sup" if offset > 0 else "sub" if offset < 0 else ""

            text_node = run.find("hp:t")
            if text_node and text_node.text.strip():
                runs.append({
                    "type": "text",
                    "version": 1,
                    "text": text_node.text.strip(),
                    "format": 1 if style.get("bold") else 0,
                    "detail": 0,
                    "mode": "normal",
                    "style": "",
                    "textStyle": text_style
                })

        if runs:
            merged = merge_runs(runs)
            paragraphs.append({
                "type": "paragraph",
                "version": 1,
                "direction": "ltr",
                "format": "",
                "indent": 0,
                "textFormat": 0,
                "textStyle": "",
                "children": merged
            })

    # 약물명 기준 분리
    para_tags = section_soup.find_all("hp:p")
    blocks = []
    current = []
    drug_names = []

    for para, tag in zip(paragraphs, para_tags):
        text = ''.join(t.get_text() for t in tag.find_all("hp:t")).strip()
        # is_drug = any(seg.get("textheight") == "1100" for seg in tag.find_all("hp:lineseg"))
        is_drug = (
            any(seg.get("textheight") == "1100" for seg in tag.find_all("hp:lineseg")) and
            re.search(r'[가-힣]', text)  # 한글 포함 여부 체크
        )

        if is_drug:
            if current and drug_names:
                blocks.append((drug_names[-1], current))
            drug_name = re.sub(r'[^\w가-힣]', '_', text)[:50]
            drug_names.append(drug_name)
            current = [para]  # 새 블록 시작
        elif drug_names:
            current.append(para)  # 약물명 이후 문단만 추가

    if current and drug_names:
        blocks.append((drug_names[-1], current))

    # 저장
    os.makedirs(output_dir, exist_ok=True)
    for name, content in blocks:
        data = {
            "root": {
                "type": "root",
                "version": 1,
                "format": "",
                "indent": 0,
                "direction": "ltr",
                "children": content
            }
        }
        with open(os.path.join(output_dir, f"{name}.json"), "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

# ✅ 실행 예
parse_hwpx_to_json_blocks("test.hwpx")