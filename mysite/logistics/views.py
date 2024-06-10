from django.http import HttpResponse
from django.shortcuts import render
from django.views import generic
import pandas as pd
from pandas.tseries.offsets import BDay
import numpy as np
from pandas.tseries.holiday import USFederalHolidayCalendar as Calendar


# some data cleaning according to the provided ipynb
data = pd.read_csv('logistics/ByteDance_Foxconn_2024_modified_TECH.csv')
data.dropna(subset=['START DATE', 'END DATE'], inplace=True)
data.drop_duplicates(subset=['BD Ticket #'], inplace=True)
data['START DATE'] = pd.to_datetime(data['START DATE'])
data['END DATE'] = pd.to_datetime(data['END DATE'])

calendar = Calendar()
holidays = calendar.holidays(start=data['START DATE'].min(), end=data['END DATE'].max())
holidays = holidays.to_numpy(dtype='datetime64[D]') 

data['Business Days'] = np.busday_count(data['START DATE'].values.astype('datetime64[D]'), 
                                    data['END DATE'].values.astype('datetime64[D]'),
                                    holidays=holidays)
data['TECH'] = data['TECH'].str.title()
data['Individual TECH'] = data['TECH'].apply(lambda x: x.split('/'))
tech_list=[None] + sorted(list(set([tech for sublist in data['Individual TECH'] for tech in sublist])))

def index(request):  
    form_posted = False
    threshold_reached = False
    on_time_rate = 0
    start_date = None
    end_date = None
    tech = None
    mode = None
    threshold = None

    if request.method == 'POST':
        start_date = request.POST.get('date-start')
        end_date = request.POST.get('date-end')
        tech = request.POST.get('tech')
        mode = request.POST.get('mode')
        threshold = request.POST.get('threshold')
        threshold_days = 5 if threshold == "5天95%" else 7
        threshold_percentage = 95 if threshold == "5天95%" else 97
        
        tech_data = data.copy()  
        if tech != "None":
            if mode == 'Cooperative':
                tech_data = data[data['TECH'].apply(lambda x: tech in x.split('/') and '/' in x)]
            elif mode == 'Independent':
                tech_data = data[data['TECH'].apply(lambda x: tech in x.split('/') and '/' not in x)]

        # 如果未选择日期，则选择全部时间范围
        if start_date and end_date:
            range_data = tech_data[(tech_data['END DATE'] >= pd.to_datetime(start_date)) & 
                                    (tech_data['END DATE'] <= pd.to_datetime(end_date))]
        else:
            range_data = tech_data  # 全时间数据，如果未指定日期

        condition_count = (range_data['Business Days'] <= threshold_days).sum()
        total_count = range_data.shape[0]
        on_time_rate = (condition_count / total_count) * 100 if total_count > 0 else 0
        threshold_reached = True if on_time_rate >= threshold_percentage else False
        form_posted = True

    context = {
        'tech_list': tech_list,
        'form_posted': form_posted,
        "threshold_reached": threshold_reached,
        "on_time_rate": on_time_rate,
        "start_date": start_date,
        "end_date": end_date,
        "mode": mode,
        "tech": tech,
        "threshold": threshold,
    }

    # Render the HTML template index.html with the data in the context variable
    return render(request, 'index.html', context=context)