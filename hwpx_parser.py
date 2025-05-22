import zipfile
import re
import os
import json
from bs4 import BeautifulSoup

def extract_style_info(soup):
    """스타일 정보를 추출합니다."""
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

def parse_paragraph(p_tag, style_map):
    """문단을 파싱하여 텍스트와 스타일 정보를 추출합니다."""
    runs = []
    
    # 이미지 처리
    if p_tag.find("hp:img"):
        img = p_tag.find("hp:img")
        runs.append({
            "type": "image",
            "version": 1,
            "altText": img.get("id", ""),
            "caption": {
                "editorState": {
                    "root": {
                        "children": [],
                        "direction": None,
                        "format": "",
                        "indent": 0,
                        "type": "root",
                        "version": 1
                    }
                }
            },
            "height": 0,
            "maxWidth": 500,
            "showCaption": False,
            "src": img.get("binaryData", "")
        })
        return runs

    # 수식 처리
    if p_tag.find("hp:equation"):
        eq = p_tag.find("hp:equation")
        runs.append({
            "type": "equation",
            "version": 1,
            "equation": eq.get("equation", "")
        })
        return runs

    # 일반 텍스트 처리
    for run in p_tag.find_all('hp:run'):
        charPr_id = run.get("charPrIDRef")
        style = style_map.get(charPr_id, {})
        
        text_node = run.find("hp:t")
        if not text_node or not text_node.text.strip():
            continue
            
        text = text_node.text.strip()
        offset = style.get("offset", 0)
        text_style = "sup" if offset > 0 else "sub" if offset < 0 else ""
        
        runs.append({
            "type": "text",
            "version": 1,
            "text": text,
            "format": 1 if style.get("bold") else 0,
            "detail": 0,
            "mode": "normal",
            "style": "",
            "textStyle": text_style
        })
    
    return runs

def is_drug_name(p_tag):
    """의약품명 여부를 확인합니다."""
    # textheight가 1100인지 확인
    has_correct_height = any(
        seg.get("textheight") == "1100" 
        for seg in p_tag.find_all("hp:lineseg")
    )
    
    # 한글만 포함되어 있는지 확인
    text = ''.join(t.text for t in p_tag.find_all("hp:t")).strip()
    is_korean = bool(re.match(r'^[가-힣\s]+$', text))
    
    return has_correct_height and is_korean

def parse_hwpx_to_json(hwpx_path, output_dir="output"):
    """HWPX 파일을 파싱하여 JSON으로 변환합니다."""
    # 1. HWPX -> XML 변환
    with zipfile.ZipFile(hwpx_path, 'r') as z:
        section_xml = z.read('Contents/section0.xml')
    
    # 2. XML 파싱
    soup = BeautifulSoup(section_xml, 'xml')
    style_map = extract_style_info(soup)
    
    # 3. 문단 파싱 및 의약품명 기준 분리
    blocks = []
    current_block = []
    current_drug = None
    
    for p in soup.find_all('hp:p'):
        runs = parse_paragraph(p, style_map)
        if not runs:
            continue
            
        # 문단 타입 결정
        p_type = "heading" if p.find("hp:heading") else "paragraph"
        tag = "h2" if p_type == "heading" else None
            
        paragraph = {
            "type": p_type,
            "version": 1,
            "direction": "ltr",
            "format": "",
            "indent": 0,
            "textFormat": 0,
            "textStyle": "",
            "children": runs
        }
        
        if tag:
            paragraph["tag"] = tag
        
        # 의약품명 확인
        if is_drug_name(p):
            if current_block and current_drug:
                blocks.append((current_drug, current_block))
            current_drug = runs[0]["text"] if runs and runs[0]["type"] == "text" else ""
            current_block = [paragraph]
        elif current_drug:
            current_block.append(paragraph)
    
    # 마지막 블록 처리
    if current_block and current_drug:
        blocks.append((current_drug, current_block))
    
    # 4. JSON 저장
    os.makedirs(output_dir, exist_ok=True)
    for drug_name, content in blocks:
        data = {
            "root": {
                "type": "root",
                "version": 1,
                "direction": "ltr",
                "format": "",
                "indent": 0,
                "children": content
            }
        }
        
        # 파일명 생성 (특수문자 제거)
        safe_name = re.sub(r'[^\w가-힣]', '_', drug_name)
        output_path = os.path.join(output_dir, f"{safe_name}.json")
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    parse_hwpx_to_json("test.hwpx") 