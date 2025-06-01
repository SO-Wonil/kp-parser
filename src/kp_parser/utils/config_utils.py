import yaml
import os
from typing import Dict, Any


def load_parsing_rules(config_name: str) -> Dict[str, Any]:
    """YAML 설정 파일을 로드합니다.

    Args:
        config_name: 설정 파일 이름 (확장자 제외)

    Returns:
        Dict[str, Any]: 파싱 규칙 딕셔너리
    """
    config_dir = os.path.dirname(os.path.dirname(__file__))
    rules_path = os.path.join(config_dir, "config", f"{config_name}.yaml")

    try:
        with open(rules_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        print(f"Warning: {rules_path} 파일을 찾을 수 없습니다.")
        return {}
    except yaml.YAMLError:
        print(f"Error: {rules_path} 파일의 YAML 형식이 올바르지 않습니다.")
        return {}


def get_parsing_rule(
    rule_path: str, config_name: str = "drug_manual_part2_hwpml_rules"
) -> Any:
    """특정 파싱 규칙을 가져옵니다.

    Args:
        rule_path: 규칙 경로 (예: "content_hpf")
        config_name: 설정 파일 이름 (확장자 제외)

    Returns:
        Any: 파싱 규칙 값
    """
    rules = load_parsing_rules(config_name)
    if not rules:
        return None

    try:
        for key in rule_path.split("."):
            rules = rules[key]
        return rules
    except (KeyError, TypeError):
        return None
