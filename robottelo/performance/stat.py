"""Test utilities for writing csv files"""
import csv
import numpy


def generate_stat_for_concurrent_thread(thread_name, time_list,
                                        stat_file_name, bucket_size,
                                        num_buckets):
    num_buckets = len(time_list)/bucket_size

    # create list of bucket series
    buckets = ['{0}-{1}'.format(bucket_size * i + 1, bucket_size * (i + 1))
               for i in range(num_buckets)]

    with open(stat_file_name, 'a') as handler:
        writer = csv.writer(handler)
        writer.writerow([])
        writer.writerow(['{}'.format(thread_name)])
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
            time_list_slice = time_list[bucket_size * i:bucket_size * (i + 1)]
            writer.writerow([
                bucket,
                numpy.amin(time_list_slice),
                numpy.median(time_list_slice),
                numpy.mean(time_list_slice),
                numpy.amax(time_list_slice),
                numpy.std(time_list_slice),
                numpy.percentile(time_list_slice, 90),
                numpy.percentile(time_list_slice, 95),
                numpy.percentile(time_list_slice, 99)
            ])
