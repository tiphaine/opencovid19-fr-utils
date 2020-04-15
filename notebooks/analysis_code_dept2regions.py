import matplotlib.pyplot as plt
import pandas as pd

from collections import defaultdict

plt.rcParams["figure.figsize"] = (8, 6)

regions = {
    'ara': ['01', '03', '07', '15', '26', '38', '42', '43', '63', '69', '69', '73', '74', ],
    'bfc': ['21','25','39','58','70','71','89','90',],
    'bretagne': ['22','29','35','56',],
    'cvl': ['18','28','36','37','41','45',],
    'corse': ['2A', '2B'],
    'hdf': ['02','59','60','62','80',],
    'grand-est': ['08','10','51','52','54','55','57','67','68','88'],
    'ile-de-france': ['75', '77', '78', '91', '92', '93', '94', '95'],
    'normandie': ['14','27','50','61','76',],
    'na': ['16','17','19','23','24','33','40','47','64','79','86','87',],
    'occitanie': ['09','11','12','30','31','32','34','46','48','65','66','81','82',],
    'pdl': ['44','49','53','72','85',],
    'paca': ['04','05','06','13','83','84',]
}

data_url = 'https://raw.githubusercontent.com/opencovid19-fr/data/master/dist/chiffres-cles.csv'

def get_previous_date(date):
    year, month, day = str(date).split('-')
    if int(day) == 1:
        return '-'.join([year, '{:02d}'.format(int(month)-1), '31'])
    else:
        return '-'.join([year, month, '{:02d}'.format(int(day)-1)])

def get_data_dept(spf_data, dept):
    try:
        dept_data = spf_data[spf_data.maille_code == 'DEP-{:2d}'.format(dept)]
    except ValueError:
        dept_data = spf_data[spf_data.maille_code == 'DEP-{:2s}'.format(dept)]
    dept_data = dept_data.sort_values(by='date', ascending=True)
    cumul = defaultdict(lambda: defaultdict(int))
    for key in (
        'cas_confirmes',
        'deces',
        'deces_ehpad',
        'reanimation',
        'hospitalises',
        'gueris',
        'depistes',
    ):
        for index, row in dept_data.iterrows():
            date = row['date']
            value = row.get(key, 0)
            #cumul[key][date] = value + cumul[key].get(get_previous_date(date), 0)
            cumul[key][date] = value

    diff = defaultdict(lambda: defaultdict(int))
    for key in (
        'cas_confirmes',
        'deces',
        'deces_ehpad',
        'reanimation',
        'hospitalises',
        'gueris',
        'depistes',
    ):
        for index, row in dept_data.iterrows():
            date = row['date']
            diff[key][date] = cumul[key][date] - cumul[key].get(get_previous_date(date), 0)

    for key in (
        'cas_confirmes',
        'deces',
        'deces_ehpad',
        'reanimation',
        'hospitalises',
        'gueris',
        'depistes',
    ):
        cumul_df = pd.DataFrame.from_dict(dict(cumul[key]), orient='index', columns=[key])
        cumul[key] = cumul_df
        diff_df = pd.DataFrame.from_dict(dict(diff[key]), orient='index', columns=[key])
        diff[key] = diff_df

    return {
        'cumul': dict(cumul),
        'diff': dict(diff),
    }


def _gen_ts_dept(spf_data):
    dept_analyses = {}
    for maille_code in spf_data.maille_code.unique():
        dept_nb = maille_code.split('-')[1]
        dept_data = get_data_dept(spf_data, dept_nb)
        dept_analyses[dept_nb] = dept_data
    return dept_analyses

def gen_region_ts(spf_data, keys=None):
    if keys is None:
        keys = [
            'cas_confirmes',
            'deces',
            'deces_ehpad',
            'reanimation',
            'hospitalises',
            'gueris',
            'depistes',
        ]
    dept_analyses = _gen_ts_dept(spf_data)

    region_data = defaultdict(lambda: defaultdict(dict))
    for region, depts in regions.items():
        for key in keys:
            region_data_cumul_list = []
            region_data_diff_list = []
            for dept in depts:
                dept_key_cumul_df = dept_analyses[dept]['cumul'][key]
                region_data_cumul_list.append(dept_key_cumul_df)
                dept_key_diff_df = dept_analyses[dept]['diff'][key]
                region_data_diff_list.append(dept_key_diff_df)
            region_key_cumul_df = pd.DataFrame(pd.concat(region_data_cumul_list, axis=1).sum(axis=1))
            region_key_cumul_df.columns = [key]
            region_key_diff_df = pd.DataFrame(pd.concat(region_data_diff_list, axis=1).sum(axis=1))
            region_key_diff_df.columns = [key]
            region_data[region]['cumul'][key] = region_key_cumul_df
            region_data[region]['diff'][key] = region_key_diff_df
    return region_data



