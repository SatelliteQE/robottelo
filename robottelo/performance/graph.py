"""Test utilities for generating charts for both Candlepin and Pulp tests"""
import pygal


def generate_bar_chart_stat(stat_dict, head, filename, legend):
    """Generate Bar chart for stat on concurrent subscription

    :param dict stat_dict: The dictionary containing min/median/max/std
    :param str head: Titile of charts
    :param str filename: The name of output svg chart
    :param str legend: The legend of generated bar charts

    """
    bar_chart = pygal.Bar()
    bar_chart.title = head
    bar_chart.x_labels = ('min', 'median', 'max', 'std')
    bar_chart.x_title = 'Statistics'
    bar_chart.y_title = 'Time (s)'
    for key in range(len(stat_dict)):
        bar_chart.add('{0}-{1}'.format(legend, key), stat_dict.get(key))
    bar_chart.render_to_file(filename)


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
        key = 'thread-{0}'.format(thread)
        time_list = time_result_dict.get(key)
        stackedline_chart.add('client-{0}'.format(thread), time_list)
    stackedline_chart.render_to_file(filename)


def generate_line_chart_raw(time_result_dict, head, filename, line_chart):
    """Common function for line charts used by Candlepin and Pulp tests

    Both Candlepin and Pulp test would generate line-chart for raw timing
    values. However, Candlepin test set range of y-axis on purpose, so that
    users can compare the growing trend across 2, 4, ..., N test-cases of
    concurrent subscription/deletion. On the other hand, the concurrent
    sync of Pulp test produces only one raw data file/chart, so it only
    declares ``pygal.Line()`` without specifying range.

    Therefore, the difference lies in Line object parameters, while the
    remaining parts like labels, titles, and rendering are both common
    code.

    :param dict stat_dict: The dictionary containing min/median/max/std
    :param str head: Titile of charts
    :param str filename: The name of output svg chart
    :param obj line_chart: Line chart object from either Pulp or Candlepin

    """
    max_label = len(time_result_dict.get('thread-0'))
    line_chart.x_labels = [str(i) for i in range(1, max_label + 1)]
    line_chart.title = head
    line_chart.x_title = 'Iterations'
    line_chart.y_title = 'Time (s)'
    # for each client, add time list into chart
    for thread in range(len(time_result_dict)):
        key = 'thread-{0}'.format(thread)
        time_list = time_result_dict.get(key)
        line_chart.add('client-{0}'.format(thread), time_list)
    line_chart.render_to_file(filename)


def generate_line_chart_raw_pulp(time_result_dict, head, filename):
    """Generate Normal Line chart for raw data of sync/resync"""
    line_chart = pygal.Line()
    generate_line_chart_raw(time_result_dict, head, filename, line_chart)


def generate_line_chart_raw_candlepin(time_result_dict, head, filename):
    """Generate Normal Line chart for raw data of ak/att/del/reg"""
    line_chart = pygal.Line(show_dots=False, range=(0, 50))
    generate_line_chart_raw(time_result_dict, head, filename, line_chart)


def generate_line_chart_stat(stat_dict, filename, line_chart):
    """Common funtion for Line charts used by Candlepin and Pulp tests

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
    :param obj line_chart: Line chart object from either Pulp or Candlepin

    """
    # parameters for formats on charts
    legend = ('min', 'median', 'max', 'std')
    for i in range(len(legend)):
        line_chart.add(legend[i], [vlist[i] for vlist in stat_dict.values()])
    line_chart.render_to_file(filename)


def generate_line_chart_stat_bucketized_candlepin(
        stat_dict,
        head,
        filename,
        bucket_size,
        num_buckets):
    """Generate Normal Line chart for stat data of ak/att/del/reg by buckets

    :param dict stat_dict: The dictionary containing min/median/max/std
    :param str head: Title of charts
    :param str filename: The name of output svg chart
    :param int bucket_size: The number of timing values grouped by a bucket
    :param int num_buckets: The number of buckets to slice a client

    """
    if bucket_size == 0:
        return

    buckets = [
        '{0}-{1}'.format(bucket_size * i + 1, bucket_size * (i + 1))
        for i in range(num_buckets)
    ]
    line_chart = pygal.Line()
    line_chart.title = head
    line_chart.x_labels = buckets
    line_chart.x_title = 'Buckets'
    line_chart.y_title = 'Time (s)'
    generate_line_chart_stat(stat_dict, filename, line_chart)


def generate_line_chart_stat_pulp(stat_dict, head, filename, max_num_tests):
    """
    Generate Normal Line chart for stat data of Pulp sync/resync test

    :param dict stat_dict: The dictionary containing min/median/max/std
    :param str head: Title of charts
    :param str filename: The name of output svg chart
    :param int max_num_buckets: The number of repositories to be synced;
        this parameter is decided by # of target repos

    """
    line_chart = pygal.Line()
    line_chart.title = head
    line_chart.x_labels = [
        '{0}'.format(x) for x in range(2, max_num_tests + 1)
    ]
    line_chart.x_title = '# of Repos Synced'
    line_chart.y_title = 'Time (s)'
    generate_line_chart_stat(stat_dict, filename, line_chart)
