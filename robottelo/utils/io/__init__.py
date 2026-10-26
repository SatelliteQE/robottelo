# Helper methods for tests requiring I/0
import hashlib
import json
from pathlib import Path
import tarfile

# Temporary download directory for hammer CLI insights reports
INSIGHTS_REPORTS_DOWNLOAD_DIR = '/tmp/insights_reports'
generated_reports_dir = (
    '/var/lib/containers/storage/volumes/foreman-data-run/_data/red_hat_inventory/generated_reports'
)
done_dir = (
    '/var/lib/containers/storage/volumes/foreman-data-run/_data/red_hat_inventory/uploads/done'
)


def get_local_file_data(path):
    """Returns information about tar file.

    Args:
        path: path to tar file
    """
    size = Path(path).stat().st_size

    with open(path, 'rb') as fh:
        file_content = fh.read()
    checksum = hashlib.sha256(file_content).hexdigest()

    try:
        with tarfile.open(path, mode='r') as tarobj:
            host_counts = get_host_counts(tarobj)
            extractable = True
            json_files_parsable = True
    except (tarfile.TarError, json.JSONDecodeError):
        host_counts = {}
        extractable = False
        json_files_parsable = False

    return {
        'size': size,
        'checksum': checksum,
        'extractable': extractable,
        'json_files_parsable': json_files_parsable,
        **host_counts,
    }


def get_host_counts(tarobj):
    """Returns hosts count from tar file.

    Args:
        tarobj: tar file to get host count from
    """
    metadata_counts = {}
    slices_counts = {}
    for file_ in tarobj.getmembers():
        file_name = Path(file_.name).name
        if not file_name.endswith('.json'):
            continue
        json_data = json.load(tarobj.extractfile(file_))
        if file_name == 'metadata.json':
            metadata_counts = {
                f'{key}.json': value['number_hosts']
                for key, value in json_data['report_slices'].items()
            }
        else:
            slices_counts[file_name] = len(json_data['hosts'])

    return {
        'metadata_counts': metadata_counts,
        'slices_counts': slices_counts,
    }


def get_remote_report_checksum(satellite, remote_path):
    """Returns checksum of red_hat_inventory report present on satellite.

    Args:
        satellite: satellite host
        remote_path: path to report file on the satellite
    """
    # Use provided path (e.g., from hammer download-report)
    result = satellite.execute(f'sha256sum {remote_path}')
    if result.status == 0:
        checksum, _ = result.stdout.split(maxsplit=1)
        return checksum
    return None


def get_report_data(report_path):
    """Returns report data from tar file.

    Args:
        tarobj: tar file to get report data from
    """
    json_data = {}
    with tarfile.open(report_path, mode='r') as tarobj:
        for file_ in tarobj.getmembers():
            file_name = Path(file_.name).name
            if not file_name.endswith('.json'):
                continue
            if file_name != 'metadata.json':
                json_data = json.load(tarobj.extractfile(file_))
    return json_data


def get_report_metadata(report_path):
    """Returns metadata.json contents from the report

    Args:
        report_path: path to tar file
    """
    json_meta_data = {}
    with tarfile.open(report_path, mode='r') as tarobj:
        for file_ in tarobj.getmembers():
            file_name = Path(file_.name).name
            if file_name == 'metadata.json':
                json_meta_data = json.load(tarobj.extractfile(file_))
    return json_meta_data
