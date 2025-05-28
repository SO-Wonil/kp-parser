from kp_parser.utils.file_utils import extract_hwpx_content
from typing import Dict, Union
from xml.etree import ElementTree

if __name__ == "__main__":
    # 분석할 파일 경로
    hwpx_path = "data/input/test.hwpx"

    # 일반 모드로 실행 (debug=False)
    content_map: Union[Dict[str, Union[ElementTree.Element, bytes]], str] = (
        extract_hwpx_content(hwpx_path, debug=False)
    )

    # 메모리에 저장된 파일 목록 출력
    print("\n[메모리에 저장된 파일 목록]")
    if isinstance(content_map, dict):
        for filename in content_map.keys():
            print(f"- {filename}")

        # XML 파일의 루트 태그 출력
        print("\n[XML 파일 루트 태그]")
        for filename, content in content_map.items():
            if filename.endswith((".xml", ".hpf")):
                if isinstance(content, ElementTree.Element):
                    print(f"{filename}: {content.tag}")
                else:
                    print(f"{filename}: 바이너리 데이터")
    else:
        print("디버그 모드로 실행되었습니다. 파일이 디스크에 저장되었습니다.")
