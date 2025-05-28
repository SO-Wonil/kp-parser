import os
import json
import re
import base64
import shutil
import pprint

from bs4 import BeautifulSoup


# 이미지 정보 추출
def get_image_info():
    with open("test/Contents/content.hpf", "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), "xml")
    opf_items = soup.find_all("opf:item")

    ret = {}
    for item in opf_items:
        ret[item.get("id")] = {
            "href": item.get("href"),
            "media_type": item.get("media-type"),
            "is_embedded": item.get("isEmbeded"),
        }
    return ret


# 스타일 정보 추출
def get_style_info():
    with open("test/Contents/header.xml", "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), "xml")

    ret = {}
    charPr_tags = soup.find_all("hh:charPr")
    for charPr_tag in charPr_tags:
        id = charPr_tag.get("id")
        bold = charPr_tag.find("hh:bold") is not None
        italic = charPr_tag.find("hh:italic") is not None
        underline = charPr_tag.find("hh:underline").get("type") != "NONE"
        sub = charPr_tag.find("hh:subscript") is not None
        sup = charPr_tag.find("hh:superscript") is not None

        ret[f"charPr-{id}"] = {
            "bold": bold,
            "italic": italic,
            "underline": underline,
            "format": 32 if sub else 64 if sup else 0,
        }

    return ret


# section0.xml 파싱
def process_image_in_paragraph(run, image_info, folder_path):
    pic_tag = run.find("hp:pic")
    if not pic_tag:
        return None

    img_tag = pic_tag.find("hc:img")
    if not img_tag:
        return None

    img_id = img_tag.get("binaryItemIDRef")
    if not img_id:
        return None

    image_meta = image_info.get(img_id)
    if not image_meta:
        return None

    href = image_meta["href"]
    extension = os.path.splitext(href)[-1].lower()

    # 원본 이미지 경로 (항상 고정된 위치에서 찾는다)
    source_path = os.path.join("test", href)
    if not os.path.exists(source_path):
        return None

    # 저장 대상 경로 (의약품 전용 폴더)
    os.makedirs(folder_path, exist_ok=True)
    target_path = os.path.join(folder_path, os.path.basename(href))

    with open(source_path, "rb") as img_f:
        image_data = img_f.read()

    # ✅ 파일 저장은 항상 한다
    with open(target_path, "wb") as out_f:
        out_f.write(image_data)

    # ✅ base64 인코딩은 표시 가능한 포맷만
    if extension in [".png", ".jpg", ".jpeg", ".gif", ".bmp"]:
        mime = f"image/{extension[1:]}" if extension != ".jpg" else "image/jpeg"
        encoded_data = base64.b64encode(image_data).decode("utf-8")
        src = f"data:{mime};base64,{encoded_data}"
    else:
        src = None  # 표시 불가 포맷은 base64 미생성

    return {
        "type": "image",
        "version": 1,
        "altText": img_id,
        "caption": {
            "editorState": {
                "root": {
                    "children": [],
                    "direction": None,
                    "format": "",
                    "indent": 0,
                    "type": "root",
                    "version": 1,
                }
            }
        },
        "height": 0,
        "maxWidth": 500,
        "showCaption": False,
        "src": src,
    }


def extract_text(hp_p_tag):
    return " ".join(t.text.strip() for t in hp_p_tag.find_all("hp:t") if t.text.strip())


def convert_to_katex(equation):
    # 분수 변환: a over b → \frac{a}{b}
    equation = re.sub(r"([^{\s]+)\s+over\s+([^{\s]+)", r"\\frac{\1}{\2}", equation)
    # rm, it 변환: rm{ABC} → \mathrm{ABC}, it{ABC} → \textit{ABC}
    equation = re.sub(r"rm{([^}]+)}", r"\\mathrm{\1}", equation)
    equation = re.sub(r"it{([^}]+)}", r"\\textit{\1}", equation)
    # TIMES 변환
    equation = equation.replace("TIMES", "\\times")
    # 명령어 뒤에 공백 추가
    equation = re.sub(r"(\\(?:mathrm|textit|frac|times))", r"\1 ", equation)
    # 연속 공백 정리
    equation = re.sub(r" +", " ", equation).strip()
    return equation


def process_equation_in_paragraph(run):
    """수식 태그를 발견하면 빨간색 볼드체 '수식' 텍스트 노드를 반환"""
    equation_tag = run.find("hp:equation")
    if not equation_tag:
        return None

    # 빨간색 볼드체 '수식' 텍스트 노드 반환
    return {
        "detail": 0,
        "format": 1,  # 볼드체
        "mode": "normal",
        "style": "color: #ff0000;",  # 빨간색
        "text": "수식",
        "type": "text",
        "version": 1,
    }


def build_paragraph(hp_p_tag, style_info, folder_path):
    paragraph = {
        "type": "paragraph",
        "version": 1,
        "direction": "ltr",
        "format": "",
        "indent": 0,
        "textFormat": 0,
        "textStyle": "",
        "children": [],
    }

    for run in hp_p_tag.find_all("hp:run"):
        char_pr_id = run.get("charPrIDRef")
        style = style_info.get(f"charPr-{char_pr_id}", {}) if char_pr_id else {}

        format_flag = 0
        if style.get("bold"):
            format_flag = 1
        elif style.get("italic"):
            format_flag = 2
        elif style.get("underline"):
            format_flag = 4
        # subscript or superscript
        else:
            format_flag = style.get("format", 0)

        # 이미지 처리
        pic_tag = run.find("hp:pic")
        if pic_tag:
            image_node = process_image_in_paragraph(run, image_info, folder_path)
            if image_node:
                paragraph["children"].append(image_node)

        # 수식 처리
        equation_node = process_equation_in_paragraph(run)
        if equation_node:
            paragraph["children"].append(equation_node)

        for t in run.find_all("hp:t"):
            if t.text.strip():  # 빈 텍스트는 건너뛰기
                paragraph["children"].append(
                    {
                        "detail": 0,
                        "format": format_flag,
                        "mode": "normal",
                        "style": "",
                        "text": t.text,
                        "type": "text",
                        "version": 1,
                    }
                )

    return paragraph


def parse_section0_xml(style_info):
    with open("test/Contents/section0.xml", "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), "xml")
    hp_p_tags = soup.find_all("hp:p")

    result = []
    current_page = None
    i = 0
    order = 1  # 의약품 순서를 추적하기 위한 변수

    while i < len(hp_p_tags):
        print(order)
        p_tag = hp_p_tags[i]
        if p_tag.get("styleIDRef") in ("1", "2") and any(
            seg.get("textheight") == "1100" for seg in p_tag.find_all("hp:lineseg")
        ):
            first_text = extract_text(p_tag)
            second_text = (
                extract_text(hp_p_tags[i + 1]) if i + 1 < len(hp_p_tags) else ""
            )

            def is_korean(text):
                return any("\uac00" <= char <= "\ud7a3" for char in text)

            if is_korean(first_text):
                title = first_text
                subtitle = second_text
            else:
                title = second_text
                subtitle = first_text

            folder_path = os.path.join("output_pages", sanitize_filename(title))
            os.makedirs(folder_path, exist_ok=True)

            metadata = {"title": title, "subtitle": subtitle, "order": order}
            metadata_path = os.path.join(folder_path, "metadata.json")
            with open(metadata_path, "w", encoding="utf-8") as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)

            current_page = {
                "title": title,
                "subtitle": subtitle,
                "content": [],
                "folder_path": folder_path,  # 폴더 경로 저장
            }
            result.append(current_page)
            order += 1
            i += 2
            continue

        if current_page:
            para = build_paragraph(p_tag, style_info, current_page["folder_path"])
            if para["children"]:
                current_page["content"].append(para)

        i += 1

    # 각 의약품별로 JSON 파일 저장
    for page in result:
        title = sanitize_filename(page.get("title", "untitled"))
        folder_path = page.get("folder_path", os.path.join("output_pages", title))
        output_data = {
            "root": {
                "direction": "ltr",
                "format": "",
                "indent": 0,
                "type": "root",
                "version": 1,
                "children": page.get("content", []),
            }
        }
        json_path = os.path.join(folder_path, "data.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)

    return result


def sanitize_filename(name):
    """윈도우나 리눅스에서 파일/폴더 이름에 쓸 수 없는 문자 제거 및 기호 주변 공백 제거"""
    # 먼저 파일명에 사용할 수 없는 문자를 언더스코어로 변경
    name = re.sub(r'[\\/*?:"<>|]', "_", name)
    # 문자 사이의 하이픈과 가운뎃점 주변 공백 제거 (기호는 유지)
    name = re.sub(r"(\S)\s*([-·])\s*(\S)", r"\1\2\3", name)
    return name.strip()


image_info = get_image_info()
style_info = get_style_info()
text_info = parse_section0_xml(style_info)


# ret = {
#         'root': {
#             'direction': 'ltr',
#             'format': '',
#             'indent': 0,
#             'type': 'root',
#             'version': 1,
#             'children': []
#         }
#     }
