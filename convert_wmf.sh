#!/bin/bash

# 기본 디렉토리 설정
BASE_DIR="data/output/output_pages"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="${SCRIPT_DIR}/conversion_$(date +%Y%m%d_%H%M%S).log"

# 로그 파일 초기화
echo "Conversion started at $(date)" > "$LOG_FILE"

# 실패한 변환을 저장할 디렉토리 생성
mkdir -p failed_conversions

# 전체 디렉토리 수 계산
total_dirs=$(find "$BASE_DIR" -type d | wc -l)

# WMF/EMF 파일이 있는 디렉토리 수 계산
wmf_emf_dirs=$(find "$BASE_DIR" -type d -exec sh -c 'ls "$1"/*.{wmf,emf} 2>/dev/null | grep -q . && echo "$1"' _ {} \; | wc -l)

echo "Total directories: $total_dirs"
echo "Directories with WMF/EMF files: $wmf_emf_dirs"
echo "Ratio: $wmf_emf_dirs/$total_dirs"

# WMF 파일이 포함된 폴더만 찾기
find "$BASE_DIR" -type d | while read -r dir; do
    # 해당 디렉토리에 WMF 또는 EMF 파일이 있는지 확인
    if ls "$dir"/*.{wmf,emf} 2>/dev/null | grep -q .; then
        echo "Found WMF/EMF files in directory: $dir" | tee -a "$LOG_FILE"
        
        # 해당 디렉토리로 이동
        cd "$dir" || continue
        
        # WMF와 EMF 파일 변환
        for file in *.{wmf,emf}; do
            if [ -f "$file" ]; then
                echo "Converting $file to PNG in $(pwd)..." | tee -a "$LOG_FILE"
                if inkscape "$file" --export-type=png --export-area-snap --export-width=600 2>> "$LOG_FILE"; then
                    echo "Successfully converted $file" | tee -a "$LOG_FILE"
                else
                    echo "Failed to convert $file" | tee -a "$LOG_FILE"
                    # 실패한 파일을 별도 디렉토리로 이동
                    cp "$file" "${SCRIPT_DIR}/failed_conversions/$(basename "$dir")_$file"
                fi
            fi
        done
        
        # 원래 디렉토리로 돌아가기
        cd - > /dev/null
    fi
done

echo "Conversion completed! Check $LOG_FILE for details." 