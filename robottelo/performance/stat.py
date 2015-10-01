"""Test utilities for writing csv files"""
import csv
import numpy


def generate_stat_for_concurrent_thread(
        thread_name,
        time_list,
        stat_file_name,
        bucket_size,
        num_buckets):
    """statistics computing utility for Candlepin tests"""
    # check empty case: empty bucket has no need to compute stat
    if bucket_size == 0:
        return
    else:
        num_buckets = len(time_list)/bucket_size

    return_stat = {}

    # create list of bucket series
    buckets = ['{0}-{1}'.format(bucket_size * i + 1, bucket_size * (i + 1))
               for i in range(num_buckets)]

    with open(stat_file_name, 'a') as handler:
        writer = csv.writer(handler)
        writer.writerow([])
        writer.writerow(['{0}'.format(thread_name)])
        writer.writerow([
            'bucket',
            'min',
            'median',
            'mean',
            'max',
            'std',
            '90%',
            '95%',
            '99%'
        ])
        for i, bucket in enumerate(buckets):
            # slice the given time-list into buckets
            time_list_slice = time_list[bucket_size * i:bucket_size * (i + 1)]

            # variables for generating graphs only
            gmin = numpy.amin(time_list_slice)
            gmean = numpy.mean(time_list_slice)
            gmedian = numpy.median(time_list_slice)
            gmax = numpy.amax(time_list_slice)
            gstd = numpy.std(time_list_slice)

            writer.writerow([
                bucket,
                gmin,
                gmedian,
                gmean,
                gmax,
                gstd,
                numpy.percentile(time_list_slice, 90),
                numpy.percentile(time_list_slice, 95),
                numpy.percentile(time_list_slice, 99)
            ])

            # update a dictionary with key as each bucket and values as stat
            return_stat.update({i: (gmin, gmedian, gmax, gstd)})
        return return_stat


def generate_stat_for_pulp_sync(index, time_list, stat_file_name):
    """statistics computing utility for Pulp synchronization tests"""
    with open(stat_file_name, 'a') as handler:
        writer = csv.writer(handler)

        sync_min = numpy.amin(time_list)
        sync_median = numpy.median(time_list)
        sync_max = numpy.amax(time_list)
        sync_std = numpy.std(time_list)

        writer.writerow([
            'test-{0}-threads'.format(index),
            sync_min,
            sync_median,
            sync_max,
            sync_std,
        ])
    return (sync_min, sync_median, sync_max, sync_std)
