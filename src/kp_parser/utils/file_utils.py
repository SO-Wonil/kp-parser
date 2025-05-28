import os
import zipfile
from xml.etree import ElementTree
from typing import Dict, Union


def extract_hwpx_content(
    hwpx_path: str, extract_dir: str = "temp", debug: bool = False
) -> Dict[str, Union[ElementTree.Element, bytes]]:
    """
    .hwpx 파일의 내용을 추출합니다.

    Args:
        hwpx_path: .hwpx 파일 경로
        extract_dir: 디버그 모드일 때 압축 해제할 디렉토리
        debug: True면 메모리에 저장하고 추가로 디스크에도 저장, False면 메모리에만 저장

    Returns:
        Dict[str, Union[ElementTree.Element, bytes]]: 파일 경로를 키로, XML Element 또는 바이너리 데이터를 값으로 하는 딕셔너리
    """
    # 메모리에 파일 로딩 (Contents/ + BinData/)
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

    # 디버그 모드일 경우 추가로 디스크에 저장
    if debug:
        os.makedirs(extract_dir, exist_ok=True)
        with zipfile.ZipFile(hwpx_path, "r") as zip_ref:
            zip_ref.extractall(extract_dir)
        print(f"[디버그] 파일이 {extract_dir}에 저장되었습니다.")

    return content_map
