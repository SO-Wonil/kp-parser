# KP Parser

한글 문서(.hwpx) 파싱 라이브러리

## 설치 방법

```bash
# 가상환경 생성 및 활성화
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 또는
.\venv\Scripts\activate  # Windows

# 패키지 설치 (개발 의존성 포함)
pip install -e ".[dev]"
```

## 사용 방법

### 기본 사용법

```python
from kp_parser import ContentHpfParser, HeaderXmlParser, SectionXmlParser
from kp_parser.utils.file_utils import extract_hwpx_content

# HWPX 파일 압축 해제 및 내용 로드
content_map = extract_hwpx_content(
    "example.hwpx",
    extract_dir="data/tmp",
    debug=False
)

# header.xml 파싱
header_parser = HeaderXmlParser()
header_xml = content_map.get("Contents/header.xml")
style_info = {}
if header_xml is not None:
    style_info = header_parser.parse(header_xml)

# content.hpf 파싱 (이미지 정보)
content_parser = ContentHpfParser()
content_hpf = content_map.get("Contents/content.hpf")
image_info = {}
if content_hpf is not None:
    parsed_image_info = content_parser.parse(content_hpf)
    if isinstance(parsed_image_info, list):
        image_info = {img["id"]: img for img in parsed_image_info}

# section0.xml 파싱
section_parser = SectionXmlParser()
section0_xml = content_map.get("Contents/section0.xml")
if section0_xml is not None:
    parsed_data = section_parser.parse(
        section0_xml,
        style_info,
        image_info,
        output_dir="data/output/result"
    )
```

### 파싱 결과 구조

```json
{
  "chapter": "의약품각조 제2부",
  "section": "제1장",
  "title": "의약품명",
  "subtitle": "영문명",
  "order": 1,
  "content": [
    {
      "type": "paragraph",
      "version": 1,
      "direction": "ltr",
      "format": "",
      "indent": 0,
      "textFormat": 0,
      "textStyle": "",
      "children": [
        {
          "type": "text",
          "version": 1,
          "text": "내용",
          "format": 0,
          "mode": "normal",
          "style": ""
        }
      ]
    }
  ]
}
```

## 개발 환경 설정

### 코드 포맷팅

```bash
# 코드 포맷팅
black .

# import 정렬
isort .
```

### 타입 체크

```bash
mypy src/kp_parser
```

## 프로젝트 구조

```
kp_parser/
├── src/
│   └── kp_parser/
│       ├── config/
│       │   └── drug_manual_part2/
│       │       └── parsing_rules.yaml
│       ├── core/
│       │   ├── content_hpf_parser.py
│       │   ├── header_xml_parser.py
│       │   └── section_xml_parser.py
│       └── utils/
│           ├── config_utils.py
│           └── file_utils.py
├── main.py
├── pyproject.toml
└── README.md
```
