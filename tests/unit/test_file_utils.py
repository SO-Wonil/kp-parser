import os
import pytest
from kp_parser.utils import extract_hwpx_content


def test_extract_hwpx_content_debug_mode():
    """디버그 모드에서의 extract_hwpx_content 테스트"""
    # 테스트용 .hwpx 파일 경로
    test_file = "data/input/test.hwpx"

    # 디버그 모드로 실행 (data/output/tmp에 저장)
    extract_dir = "data/output/tmp"
    result = extract_hwpx_content(test_file, extract_dir=extract_dir, debug=True)

    # 결과 검증
    assert isinstance(result, str)  # debug=True일 때는 문자열(디렉토리 경로) 반환
    assert os.path.exists(result)
    assert os.path.isdir(result)
    # TODO: 추출된 파일들의 존재 여부 확인


def test_extract_hwpx_content_normal_mode(tmp_path):
    """일반 모드에서의 extract_hwpx_content 테스트"""
    # 테스트용 .hwpx 파일 경로
    test_file = "data/input/test.hwpx"

    # 일반 모드로 실행
    extract_dir = str(tmp_path / "test_normal")
    result = extract_hwpx_content(test_file, extract_dir=extract_dir, debug=False)

    # 결과 검증
    assert isinstance(result, dict)
    # Contents/ 또는 BinData/로 시작하는 파일들만 포함되어 있는지 확인
    for filename in result.keys():
        assert filename.startswith(("Contents/", "BinData/"))
