#!/bin/bash
# 단위 테스트
# wmf, emf -> svg
# libreoffice --headless --convert-to pdf image53.emf
# svg -> png
# inkscape image52.svg --export-type=png --export-width=600 --export-area-drawing

# 기본 디렉토리 설정
BASE_DIR="data/output/output_pages"
# BASE_DIR="data/output/BinData"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="${SCRIPT_DIR}/conversion_$(date +%Y%m%d_%H%M%S).log"

# 변환 시작 로그 기록
echo "Conversion started at $(date)" > "$LOG_FILE"
mkdir -p "${SCRIPT_DIR}/failed_conversions"

# 디렉토리 통계 계산
total_dirs=$(find "$BASE_DIR" -type d | wc -l)
wmf_emf_dirs=$(find "$BASE_DIR" -type d -exec sh -c 'ls "$1"/*.{wmf,emf} 2>/dev/null | grep -q . && echo "$1"' _ {} \; | wc -l)

# 통계 정보 로그 기록
echo "Total directories: $total_dirs" | tee -a "$LOG_FILE"
echo "Directories with WMF/EMF files: $wmf_emf_dirs" | tee -a "$LOG_FILE"
echo "Ratio: $wmf_emf_dirs/$total_dirs" | tee -a "$LOG_FILE"

# 모든 디렉토리 순회
find "$BASE_DIR" -type d | while read -r dir; do
    # WMF/EMF 파일이 있는 디렉토리만 처리
    if ls "$dir"/*.{wmf,emf} 2>/dev/null | grep -q .; then
        echo "Found WMF/EMF files in directory: $dir" | tee -a "$LOG_FILE"
        cd "$dir" || continue

        # 각 WMF/EMF 파일 처리
        for file in *.{wmf,emf}; do
            [ -f "$file" ] || continue

            # 파일명 설정
            base="${file%.*}"
            svg_file="${base}.svg"
            png_file="${base}.png"

            # SVG 변환 시도
            echo "Converting $file to SVG..." | tee -a "$LOG_FILE"
            if libreoffice --headless --convert-to svg "$file" >> "$LOG_FILE" 2>&1 && [ -f "$svg_file" ]; then
                echo "Successfully converted $file to $svg_file" | tee -a "$LOG_FILE"
                
                # SVG를 PNG로 변환
                echo "Converting $svg_file to PNG..." | tee -a "$LOG_FILE"
                if inkscape "$svg_file" --export-type=png --export-width=600 --export-area-drawing >> "$LOG_FILE" 2>&1; then
                    echo "Successfully converted $svg_file to PNG" | tee -a "$LOG_FILE"
                else
                    echo "Failed to convert $svg_file to PNG" | tee -a "$LOG_FILE"
                    cp "$file" "${SCRIPT_DIR}/failed_conversions/$(basename "$dir")_$file"
                fi
            else
                # EMF 파일인 경우 emf2svg-conv 시도
                if [[ "$file" == *.emf ]]; then
                    echo "LibreOffice conversion failed, trying emf2svg-conv..." | tee -a "$LOG_FILE"
                    if emf2svg-conv -i "$file" -o "$svg_file" >> "$LOG_FILE" 2>&1 && [ -f "$svg_file" ]; then
                        echo "Successfully converted $file to $svg_file using emf2svg-conv" | tee -a "$LOG_FILE"
                        
                        # SVG를 PNG로 변환
                        echo "Converting $svg_file to PNG..." | tee -a "$LOG_FILE"
                        if inkscape "$svg_file" --export-type=png --export-width=600 --export-area-drawing >> "$LOG_FILE" 2>&1; then
                            echo "Successfully converted $svg_file to PNG" | tee -a "$LOG_FILE"
                        else
                            echo "Failed to convert $svg_file to PNG" | tee -a "$LOG_FILE"
                            cp "$file" "${SCRIPT_DIR}/failed_conversions/$(basename "$dir")_$file"
                        fi
                    else
                        echo "Failed to convert $file to SVG using emf2svg-conv" | tee -a "$LOG_FILE"
                        cp "$file" "${SCRIPT_DIR}/failed_conversions/$(basename "$dir")_$file"
                    fi
                else
                    echo "Failed to convert $file to SVG" | tee -a "$LOG_FILE"
                    cp "$file" "${SCRIPT_DIR}/failed_conversions/$(basename "$dir")_$file"
                fi
            fi
        done

        # 원래 디렉토리로 돌아가기
        cd - > /dev/null
    fi
done

# 변환 완료 메시지
echo "Conversion completed! Check $LOG_FILE for details."