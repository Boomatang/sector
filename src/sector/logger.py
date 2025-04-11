import logging


def configure(debug: bool = False) -> None:
    level = logging.INFO
    handlers = [logging.FileHandler("sector.log")]
    if debug:
        level = logging.DEBUG
        # handlers.append(logging.StreamHandler(sys.stdout))
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=handlers,
    )
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)


def get_logger(name: str | None = None) -> logging.Logger:
    if name:
        return logging.getLogger(name)
    return logging.getLogger()