def get_data_france(spf_data, keys=None):
    if keys is None:
        keys = [
            'cas_confirmes',
            'deces',
            'deces_ehpad',
            'reanimation',
            'hospitalises',
            'gueris',
            'depistes',
        ]
    france_data = spf_data.groupby('date').agg('sum').reset_index()
    france_data = france_data.sort_values(by='date', ascending=True)
    cumul = defaultdict(lambda: defaultdict(int))
    for key in keys:
        for index, row in france_data.iterrows():
            date = row['date']
            value = row.get(key, 0)
            cumul[key][date] = value
    diff = defaultdict(lambda: defaultdict(int))
    for key in keys:
        for index, row in france_data.iterrows():
            date = row['date']
            diff[key][date] = cumul[key][date] - cumul[key].get(get_previous_date(date), 0)
    for key in keys:
        cumul_df = pd.DataFrame.from_dict(dict(cumul[key]), orient='index', columns=[key])
        cumul[key] = cumul_df
        diff_df = pd.DataFrame.from_dict(dict(diff[key]), orient='index', columns=[key])
        diff[key] = diff_df

    return {
        'cumul': dict(cumul),
        'diff': dict(diff),
    }

def get_plot_cumul_france_separate(france_data, keys=None):
    if keys is None:
        keys = [
            'cas_confirmes',
            'deces',
            'deces_ehpad',
            'reanimation',
            'hospitalises',
            'gueris',
            'depistes',
        ]
    pd.concat([france_data['cumul'][key] for key in keys], axis=1).plot.line(
    y=keys, subplots=True, layout=(4,2), title='France / Cumul')


def get_plot_diff_france_separate(france_data, keys=None):
    if keys is None:
        keys = [
            'cas_confirmes',
            'deces',
            'deces_ehpad',
            'reanimation',
            'hospitalises',
            'gueris',
            'depistes',
        ]
    pd.concat([france_data['diff'][key] for key in keys], axis=1).plot.line(
    y=keys, subplots=True, layout=(4,2), title='France / Diff')

def get_plot_cumul_france_merged(france_data, keys=None):
    if keys is None:
        keys = [
            'cas_confirmes',
            'deces',
            'deces_ehpad',
            'reanimation',
            'hospitalises',
            'gueris',
            'depistes',
        ]
    pd.concat([france_data['cumul'][key] for key in keys], axis=1).plot.line(
    y=keys, title='France / Cumul')

def get_plot_diff_france_merged(france_data, keys=None):
    if keys is None:
        keys = [
            'cas_confirmes',
            'deces',
            'deces_ehpad',
            'reanimation',
            'hospitalises',
            'gueris',
            'depistes',
        ]
    pd.concat([france_data['diff'][key] for key in keys], axis=1).plot.line(
    y=keys, title='France / Diff')

def get_plot_cumul_region_separate(region, region_data, keys=None):
    if keys is None:
        keys = [
            'cas_confirmes',
            'deces',
            'deces_ehpad',
            'reanimation',
            'hospitalises',
            'gueris',
            'depistes',
        ]
    print('{} / CUMUL'.format(region.upper()))
    pd.concat([region_data[region]['cumul'][key] for key in keys], axis=1).plot.line(
    y=keys, subplots=True, layout=(4,2))


def get_plot_diff_region_separate(region, region_data, keys=None):
    if keys is None:
        keys = [
            'cas_confirmes',
            'deces',
            'deces_ehpad',
            'reanimation',
            'hospitalises',
            'gueris',
            'depistes',
        ]
    print('{} / DIFF'.format(region.upper()))
    pd.concat([region_data[region]['diff'][key] for key in keys], axis=1).plot.line(
    y=keys, subplots=True, layout=(4,2))

def get_plot_cumul_region_merged(region, region_data, keys=None):
    if keys is None:
        keys = [
            'cas_confirmes',
            'deces',
            'deces_ehpad',
            'reanimation',
            'hospitalises',
            'gueris',
            'depistes',
        ]
    print('{} / CUMUL'.format(region.upper()))
    pd.concat([region_data[region]['cumul'][key] for key in keys], axis=1).plot.line(
    y=keys, )

def get_plot_diff_region_merged(region, region_data, keys=None):
    if keys is None:
        keys = [
            'cas_confirmes',
            'deces',
            'deces_ehpad',
            'reanimation',
            'hospitalises',
            'gueris',
            'depistes',
        ]
    print('{} / DIFF'.format(region.upper()))
    pd.concat([region_data[region]['diff'][key] for key in keys], axis=1).plot.line(
    y=keys, )


def get_plot_cumul_multiregions(region_data, keys=None):
    if keys is None:
        keys = [
            'cas_confirmes',
            'deces',
            'deces_ehpad',
            'reanimation',
            'hospitalises',
            'gueris',
            'depistes',
        ]
    for region, cur_region_data in region_data.items():
        pd.concat([cur_region_data['cumul'][key] for key in keys], axis=1).plot.line(
        y=keys, title='{} / Cumul'.format(region.upper()))

def get_plot_diff_multiregions(region_data, keys=None):
    if keys is None:
        keys = [
            'cas_confirmes',
            'deces',
            'deces_ehpad',
            'reanimation',
            'hospitalises',
            'gueris',
            'depistes',
        ]
    for region, cur_region_data in region_data.items():
        pd.concat([cur_region_data['diff'][key] for key in keys], axis=1).plot.line(
        y=keys, title='{} / Cumul'.format(region.upper()))
