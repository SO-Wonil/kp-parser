from typing import Dict, Any, Optional, Union, List
from xml.etree import ElementTree
import re
import os
import base64

from kp_parser.utils.config_utils import get_parsing_rule


class SectionXmlParser:
    """section{n}.xml 파일을 파싱하는 클래스"""

    def __init__(self, config_name: str = "drug_manual_part2/parsing_rules"):
        """초기화

        Args:
            config_name (str, optional): 파싱 규칙 설정 파일 이름. Defaults to "drug_manual_part2/parsing_rules".
        """
        self.config_name = config_name
        self.rules = get_parsing_rule("section_xml", config_name)
        if not self.rules:
            raise ValueError(f"section_xml 파싱 규칙을 찾을 수 없습니다.")
        self.namespaces = self.rules["namespaces"]

    def _extract_text(self, p_elem: ElementTree.Element) -> str:
        """문단에서 텍스트를 추출

        Args:
            p_elem (ElementTree.Element): 문단 요소

        Returns:
            str: 추출된 텍스트
        """
        # run 태그 내의 모든 t 태그를 찾아서 텍스트 추출
        text_parts = []
        for run in p_elem.findall(".//hp:run", self.namespaces):
            for t in run.findall(".//hp:t", self.namespaces):
                if t.text and t.text.strip():
                    text_parts.append(t.text.strip())
        return " ".join(text_parts)

    def _is_korean(self, text: str) -> bool:
        """텍스트가 한글을 포함하는지 확인

        Args:
            text (str): 확인할 텍스트

        Returns:
            bool: 한글 포함 여부
        """
        return any("\uac00" <= char <= "\ud7a3" for char in text)

    def _process_image_in_paragraph(
        self, run: ElementTree.Element, image_info: Dict[str, Any], folder_path: str
    ) -> Optional[Dict[str, Any]]:
        """문단 내의 이미지를 처리

        Args:
            run (ElementTree.Element): run 태그
            image_info (Dict[str, Any]): 이미지 정보
            folder_path (str): 이미지 저장 경로

        Returns:
            Optional[Dict[str, Any]]: 이미지 노드 또는 None
        """
        pic_tag = run.find("./hp:pic", self.namespaces)
        if not pic_tag:
            return None

        # 모든 자식 요소를 순회하면서 img 태그 찾기
        for child in pic_tag:
            if child.tag.endswith("}img"):
                img_tag = child
                break
        else:
            print(f"img_tag not found in pic_tag: {pic_tag}")
            return None

        img_id = img_tag.get("binaryItemIDRef")
        if not img_id:
            return None

        image_meta = image_info.get(img_id)
        if not image_meta:
            print(f"Image meta not found for ID: {img_id}")
            return None

        # href 대신 path 사용
        href = image_meta.get("path")
        if not href:
            print(f"path not found in image_meta: {image_meta}")
            return None

        print(f"Found href: {href}")

        extension = os.path.splitext(href)[-1].lower()
        print(f"File extension: {extension}")

        # 원본 이미지 경로 (BinData 폴더에서 찾기)
        source_path = os.path.join("data/tmp/BinData", os.path.basename(href))

        if not os.path.exists(source_path):
            print(f"이미지 파일을 찾을 수 없습니다: {source_path}")
            return None

        # 저장 대상 경로 (의약품별 폴더)
        target_path = os.path.join(folder_path, os.path.basename(href))

        with open(source_path, "rb") as img_f:
            image_data = img_f.read()
            print(f"Read {len(image_data)} bytes from source file")

        # 파일 저장
        with open(target_path, "wb") as out_f:
            out_f.write(image_data)
            print(f"Wrote {len(image_data)} bytes to target file")

        # base64 인코딩 (표시 가능한 포맷만)
        if extension in [".png", ".jpg", ".jpeg", ".gif", ".bmp"]:
            mime = f"image/{extension[1:]}" if extension != ".jpg" else "image/jpeg"
            encoded_data = base64.b64encode(image_data).decode("utf-8")
            src = f"data:{mime};base64,{encoded_data}"
        else:
            src = None

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

    def _process_equation_in_paragraph(
        self, run: ElementTree.Element
    ) -> Optional[Dict[str, Any]]:
        """문단 내의 수식을 처리

        Args:
            run (ElementTree.Element): run 태그

        Returns:
            Optional[Dict[str, Any]]: 수식 노드 또는 None
        """
        equation_tag = run.find(".//hp:equation", self.namespaces)
        if not equation_tag:
            return None

        return {
            "detail": 0,
            "format": 1,  # 볼드체
            "mode": "normal",
            "style": "color: #ff0000;",  # 빨간색
            "text": "수식",
            "type": "text",
            "version": 1,
        }

    def _build_paragraph(
        self, p_elem: ElementTree.Element, style_info: Dict[str, Any], folder_path: str
    ) -> Dict[str, Any]:
        """문단을 빌드

        Args:
            p_elem (ElementTree.Element): 문단 요소
            style_info (Dict[str, Any]): 스타일 정보
            folder_path (str): 이미지 저장 경로

        Returns:
            Dict[str, Any]: 문단 노드
        """
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

        for run in p_elem.findall(".//hp:run", self.namespaces):
            char_pr_id = run.get("charPrIDRef")
            style = style_info.get(f"charPr-{char_pr_id}", {}) if char_pr_id else {}

            format_flag = 0
            if style.get("bold"):
                format_flag = 1
            elif style.get("italic"):
                format_flag = 2
            elif style.get("underline"):
                format_flag = 4
            else:
                format_flag = style.get("format", 0)

            # 이미지 처리
            image_node = self._process_image_in_paragraph(
                run, self.image_info, folder_path
            )

            if image_node:
                paragraph["children"].append(image_node)

            # 수식 처리
            equation_node = self._process_equation_in_paragraph(run)
            if equation_node:
                paragraph["children"].append(equation_node)

            # 텍스트 처리
            for t in run.findall(".//hp:t", self.namespaces):
                if t.text and t.text.strip():
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

    def parse(
        self,
        xml_content: Union[str, ElementTree.Element],
        style_info: Dict[str, Any],
        image_info: Dict[str, Any],
        output_dir: str = "data/output/result",
    ) -> List[Dict[str, Any]]:
        """XML 내용을 파싱하여 메타데이터와 내용을 추출

        Args:
            xml_content (Union[str, ElementTree.Element]): XML 내용 (문자열 또는 ElementTree.Element)
            style_info (Dict[str, Any]): 스타일 정보
            image_info (Dict[str, Any]): 이미지 정보
            output_dir (str): 출력 디렉토리 경로

        Returns:
            List[Dict[str, Any]]: 추출된 메타데이터와 내용 목록
        """
        self.style_info = style_info
        self.image_info = image_info
        self.output_dir = output_dir

        # XML 파싱 (문자열인 경우에만)
        root = (
            xml_content
            if isinstance(xml_content, ElementTree.Element)
            else ElementTree.fromstring(xml_content)
        )

        # 모든 문단 찾기
        paragraphs = root.findall(".//hp:p", self.namespaces)
        result = []
        current_metadata = {}
        current_section = None
        current_content = []
        i = 0
        order = 1  # 의약품 순서

        while i < len(paragraphs):
            p = paragraphs[i]
            style_id = p.get("styleIDRef", "").replace("style-", "")

            # 카테고리 문단 확인
            if (
                style_id
                == self.rules["metadata_extraction"]["section"]["conditions"][
                    "styleIDRef"
                ]
            ):
                text = self._extract_text(p)
                if text:
                    current_section = text
                    order = 1  # 섹션이 바뀔 때마다 order 초기화

            # 의약품 제목 문단 확인 (textheight가 1100인 경우)
            lineseg = p.find(".//hp:lineseg", self.namespaces)
            if lineseg is not None and lineseg.get("textheight") == "1100":
                # 이전 메타데이터와 내용이 있으면 저장
                if current_metadata:
                    result.append({**current_metadata, "content": current_content})

                # 새로운 메타데이터와 내용 시작
                first_text = self._extract_text(p)
                second_text = (
                    self._extract_text(paragraphs[i + 1])
                    if i + 1 < len(paragraphs)
                    else ""
                )

                # 한글/영문 구분하여 제목/부제목 설정
                if self._is_korean(first_text):
                    current_metadata = {
                        "chapter": self.rules["metadata_extraction"][
                            "chapter"
                        ],  # 챕터 정보 추가
                        "section": current_section,  # 현재 섹션 포함
                        "title": first_text,
                        "subtitle": second_text,
                        "order": order,
                    }
                else:
                    current_metadata = {
                        "chapter": self.rules["metadata_extraction"][
                            "chapter"
                        ],  # 챕터 정보 추가
                        "section": current_section,  # 현재 섹션 포함
                        "title": second_text,
                        "subtitle": first_text,
                        "order": order,
                    }
                current_content = []
                order += 1
                i += 2
                continue

            # 일반 문단 처리
            else:
                # 이미지 저장 경로는 main.py에서 설정한 output_dir을 사용
                folder_path = os.path.join(
                    self.output_dir,
                    current_metadata.get("title", "untitled"),
                )
                os.makedirs(folder_path, exist_ok=True)
                para = self._build_paragraph(p, style_info, folder_path)
                if para["children"]:
                    current_content.append(para)

            i += 1

        # 마지막 메타데이터와 내용 추가
        if current_metadata:
            result.append({**current_metadata, "content": current_content})

        return result
