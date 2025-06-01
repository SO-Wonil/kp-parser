#!/usr/bin/env python3
"""
한글 문서(.hwpx) 파싱 메인 스크립트
"""

import argparse
import os
import json
import re
from pathlib import Path
from typing import Dict, Any, List, Union
from xml.etree import ElementTree

from kp_parser import ContentHpfParser, HeaderXmlParser, SectionXmlParser
from kp_parser.utils.file_utils import extract_hwpx_content
from kp_parser.utils.config_utils import get_parsing_rule


def sanitize_filename(name: str) -> str:
    """윈도우나 리눅스에서 파일/폴더 이름에 쓸 수 없는 문자 제거 및 기호 주변 공백 제거"""
    # 먼저 파일명에 사용할 수 없는 문자를 언더스코어로 변경
    name = re.sub(r'[\\/*?:"<>|]', "_", name)
    # 문자 사이의 하이픈과 가운뎃점 주변 공백 제거 (기호는 유지)
    name = re.sub(r"(\S)\s*([-·])\s*(\S)", r"\1\2\3", name)
    return name.strip()


def save_parsed_data(output_dir: str, parsed_data: List[Dict[str, Any]]) -> None:
    """파싱된 데이터를 각 의약품별 폴더에 저장

    Args:
        output_dir (str): 출력 디렉토리
        parsed_data (List[Dict[str, Any]]): 파싱된 데이터
    """
    for item in parsed_data:
        # 의약품명으로 폴더명 생성
        folder_name = sanitize_filename(item.get("title", "untitled"))
        folder_path = os.path.join(output_dir, folder_name)
        os.makedirs(folder_path, exist_ok=True)

        # 메타데이터 저장
        metadata = {
            "chapter": item.get("chapter"),
            "section": item.get("section"),
            "title": item.get("title"),
            "subtitle": item.get("subtitle"),
            "order": item.get("order"),
        }
        metadata_path = os.path.join(folder_path, "metadata.json")
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)

        # 내용 저장
        content = {
            "root": {
                "direction": "ltr",
                "format": "",
                "indent": 0,
                "type": "root",
                "version": 1,
                "children": item.get("content", []),
            }
        }
        content_path = os.path.join(folder_path, "data.json")
        with open(content_path, "w", encoding="utf-8") as f:
            json.dump(content, f, ensure_ascii=False, indent=2)


def main():
    parser = argparse.ArgumentParser(description="HWPX 파일 파싱")
    parser.add_argument("input_file", help="입력 HWPX 파일 경로")
    parser.add_argument(
        "--output-dir", default="data/output/result", help="출력 디렉토리 경로"
    )
    parser.add_argument("--debug", action="store_true", help="디버그 모드 활성화")
    args = parser.parse_args()

    # 입력 파일 경로 설정
    input_file = Path(args.input_file)
    if not input_file.exists():
        print(f"입력 파일을 찾을 수 없습니다: {input_file}")
        return

    # 출력 디렉토리 생성
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # HWPX 파일 압축 해제 및 내용 로드
    content_map = extract_hwpx_content(
        str(input_file),
        extract_dir=str(output_dir.parent / "tmp"),
        debug=args.debug,
    )

    # header.xml 파싱
    header_parser = HeaderXmlParser()
    header_xml = content_map.get("Contents/header.xml")
    style_info: Dict[str, Any] = {}
    if header_xml is not None:
        if isinstance(header_xml, (str, ElementTree.Element)):
            style_info = header_parser.parse(header_xml)

    # section0.xml 파싱
    section_parser = SectionXmlParser()
    section0_xml = content_map.get("Contents/section0.xml")
    if section0_xml is not None and isinstance(
        section0_xml, (str, ElementTree.Element)
    ):
        # content.hpf에서 이미지 정보 가져오기
        content_parser = ContentHpfParser()
        content_hpf = content_map.get("Contents/content.hpf")
        image_info: Dict[str, Any] = {}
        if content_hpf is not None:
            if isinstance(content_hpf, (str, ElementTree.Element)):
                parsed_image_info = content_parser.parse(content_hpf)
                if isinstance(parsed_image_info, list):
                    # 이미지 정보를 id를 키로 하는 딕셔너리로 변환
                    image_info = {img["id"]: img for img in parsed_image_info}

        parsed_data = section_parser.parse(
            section0_xml, style_info, image_info, output_dir=str(output_dir)
        )

        # 파싱된 데이터 저장
        save_parsed_data(str(output_dir), parsed_data)

    print(f"파싱이 완료되었습니다. 결과가 {output_dir}에 저장되었습니다.")


if __name__ == "__main__":
    main()
