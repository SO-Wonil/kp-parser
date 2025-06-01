from typing import Dict, List, Any, Union
from xml.etree import ElementTree
from kp_parser.utils.config_utils import get_parsing_rule


class HeaderXmlParser:
    """header.xml 파일 파싱을 위한 전용 파서"""

    def __init__(self, config_name: str = "drug_manual_part2/parsing_rules"):
        """파서 초기화

        Args:
            config_name: 파싱 규칙 설정 파일 이름
        """
        self.config_name = config_name
        self.rules = get_parsing_rule("header_xml", config_name=self.config_name)
        if not self.rules:
            raise ValueError(f"header_xml 파싱 규칙을 찾을 수 없습니다.")

    def parse(
        self, xml_content: Union[str, ElementTree.Element]
    ) -> Dict[str, Dict[str, Union[bool, int, str]]]:
        """header.xml 파일을 파싱합니다.

        Args:
            xml_content: header.xml 파일의 XML 내용 (문자열 또는 ElementTree.Element)

        Returns:
            Dict[str, Dict[str, Union[bool, int, str]]]: 스타일 ID를 키로, 스타일 정보를 값으로 하는 딕셔너리
                - charPr 스타일:
                    - bold: 볼드체 여부
                    - italic: 이탤릭체 여부
                    - underline: 밑줄 여부
                    - format: 서식 플래그 (0: 기본, 32: 아래첨자, 64: 위첨자)
                - style 스타일:
                    - type: 스타일 타입 (PARA, CHAR)
                    - name: 스타일 이름
                    - engName: 영문 스타일 이름
                    - paraPrIDRef: 문단 스타일 ID 참조
                    - charPrIDRef: 글자 스타일 ID 참조
                    - nextStyleIDRef: 다음 스타일 ID 참조
                    - langID: 언어 ID
                    - lockForm: 잠금 여부
        """
        # XML 파싱 (문자열인 경우에만)
        root = (
            xml_content
            if isinstance(xml_content, ElementTree.Element)
            else ElementTree.fromstring(xml_content)
        )

        # 네임스페이스 설정
        namespaces = self.rules["namespaces"]

        # 스타일 정보 파싱
        style_info = {}

        # charPr 요소 파싱
        char_pr_rules = self.rules["style_extraction"]["charPr"]
        for char_pr in root.findall(char_pr_rules["path"], namespaces):
            char_pr_id = char_pr.get("id")
            if not char_pr_id:
                continue

            # underline 태그 찾기
            underline_tag = char_pr.find(
                char_pr_rules["conditions"]["underline"], namespaces
            )
            is_underline = (
                underline_tag is not None
                and underline_tag.get("type", "NONE") != "NONE"
            )

            # 스타일 정보 추출
            style_info[f"charPr-{char_pr_id}"] = {
                "bold": char_pr.find(char_pr_rules["conditions"]["bold"], namespaces)
                is not None,
                "italic": char_pr.find(
                    char_pr_rules["conditions"]["italic"], namespaces
                )
                is not None,
                "underline": is_underline,
                "format": (
                    32
                    if char_pr.find(
                        char_pr_rules["conditions"]["subscript"], namespaces
                    )
                    is not None
                    else (
                        64
                        if char_pr.find(
                            char_pr_rules["conditions"]["superscript"], namespaces
                        )
                        is not None
                        else 0
                    )
                ),
            }

        # style 요소 파싱
        style_rules = self.rules["style_extraction"]["style"]
        for style in root.findall(style_rules["path"], namespaces):
            style_id = style.get("id")
            if not style_id:
                continue

            # 스타일 정보 추출
            style_info[f"style-{style_id}"] = {
                "type": style.get(style_rules["attributes"]["type"], ""),
                "name": style.get(style_rules["attributes"]["name"], ""),
                "engName": style.get(style_rules["attributes"]["engName"], ""),
                "paraPrIDRef": style.get(style_rules["attributes"]["paraPrIDRef"], ""),
                "charPrIDRef": style.get(style_rules["attributes"]["charPrIDRef"], ""),
                "nextStyleIDRef": style.get(
                    style_rules["attributes"]["nextStyleIDRef"], ""
                ),
                "langID": style.get(style_rules["attributes"]["langID"], ""),
                "lockForm": style.get(style_rules["attributes"]["lockForm"], "0")
                == "1",
            }

        return style_info
