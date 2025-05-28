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
from kp_parser.utils import extract_hwpx_content

# 일반 모드 (메모리에 로딩)
content_map = extract_hwpx_content("example.hwpx", debug=False)
# content_map은 {파일명: ElementTree.Element 또는 bytes} 형태

# 디버그 모드 (파일로 추출)
extract_dir = extract_hwpx_content("example.hwpx", extract_dir="output", debug=True)
# extract_dir은 추출된 디렉토리 경로
```

### 함수 설명

`extract_hwpx_content(file_path: str, extract_dir: str = "temp", debug: bool = False)`

- `file_path`: .hwpx 파일 경로
- `extract_dir`: 디버그 모드일 때 압축 해제할 디렉토리
- `debug`:
  - `True`: 모든 파일을 디스크에 저장
  - `False`: Contents/와 BinData/ 디렉토리의 파일만 메모리에 로딩

## 테스트

### 테스트 실행

```bash
# 전체 테스트 실행
test

# 특정 테스트 파일 실행
test tests/unit/test_file_utils.py

# 자세한 출력으로 실행
test -v
```

### 테스트 커버리지 확인

```bash
test --cov=src/kp_parser --cov-report=term-missing
```

## 개발 환경 설정

### 코드 포맷팅

```bash
# 코드 포맷팅
format

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
│       ├── core/
│       │   └── parser.py
│       └── utils/
│           └── file_utils.py
├── tests/
│   └── unit/
│       └── test_file_utils.py
├── pyproject.toml
└── README.md
```
