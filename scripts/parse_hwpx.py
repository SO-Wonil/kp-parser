#!/usr/bin/env python3
"""
한글 문서(.hwpx) 파싱 스크립트

사용법:
    parse <hwpx_file_path> [--debug]
"""

import sys
import argparse
from kp_parser.utils.file_utils import extract_hwpx_content
from kp_parser.core.parser import HwpxDocument


def main():
    parser = argparse.ArgumentParser(description="한글 문서(.hwpx) 파싱")
    parser.add_argument("hwpx_path", help=".hwpx 파일 경로")
    parser.add_argument("--debug", action="store_true", help="디버그 모드 활성화")
    args = parser.parse_args()

    print(f"\n=== {args.hwpx_path} 파일 파싱 시작 ===")

    # 1. .hwpx 파일 압축 해제
    print("\n1. .hwpx 파일 압축 해제 중...")
    content_map = extract_hwpx_content(args.hwpx_path, debug=args.debug)
    print(f"- 추출된 파일 수: {len(content_map)}개")
    print("- 추출된 파일 목록:")
    for filename in content_map.keys():
        print(f"  - {filename}")

    # 2. XML 파싱
    print("\n2. XML 파싱 중...")
    doc = HwpxDocument(content_map)

    # 2-1. 이미지 정보 파싱
    print("\n2-1. 이미지 정보 파싱")
    image_info = doc.get_image_info()
    print(f"- 이미지 수: {len(image_info)}개")
    for image_id, info in image_info.items():
        print(f"\n{image_id}:")
        print(f"  - 경로: {info['href']}")
        print(f"  - 타입: {info['media_type']}")
        print(f"  - 임베딩: {info['is_embedded']}")

    # 2-2. 스타일 정보 파싱
    print("\n2-2. 스타일 정보 파싱")
    style_info = doc.get_style_info()

    # charPr 스타일 정보 출력
    char_pr_styles = {k: v for k, v in style_info.items() if k.startswith("charPr-")}
    print(f"- 글자 스타일 수: {len(char_pr_styles)}개")
    for style_id, info in char_pr_styles.items():
        print(f"\n{style_id}:")
        print(f"  - 볼드: {info['bold']}")
        print(f"  - 이탤릭: {info['italic']}")
        print(f"  - 밑줄: {info['underline']}")
        print(f"  - 서식: {info['format']}")

    # style 스타일 정보 출력
    style_styles = {k: v for k, v in style_info.items() if k.startswith("style-")}
    print(f"\n- 스타일 수: {len(style_styles)}개")
    for style_id, info in style_styles.items():
        print(f"\n{style_id}:")
        print(f"  - 타입: {info['type']}")
        print(f"  - 이름: {info['name']}")
        print(f"  - 영문 이름: {info['engName']}")
        print(f"  - 문단 스타일 ID: {info['paraPrIDRef']}")
        print(f"  - 글자 스타일 ID: {info['charPrIDRef']}")
        print(f"  - 다음 스타일 ID: {info['nextStyleIDRef']}")
        print(f"  - 언어 ID: {info['langID']}")
        print(f"  - 잠금: {info['lockForm']}")


if __name__ == "__main__":
    main()
