import os
import zipfile
import fnmatch
import re
from xml.etree import ElementTree
from typing import Dict, Union, Optional, List, Tuple
from kp_parser.utils.logger import logger


def extract_hwpx_content(
    hwpx_path: str,
    pattern: Optional[str] = None,
    extract_dir: str = "data/output/tmp",
    debug: bool = False,
) -> Dict[str, Union[ElementTree.Element, bytes]]:
    """
    .hwpx 파일의 내용을 추출합니다.

    Args:
        hwpx_path: .hwpx 파일 경로
        pattern: 파일 이름 패턴 (예: "section*.xml")
        extract_dir: 디버그 모드일 때 압축 해제할 디렉토리
        debug: True면 메모리에 저장하고 추가로 디스크에도 저장, False면 메모리에만 저장

    Returns:
        Dict[str, Union[ElementTree.Element, bytes]]: 파일 경로를 키로, XML Element 또는 바이너리 데이터를 값으로 하는 딕셔너리
    """
    logger.info(f"HWPX 파일 압축 해제 시작: {hwpx_path}")

    # 메모리에 파일 로딩 (Contents/ + BinData/)
    content_map = {}

    with zipfile.ZipFile(hwpx_path, "r") as zip_ref:
        # 먼저 모든 파일 목록을 가져옵니다
        all_files = zip_ref.namelist()

        # section 파일들을 찾고 정렬합니다
        section_pattern = re.compile(r"Contents/section(\d+)\.xml")
        section_files = []
        for f in all_files:
            match = section_pattern.match(f)
            if match:
                section_files.append((int(match.group(1)), f))

        # section 번호로 정렬
        section_files.sort(key=lambda x: x[0])
        section_files = [f[1] for f in section_files]  # 파일 경로만 추출

        logger.debug(f"발견된 section 파일들: {section_files}")

        # 모든 파일 처리
        for name in all_files:
            if name.startswith(("Contents/", "BinData/")):
                # 패턴이 지정된 경우 매칭되는 파일만 처리
                if pattern and not fnmatch.fnmatch(name, f"Contents/{pattern}"):
                    continue

                logger.debug(f"파일 로딩 중: {name}")
                with zip_ref.open(name) as file:
                    raw = file.read()
                    if name.endswith((".xml", ".hpf")):
                        try:
                            content_map[name] = ElementTree.fromstring(
                                raw.decode("utf-8")
                            )
                            logger.debug(f"XML 파싱 성공: {name}")
                        except Exception as e:
                            logger.error(f"XML 파싱 실패: {name} - {e}")
                    else:
                        content_map[name] = raw
                        logger.debug(f"바이너리 데이터 로딩 완료: {name}")

    # 디버그 모드일 경우 추가로 디스크에 저장
    if debug:
        os.makedirs(extract_dir, exist_ok=True)
        with zipfile.ZipFile(hwpx_path, "r") as zip_ref:
            zip_ref.extractall(extract_dir)
        logger.info(f"파일이 {extract_dir}에 저장되었습니다.")

    logger.info(
        f"로딩된 파일 수: {len(content_map)}, section 파일 수: {len(section_files)}"
    )
    return content_map
