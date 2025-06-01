"""
한글 문서(.hwpx) 파싱 라이브러리
"""

# 패키지 메타데이터
__version__ = "0.1.0"  # 패키지 버전
__author__ = "SO&CO"  # 작성자 정보

# 주요 클래스들을 패키지 레벨에서 import
# 이를 통해 사용자는 from kp_parser import HwpxParser 와 같이 간단히 import 가능
from kp_parser.core.content_hpf_parser import ContentHpfParser
from kp_parser.core.header_xml_parser import HeaderXmlParser
from kp_parser.core.section_xml_parser import SectionXmlParser

# from kp_parser import * 사용 시 import될 항목들을 명시
# 패키지의 공개 API를 정의
__all__ = [
    "ContentHpfParser",  # content.hpf 파일 파서
    "HeaderXmlParser",  # header.xml 파일 파서
    "SectionXmlParser",  # section{n}.xml 파일 파서
    "__version__",  # 버전 정보
]
