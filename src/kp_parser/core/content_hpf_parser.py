from typing import Dict, List, Any, Union
from xml.etree import ElementTree
from kp_parser.utils.config_utils import get_parsing_rule


class ContentHpfParser:
    """content.hpf 파일 파싱을 위한 전용 파서"""

    def __init__(self, config_name: str = "drug_manual_part2/parsing_rules"):
        """파서 초기화

        Args:
            config_name: 파싱 규칙 설정 파일 이름
        """
        self.config_name = config_name
        self.rules = get_parsing_rule("content_hpf", config_name=self.config_name)
        if not self.rules:
            raise ValueError(f"content_hpf 파싱 규칙을 찾을 수 없습니다.")

    def parse(
        self, xml_content: Union[str, ElementTree.Element]
    ) -> List[Dict[str, Any]]:
        """content.hpf 파일을 파싱합니다.

        Args:
            xml_content: content.hpf 파일의 XML 내용 (문자열 또는 ElementTree.Element)

        Returns:
            List[Dict[str, Any]]: 추출된 이미지 정보 목록
        """
        # XML 파싱 (문자열인 경우에만)
        root = (
            xml_content
            if isinstance(xml_content, ElementTree.Element)
            else ElementTree.fromstring(xml_content)
        )

        # 네임스페이스 설정
        namespaces = self.rules["namespaces"]

        # manifest 태그 찾기
        manifest_path = self.rules["image_extraction"]["manifest"]["path"]
        manifest = root.find(manifest_path, namespaces)
        if manifest is None:
            return []

        # 이미지 항목 추출
        images = []
        item_rules = self.rules["image_extraction"]["item"]
        for item in manifest.findall(item_rules["path"], namespaces):
            # media-type 조건 확인
            media_type = item.get("media-type", "")
            if not media_type.startswith(item_rules["conditions"]["media_type"]):
                continue

            # 이미지 정보 추출
            image_info = {
                "type": item_rules["output_format"]["type"],
                "version": item_rules["output_format"]["version"],
            }

            # 필드 매핑
            for field, attr in item_rules["output_format"]["fields"].items():
                image_info[field] = item.get(attr)

            images.append(image_info)

        return images
