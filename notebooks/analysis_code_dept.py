import matplotlib.pyplot as plt
import pandas as pd

from collections import defaultdict

plt.rcParams["figure.figsize"] = (8, 6)

keys = [
    #'cas_confirmes',
    'deces',
    #'deces_ehpad',
    'reanimation',
    'hospitalises',
    'gueris',
    #'depistes',
]

default_keys = [
    'cas_confirmes',
    'deces',
    'deces_ehpad',
    'reanimation',
    'hospitalises',
    'gueris',
    'depistes',
]

regions = {
    'Auvergne-Rhone-Alpes': 'REG-84',
    'Bourgogne-Franche-Comte': 'REG-27',
    'Bretagne': 'REG-53',
    'Centre-Val de Loire': 'REG-24',
    'Corse': 'REG-94',
    'Grand Est': 'REG-44',
    'Hauts-de-France': 'REG-32',
    'Normandie': 'REG-28',
    'Nouvelle-Aquitaine': 'REG-75',
    'Occitanie': 'REG-76',
    'Pays de la Loire': 'REG-52',
    "Provence-Alpes-Cote d'Azur": 'REG-93',
    'Ile-de-France': 'REG-11',
    'Guadeloupe': 'REG-01',
    'Guyane': 'REG-03',
    'La Reunion': 'REG-04',
    'Martinique': 'REG-02',
    'Mayotte': 'REG-06',
}

data_url = 'https://raw.githubusercontent.com/opencovid19-fr/data/master/dist/chiffres-cles.csv'


def get_previous_date(date):
    year, month, day = str(date).split('-')
    if int(day) == 1:
        return '-'.join([year, '{:02d}'.format(int(month)-1), '31'])
    else:
        return '-'.join([year, month, '{:02d}'.format(int(day)-1)])


def get_data_dept(spf_data, dept):
    dept_data = spf_data[spf_data.maille_code == dept]
    dept_data = dept_data.sort_values(by='date', ascending=True)
    cumul = defaultdict(lambda: defaultdict(int))
    for key in default_keys:
        for index, row in dept_data.iterrows():
            date = row['date']
            value = row.get(key, 0)
            cumul[key][date] = value

    diff = defaultdict(lambda: defaultdict(int))
    for key in default_keys:
        for index, row in dept_data.iterrows():
            date = row['date']
            diff[key][date] = cumul[key][date] - cumul[key].get(get_previous_date(date), 0)

    for key in default_keys:
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
        dept_data = get_data_dept(spf_data, maille_code)
        dept_analyses[maille_code] = dept_data
    return dept_analyses


def gen_region_ts(spf_data, keys=None):
    if keys is None:
        keys = default_keys
    dept_analyses = _gen_ts_dept(spf_data)

    region_data = defaultdict(lambda: defaultdict(dict))
    for region, region_code in regions.items():
        for key in keys:
            region_key_cumul_df = pd.DataFrame(dept_analyses[region_code]['cumul'][key])
            region_key_cumul_df.columns = [key]
            region_key_diff_df = pd.DataFrame(dept_analyses[region_code]['diff'][key])
            region_key_diff_df.columns = [key]
            region_data[region]['cumul'][key] = region_key_cumul_df
            region_data[region]['diff'][key] = region_key_diff_df
    return region_data


def get_data_france(spf_data, keys=None):
    if keys is None:
        keys = default_keys

    france_data = spf_data[spf_data.granularite == "pays"].groupby('date').agg('sum').reset_index()
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
        keys = default_keys
    pd.concat([france_data['cumul'][key] for key in keys], axis=1).plot.line(
    y=keys, subplots=True, layout=(4,2), title='France / Cumul')


def get_plot_diff_france_separate(france_data, keys=None):
    if keys is None:
        keys = default_keys
    pd.concat([france_data['diff'][key] for key in keys], axis=1).plot.line(
    y=keys, subplots=True, layout=(4,2), title='France / Diff')


def get_plot_cumul_france_merged(france_data, keys=None):
    if keys is None:
        keys = default_keys
    pd.concat([france_data['cumul'][key] for key in keys], axis=1).plot.line(
    y=keys, title='France / Cumul')


def get_plot_diff_france_merged(france_data, keys=None):
    if keys is None:
        keys = default_keys
    pd.concat([france_data['diff'][key] for key in keys], axis=1).plot.line(
    y=keys, title='France / Diff')


def get_plot_cumul_region_separate(region, region_data, keys=None):
    if keys is None:
        keys = default_keys
    print('{} / CUMUL'.format(region.upper()))
    pd.concat([region_data[region]['cumul'][key] for key in keys], axis=1).plot.line(
    y=keys, subplots=True, layout=(4,2))


def get_plot_diff_region_separate(region, region_data, keys=None):
    if keys is None:
        keys = default_keys
    print('{} / DIFF'.format(region.upper()))
    pd.concat([region_data[region]['diff'][key] for key in keys], axis=1).plot.line(
    y=keys, subplots=True, layout=(4,2))


def get_plot_cumul_region_merged(region, region_data, keys=None):
    if keys is None:
        keys = default_keys
    print('{} / CUMUL'.format(region.upper()))
    pd.concat([region_data[region]['cumul'][key] for key in keys], axis=1).plot.line(
    y=keys, )


def get_plot_diff_region_merged(region, region_data, keys=None):
    if keys is None:
        keys = default_keys
    print('{} / DIFF'.format(region.upper()))
    pd.concat([region_data[region]['diff'][key] for key in keys], axis=1).plot.line(
    y=keys, )


def get_plot_cumul_multiregions(region_data, keys=None):
    if keys is None:
        keys = default_keys
    for region, cur_region_data in region_data.items():
        pd.concat([cur_region_data['cumul'][key] for key in keys], axis=1).plot.line(
            y=keys, title='{} / Cumul'.format(region.upper()))


def get_plot_diff_multiregions(region_data, keys=None):
    if keys is None:
        keys = default_keys
    for region, cur_region_data in region_data.items():
        pd.concat([cur_region_data['diff'][key] for key in keys], axis=1).plot.line(
        y=keys, title='{} / Cumul'.format(region.upper()))
