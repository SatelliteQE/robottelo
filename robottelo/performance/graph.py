"""Test utilities for generating charts for both Candlepin and Pulp tests"""
import pygal


def generate_bar_chart_stat(stat_dict, head, filename, lengend):
    """Generate Bar chart for stat on concurrent subscription

    :param dict stat_dict: The dictionary containing min/median/max/std
    :param str head: Titile of charts
    :param str filename: The name of output svg chart
    :param str lengend: The lengend of generated bar charts

    """
    bar_chart = pygal.Bar()
    bar_chart.title = head
    bar_chart.x_labels = ('min', 'median', 'max', 'std')
    bar_chart.x_title = 'Statistics'
    bar_chart.y_title = 'Time (s)'
    for key in range(len(stat_dict)):
        bar_chart.add('{0}-{1}'.format(lengend, key), stat_dict.get(key))
    bar_chart.render_to_file(filename)


def generate_line_chart_bucketized_stat(
        stat_dict,
        head,
        filename,
        bucket_size,
        num_buckets):
    """Generate Line chart for stat on concurrent subscription

    Take a dictionary of statistic values on each client. For example::

    0: [min, | median,max,std]
    1: [min, | median,max,std]
    2: [min, | median,max,std]
    ...
    9: [min, | median,max,std],

    it would slice out all min, then all median, all max, and all std
    sequentially, form 4 lines on the chart, where each line represented
    by 10 timing points.

    :param dict stat_dict: The dictionary containing min/median/max/std
    :param str head: Titile of charts
    :param str filename: The name of output svg chart
    :param int bucket_size: Number of timing values grouped in each bucket
    :param int num_buckets: Number of buckets of the test; default 10

    """
    if bucket_size == 0:
        return

    # parameters for formats on charts
    lengend = ('min', 'median', 'max', 'std')
    buckets = [
        '{0}-{1}'.format(bucket_size * i + 1, bucket_size * (i + 1))
        for i in range(num_buckets)
    ]
    line_chart = pygal.Line()
    line_chart.title = head
    line_chart.x_labels = buckets
    line_chart.x_title = 'Buckets'
    line_chart.y_title = 'Time (s)'
    for i in len(lengend):
        line_chart.add(lengend[i], (vlist[i] for vlist in stat_dict.values()))
    line_chart.render_to_file(filename)


def generate_stacked_line_chart_raw(time_result_dict, head, filename):
    """Generate Stacked-Line chart for raw data of ak/att/del/reg

    :param dict stat_dict: The dictionary containing min/median/max/std
    :param str head: Titile of charts
    :param str filename: The name of output svg chart

    """
    stackedline_chart = pygal.StackedLine(
        fill=True,
        show_dots=False,
        range=(0, 60),
    )
    max_label = len(time_result_dict.get('thread-0'))
    stackedline_chart.x_labels = [str(i) for i in range(1, max_label + 1)]
    stackedline_chart.title = head
    stackedline_chart.x_title = 'Iterations'
    stackedline_chart.y_title = 'Time (s)'
    # for each client, add time list into chart
    for thread in range(len(time_result_dict)):
        key = 'thread-{}'.format(thread)
        time_list = time_result_dict.get(key)
        stackedline_chart.add('client-{}'.format(thread), time_list)
    stackedline_chart.render_to_file(filename)


def generate_line_chart_raw(time_result_dict, head, filename):
    """Generate Normal Line chart for raw data of ak/att/del/reg

    :param dict stat_dict: The dictionary containing min/median/max/std
    :param str head: Titile of charts
    :param str filename: The name of output svg chart

    """
    line_chart = pygal.Line(show_dots=False, range=(0, 50))
    max_label = len(time_result_dict.get('thread-0'))
    line_chart.x_labels = [str(i) for i in range(1, max_label + 1)]
    line_chart.title = head
    line_chart.x_title = 'Iterations'
    line_chart.y_title = 'Time (s)'
    # for each client, add time list into chart
    for thread in range(len(time_result_dict)):
        key = 'thread-{}'.format(thread)
        time_list = time_result_dict.get(key)
        line_chart.add('client-{}'.format(thread), time_list)
    line_chart.render_to_file(filename)
