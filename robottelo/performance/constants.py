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
RAW_AK_FILE_NAME = 'raw-ak-concurrent.csv'
RAW_ATT_FILE_NAME = 'raw-att-concurrent.csv'
RAW_DEL_FILE_NAME = 'raw-del-concurrent.csv'
STAT_AK_FILE_NAME = 'stat-ak-concurrent.csv'
STAT_ATT_FILE_NAME = 'stat-att-concurrent.csv'
STAT_DEL_FILE_NAME = 'stat-del-concurrent.csv'

# parameters for number of threads/clients
NUM_THREADS = '1,2,4,6,8,10'
