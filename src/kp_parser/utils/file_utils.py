import os
import zipfile
from xml.etree import ElementTree
from typing import Dict, Union


def extract_hwpx_content(
    hwpx_path: str, extract_dir: str = "temp", debug: bool = False
) -> Union[Dict[str, Union[ElementTree.Element, bytes]], str]:
    """
    .hwpx 파일의 내용을 추출합니다.

    Args:
        hwpx_path: .hwpx 파일 경로
        extract_dir: 디버그 모드일 때 압축 해제할 디렉토리
        debug: True면 모든 파일을 디스크에 저장, False면 Contents/와 BinData/ 파일만 메모리에 로딩

    Returns:
        Union[Dict[str, Union[ElementTree.Element, bytes]], str]:
            - debug=False: {파일명: ElementTree.Element 또는 bytes}
            - debug=True: 추출된 디렉토리 경로
    """
    if debug:
        # 디버그 모드: 전체 파일 디스크에 저장
        os.makedirs(extract_dir, exist_ok=True)
        with zipfile.ZipFile(hwpx_path, "r") as zip_ref:
            zip_ref.extractall(extract_dir)
        return extract_dir

    # 일반 모드: 메모리에 필요한 것만 로딩 (Contents/ + BinData/)
    content_map = {}
    with zipfile.ZipFile(hwpx_path, "r") as zip_ref:
        for name in zip_ref.namelist():
            if name.startswith(("Contents/", "BinData/")):
                with zip_ref.open(name) as file:
                    raw = file.read()
                    if name.endswith((".xml", ".hpf")):
                        try:
                            content_map[name] = ElementTree.fromstring(
                                raw.decode("utf-8")
                            )
                        except Exception as e:
                            print(f"[!] Failed to parse XML: {name} - {e}")
                    else:
                        content_map[name] = raw
    return content_map
