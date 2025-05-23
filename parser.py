import os
import json
import re
import base64
import shutil
import pprint

from bs4 import BeautifulSoup


# 이미지 정보 추출
def get_image_info():
    with open('test/Contents/content.hpf', 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f.read(), 'xml')
    opf_items = soup.find_all('opf:item')

    ret = {}   
    for item in opf_items:
        ret[item.get('id')] = {
            'href': item.get('href'),
            'media_type': item.get('media-type'),
            'is_embedded': item.get('isEmbeded')
        }
    return ret

# 스타일 정보 추출
def get_style_info():
    with open('test/Contents/header.xml', 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f.read(), 'xml')

    ret = {}
    charPr_tags = soup.find_all('hh:charPr')
    for charPr_tag in charPr_tags:
        id = charPr_tag.get('id')
        bold = charPr_tag.find('hh:bold') is not None
        italic = charPr_tag.find('hh:italic') is not None
        underline = charPr_tag.find('hh:underline').get('type') != "NONE"
        sub = charPr_tag.find('hh:subscript') is not None
        sup = charPr_tag.find('hh:superscript') is not None
        
        
        ret[f'charPr-{id}'] = {
            'bold': bold,
            'italic': italic,
            'underline': underline,
            'format': 32 if sub else 64 if sup else 0
        }
        
    return ret


# section0.xml 파싱
def is_displayable_image(media_type):
    return media_type in ('image/png', 'image/jpeg', 'image/jpg', 'image/gif', 'image/svg+xml')

def process_image_in_paragraph(run, image_info, folder_path):
    pic_tag = run.find('hp:pic')
    if not pic_tag:
        return None

    img_tag = pic_tag.find('hc:img')
    if not img_tag:
        return None

    img_id = img_tag.get('binaryItemIDRef')
    if not img_id:
        return None

    image_meta = image_info.get(img_id)
    if not image_meta:
        return None

    href = image_meta['href']
    extension = os.path.splitext(href)[-1].lower()

    # 원본 이미지 경로 (항상 고정된 위치에서 찾는다)
    source_path = os.path.join('test', href)
    if not os.path.exists(source_path):
        return None

    # 저장 대상 경로 (의약품 전용 폴더)
    os.makedirs(folder_path, exist_ok=True)
    target_path = os.path.join(folder_path, os.path.basename(href))

    with open(source_path, 'rb') as img_f:
        image_data = img_f.read()

    # ✅ 파일 저장은 항상 한다
    with open(target_path, 'wb') as out_f:
        out_f.write(image_data)

    # ✅ base64 인코딩은 표시 가능한 포맷만
    if extension in ['.png', '.jpg', '.jpeg', '.gif', '.bmp']:
        mime = f"image/{extension[1:]}" if extension != '.jpg' else "image/jpeg"
        encoded_data = base64.b64encode(image_data).decode('utf-8')
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
                    "version": 1
                }
            }
        },
        "height": 0,
        "maxWidth": 500,
        "showCaption": False,
        "src": src
    }

def extract_text(hp_p_tag):
    return ' '.join(t.text.strip() for t in hp_p_tag.find_all('hp:t') if t.text.strip())

def build_paragraph(hp_p_tag, style_info, folder_path):
    paragraph = {
        'type': 'paragraph',
        'version': 1,
        'direction': 'ltr',
        'format': '',
        'indent': 0,
        'textFormat': 0,
        'textStyle': '',
        'children': []
    }

    for run in hp_p_tag.find_all('hp:run'):
        char_pr_id = run.get('charPrIDRef')
        style = style_info.get(f'charPr-{char_pr_id}', {}) if char_pr_id else {}

        
        format_flag = 0
        if style.get('bold'):
            format_flag = 1
        elif style.get('italic'):
            format_flag = 2
        elif style.get('underline'):
            format_flag = 4
        # subscript or superscript
        else:
            format_flag = style.get('format', 0)  
        
         # 이미지 처리
        pic_tag = run.find('hp:pic')
        if pic_tag:
            image_node = process_image_in_paragraph(run, image_info, folder_path)
            if image_node:
                paragraph['children'].append(image_node)

        for t in run.find_all('hp:t'):
            paragraph['children'].append({
                'detail': 0,
                'format': format_flag,
                'mode': 'normal',
                'style': '',
                'text': t.text,
                'type': 'text',
                'version': 1
            })

    return paragraph

def parse_section0_xml(style_info):
    with open('test/Contents/section0.xml', 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f.read(), 'xml')
    hp_p_tags = soup.find_all('hp:p')
    
    result = []
    current_page = None
    i = 0
    
    while i < len(hp_p_tags):
        p_tag = hp_p_tags[i]
        if p_tag.get('styleIDRef') in ('1', '2') and any(seg.get("textheight") == "1100" for seg in p_tag.find_all("hp:lineseg")):
            # 새 의약품 시작
            title = extract_text(p_tag)
            subtitle = extract_text(hp_p_tags[i + 1]) if i + 1 < len(hp_p_tags) else ""
            folder_path = os.path.join('output_pages', sanitize_filename(title))

            os.makedirs(folder_path, exist_ok=True)
            
            current_page = {
                'title': title,
                'subtitle': subtitle,
                'content': []
            }
            result.append(current_page)
            i += 2  # title + subtitle 건너뛰기
            continue

        if current_page:
            para = build_paragraph(p_tag, style_info, folder_path)
            if para['children']:  # 내용이 있으면 추가
                current_page['content'].append(para)

        i += 1

    return result

def sanitize_filename(name):
    """윈도우나 리눅스에서 파일/폴더 이름에 쓸 수 없는 문자 제거"""
    return re.sub(r'[\\/*?:"<>|]', "_", name).strip()

def save_pages_by_title(pages, output_base='output_pages'):
    """
    페이지 리스트를 타이틀 기준으로 폴더로 나누어 저장한다.
    각 페이지의 content는 root.children 아래에 들어간다.
    """
    os.makedirs(output_base, exist_ok=True)

    print(len(pages))
    for page in pages:
        title = sanitize_filename(page.get('title', 'untitled'))
        folder_path = os.path.join(output_base, title)
        os.makedirs(folder_path, exist_ok=True)

        output_data = {
            "root": {
                "direction": "ltr",
                "format": "",
                "indent": 0,
                "type": "root",
                "version": 1,
                "children": page.get('content', [])
            }
        }

        json_path = os.path.join(folder_path, 'data.json')
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)                
                
    
    
    

image_info = get_image_info()
style_info = get_style_info()
text_info = parse_section0_xml(style_info)
save_pages_by_title(text_info)



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
