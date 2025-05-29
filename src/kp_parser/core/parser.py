from typing import Dict, Union, Optional, Any
from xml.etree import ElementTree


class HwpxDocument:
    """한글 문서(.hwpx)를 파싱하고 관리하는 클래스"""

    def __init__(self, content_map: Dict[str, Union[ElementTree.Element, bytes]]):
        """
        Args:
            content_map: extract_hwpx_content 함수가 반환한 딕셔너리
                - key: 파일 경로 (예: "Contents/content.hpf", "BinData/image1.png")
                - value: XML Element 또는 바이너리 데이터
        """
        self._content_map = content_map
        self._image_info = None  # 이미지 정보 캐시
        self._style_info = None  # 스타일 정보 캐시

    @property
    def content_xml(self) -> Optional[ElementTree.Element]:
        """content.hpf 파일의 XML Element"""
        content = self._content_map.get("Contents/content.hpf")
        return content if isinstance(content, ElementTree.Element) else None

    @property
    def header_xml(self) -> Optional[ElementTree.Element]:
        """header.xml 파일의 XML Element"""
        header = self._content_map.get("Contents/header.xml")
        return header if isinstance(header, ElementTree.Element) else None

    def get_image_info(self) -> Dict[str, Dict[str, Any]]:
        """content.hpf 파일에서 이미지 정보를 파싱합니다."""
        if self._image_info is not None:
            return self._image_info

        content = self._content_map.get("Contents/content.hpf")
        if content is None:
            print("content.hpf 파일이 없습니다.")
            return {}

        if not isinstance(content, ElementTree.Element):
            content = ElementTree.fromstring(content)

        # 네임스페이스 정의
        namespaces = {"opf": "http://www.idpf.org/2007/opf/"}

        # 이미지 정보 수집
        image_info = {}
        for item in content.findall(".//opf:manifest/opf:item", namespaces):
            media_type = item.get("media-type", "")
            if media_type.startswith("image/"):
                image_id = item.get("id", "")
                href = item.get("href", "")
                is_embedded = item.get("isEmbeded", "0") == "1"

                image_info[image_id] = {
                    "href": href,
                    "media_type": media_type,
                    "is_embedded": is_embedded,
                }

        print(f"이미지 정보: {image_info}")
        self._image_info = image_info
        return image_info

    def get_style_info(self) -> Dict[str, Dict[str, Union[bool, int, str]]]:
        """
        header.xml 파일에서 스타일 정보를 파싱합니다.

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
        # 캐시된 스타일 정보가 있으면 반환
        if self._style_info is not None:
            return self._style_info

        # header.xml 파일이 없으면 빈 딕셔너리 반환
        if not self.header_xml:
            print("스타일 정보: header.xml 파일이 없습니다.")
            return {}

        # 스타일 정보 파싱
        style_info = {}
        # XML 네임스페이스 정의
        namespaces = {"hh": "http://www.hancom.co.kr/hwpml/2011/head"}

        # charPr 요소 파싱
        for char_pr in self.header_xml.findall(".//hh:charPr", namespaces):
            char_pr_id = char_pr.get("id")
            if not char_pr_id:
                continue

            # 스타일 정보 추출
            underline_tag = char_pr.find(".//hh:underline", namespaces)
            style_info[f"charPr-{char_pr_id}"] = {
                "bold": char_pr.find(".//hh:bold", namespaces) is not None,
                "italic": char_pr.find(".//hh:italic", namespaces) is not None,
                "underline": underline_tag is not None
                and underline_tag.get("type", "NONE") != "NONE",
                "format": (
                    32
                    if char_pr.find(".//hh:subscript", namespaces) is not None
                    else (
                        64
                        if char_pr.find(".//hh:superscript", namespaces) is not None
                        else 0
                    )
                ),
            }

        # style 요소 파싱
        for style in self.header_xml.findall(".//hh:style", namespaces):
            style_id = style.get("id")
            if not style_id:
                continue

            # 스타일 정보 추출
            style_info[f"style-{style_id}"] = {
                "type": style.get("type", ""),
                "name": style.get("name", ""),
                "engName": style.get("engName", ""),
                "paraPrIDRef": style.get("paraPrIDRef", ""),
                "charPrIDRef": style.get("charPrIDRef", ""),
                "nextStyleIDRef": style.get("nextStyleIDRef", ""),
                "langID": style.get("langID", ""),
                "lockForm": style.get("lockForm", "0") == "1",
            }

        # 파싱 결과 캐시
        self._style_info = style_info
        print("스타일 정보:", style_info)
        return style_info
