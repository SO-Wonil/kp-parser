#!/bin/bash

# 기본 디렉토리 설정
BASE_DIR="data/output/output_pages"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="${SCRIPT_DIR}/conversion_$(date +%Y%m%d_%H%M%S).log"

# 로그 파일 초기화
echo "Conversion started at $(date)" > "$LOG_FILE"

# 실패한 변환을 저장할 디렉토리 생성
mkdir -p "${SCRIPT_DIR}/failed_conversions"

# 전체 디렉토리 수 계산
total_dirs=$(find "$BASE_DIR" -type d | wc -l)
wmf_emf_dirs=$(find "$BASE_DIR" -type d -exec sh -c 'ls "$1"/*.{wmf,emf} 2>/dev/null | grep -q . && echo "$1"' _ {} \; | wc -l)

echo "Total directories: $total_dirs" | tee -a "$LOG_FILE"
echo "Directories with WMF/EMF files: $wmf_emf_dirs" | tee -a "$LOG_FILE"
echo "Ratio: $wmf_emf_dirs/$total_dirs" | tee -a "$LOG_FILE"

# WMF/EMF 파일이 포함된 폴더 처리
find "$BASE_DIR" -type d | while read -r dir; do
    if ls "$dir"/*.{wmf,emf} 2>/dev/null | grep -q .; then
        echo "Found WMF/EMF files in directory: $dir" | tee -a "$LOG_FILE"
        cd "$dir" || continue

        for file in *.{wmf,emf}; do
            [ -f "$file" ] || continue

            base="${file%.*}"
            svg_file="${base}.svg"

            echo "Converting $file to SVG..." | tee -a "$LOG_FILE"
            if libreoffice --headless --convert-to svg "$file" >> "$LOG_FILE" 2>&1; then
                echo "Successfully converted $file to $svg_file" | tee -a "$LOG_FILE"
                
                echo "Converting $svg_file to PNG..." | tee -a "$LOG_FILE"
                if inkscape "$svg_file" --export-type=png --export-width=600 --export-area-drawing >> "$LOG_FILE" 2>&1; then
                    echo "Successfully converted $svg_file to PNG" | tee -a "$LOG_FILE"
                else
                    echo "Failed to convert $svg_file to PNG" | tee -a "$LOG_FILE"
                    cp "$file" "${SCRIPT_DIR}/failed_conversions/$(basename "$dir")_$file"
                fi
            else
                echo "Failed to convert $file to SVG" | tee -a "$LOG_FILE"
                cp "$file" "${SCRIPT_DIR}/failed_conversions/$(basename "$dir")_$file"
            fi
        done

        cd - > /dev/null
    fi
done

echo "Conversion completed! Check $LOG_FILE for details."