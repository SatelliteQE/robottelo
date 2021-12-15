import logging
import os
from pathlib import Path

import logzero
import yaml
from box import Box


robottelo_root_dir = Path(os.environ.get('ROBOTTELO_DIR', Path(__file__).resolve().parent.parent))
robottelo_log_dir = robottelo_root_dir.joinpath('logs')
robottelo_log_file = robottelo_log_dir.joinpath('robottelo.log')
robottelo_log_file.parent.mkdir(parents=True, exist_ok=True)

with robottelo_root_dir.joinpath('logging.yaml').open() as f:
    logging_yaml = Box(yaml.load(f, yaml.FullLoader))

DEFAULT_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

defaultFormatter = logzero.LogFormatter(
    fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt=DEFAULT_DATE_FORMAT
)

logger = logzero.setup_logger(
    level=logging_yaml.robottelo.level,
    logfile=str(robottelo_log_file),
    fileLoglevel=logging_yaml.robottelo.fileLevel,
    isRootLogger=True,
    formatter=defaultFormatter,
    maxBytes=1e8,  # 100MB
    backupCount=3,
)
# if name is passed during setup, then imported uses of this root logger won't have name set
logger.name = 'robottelo'


def configure_third_party_logging():
    """Increase the level of third party packages logging."""
    logger_names = (
        'airgun',
        'awxkit',
        'broker',
        'easyprocess',
        'nailgun',
        'requests.packages.urllib3.connectionpool',
        'robozilla',
        'selenium.webdriver.remote.remote_connection',
        'widgetastic_null',
        'navmazing_null',
    )

    for logger_name in logger_names:
        logger_levels = logging_yaml.get(logger_name) or logging_yaml.get('other')
        logging.getLogger(logger_name).setLevel(logger_levels['fileLevel'])


configure_third_party_logging()


collection_logger = logzero.setup_logger(
    name='robottelo.collection',
    level=logging_yaml.collection.level,
    logfile=str(robottelo_log_file),
    fileLoglevel=logging_yaml.collection.fileLevel,
    formatter=defaultFormatter,
)


config_logger = logzero.setup_logger(
    name='robottelo.config',
    level=logging_yaml.config.level,
    logfile=robottelo_log_file,
    fileLoglevel=logging_yaml.config.fileLevel,
    formatter=defaultFormatter,
)
