import logging
import sys
from typing import Optional
from colorama import Fore, Style, init

# colorama 초기화
init()


class ColoredFormatter(logging.Formatter):
    """색상이 있는 로그 포맷터"""

    COLORS = {
        "DEBUG": Fore.BLUE,
        "INFO": Fore.GREEN,
        "WARNING": Fore.YELLOW,
        "ERROR": Fore.RED,
        "CRITICAL": Fore.RED + Style.BRIGHT,
    }

    def format(self, record):
        # 로그 레벨에 따른 색상 적용
        color = self.COLORS.get(record.levelname, Fore.WHITE)
        record.levelname = f"{color}{record.levelname}{Style.RESET_ALL}"
        record.msg = f"{color}{record.msg}{Style.RESET_ALL}"
        return super().format(record)


def setup_logger(
    name: str = "kp_parser", level: int = logging.INFO, log_file: Optional[str] = None
) -> logging.Logger:
    """로거를 설정하고 반환합니다.

    Args:
        name (str): 로거 이름
        level (int): 로깅 레벨
        log_file (Optional[str]): 로그 파일 경로 (None이면 콘솔에만 출력)

    Returns:
        logging.Logger: 설정된 로거
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # 이미 핸들러가 있다면 제거
    if logger.handlers:
        logger.handlers.clear()

    # 콘솔 핸들러 (색상 적용)
    console_handler = logging.StreamHandler(sys.stdout)
    console_formatter = ColoredFormatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # 파일 핸들러 (색상 없음)
    if log_file:
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

    return logger


# 기본 로거 인스턴스
logger = setup_logger()
