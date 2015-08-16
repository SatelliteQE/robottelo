"""Define constants for performance test utilities"""


# parameter for manifest file name
MANIFEST_FILE_NAME = 'perf-manifest.zip'

# parameters for creating activation key
ACTIVATION_KEY = 'ak-1'
CONTENT_VIEW = 'Default Organization View'
DEFAULT_ORG = 'Default_Organization'
LIFE_CYCLE_ENV = 'Library'

# parameters for adding ak to subscription
QUANTITY = 1

# parameters for register and attach step
ATTACH_ENV = 'Library'

# parameters for csv data files
RAW_AK_FILE_NAME = 'perf-raw-activationKey.csv'
RAW_ATT_FILE_NAME = 'perf-raw-attach.csv'
RAW_DEL_FILE_NAME = 'perf-raw-delete.csv'
RAW_REG_FILE_NAME = 'perf-raw-register.csv'
STAT_AK_FILE_NAME = 'perf-statistics-activationKey.csv'
STAT_ATT_FILE_NAME = 'perf-statistics-attach.csv'
STAT_DEL_FILE_NAME = 'perf-statistics-delete.csv'
STAT_REG_FILE_NAME = 'perf-statistics-register.csv'

RAW_SYNC_FILE_NAME = 'perf-raw-sync.csv'
STAT_SYNC_FILE_NAME = 'perf-statistics-sync.csv'

# parameters for number of threads/clients
NUM_THREADS = '1,2,4,6,8,10'
