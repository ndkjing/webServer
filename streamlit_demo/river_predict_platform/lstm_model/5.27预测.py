import os
os.environ["CUDA_VISIBLE_DEVICES"] = "1"

import pandas as pd
import numpy as np
import psycopg2

# In[46]:


zb_list=['nh3n_avg','tp_avg','do_avg','codmn_avg']
begin_time = '2019-08-01 00:00:00'
end_time= '2020-05-25 20:00:00'
#data = pd.read_excel('4.26气象数据合并rainfall_pre.xlsx',sheet_name='鲁岗涌')
# data = data[['data_time','mn','总磷','氨氮','水温','溶解氧','高锰酸盐指数']]
# data[['总磷','氨氮','水温','溶解氧','高锰酸盐指数']] = data[['总磷','氨氮','水温','溶解氧','高锰酸盐指数']].astype(float)
# data['mn'] = data['mn'].astype(str)
# data['mn']=data['mn'].map(lambda x:'0'+str(x) if len(str(x))==13 else x)
def query(conn, sql):
    connect = conn
    cur = connect.cursor()
    cur.execute(sql)
    index = cur.description
    result = []
    for res in cur.fetchall():
        row = {}
        for i in range(len(index)):
            row[index[i][0]] = res[i]
        result.append(row)
        connect.close()
    return result

conn = psycopg2.connect(database="create_dw",
                        user="ds_usr",
                        password="QNWZWIPN6**F", 
                        host="47.106.73.123",
                        port='5432')
SQL = "SELECT data_time,site_name,nh3n_avg,tp_avg,do_avg,codcr_avg,codmn_avg,rainfall FROM ds_wdp.wdp_rpt_site_mon_data_list where site_name in ('鲁岗涌','芦苞涌古云桥断面','芦苞涌入西南涌断面','科勒大道断面','凤岗断面','广三高速断面') and data_time between '"+begin_time+"' and '"+end_time + "'"
rows = query(conn = conn,sql = SQL)
data= pd.DataFrame(rows)
data[['nh3n_avg','tp_avg','do_avg','codcr_avg','codmn_avg','rainfall']]=data[['nh3n_avg','tp_avg','do_avg','codcr_avg','codmn_avg','rainfall']].astype(float)
data['data_time'] = pd.to_datetime(data['data_time'])
data = data.sort_values(by='data_time')

data['next_rain'] = data['rainfall'][1:].tolist()+[0.0]
data.head()


# In[47]:


def pre_site(data,rain_now):
    pre_data={}
    for zb in zb_list:
        model2 = load_model('lstm_model/lstm_%s_%s.h5'%('鲁岗涌',zb))
        scale_model = joblib.load('lstm_model/scaler_%s_%s'%('鲁岗涌',zb))
        site_data = data[data['site_name']=='鲁岗涌']
        site_data = site_data.set_index('data_time').resample('4H').asfreq().fillna(method='ffill').fillna(method='bfill').reset_index()
        test_data = site_data[site_data['data_time'] >='2020-05-22 00:00:00'][['nh3n_avg','next_rain']]
        test_data = np.array(test_data)
        an_test_data = test_data[:,0].reshape(-1,1)
        rain_test_data = test_data[:,1:].reshape(-1,1)
        rain_test_data[-1]=rain_now
        an_test = scale_model.transform(an_test_data).reshape(-1,1)
        test_data = np.hstack([an_test,rain_test_data])
        x_test,y_test = create_dataset(test_data,18,6)       
        

        y_test_predict=model2.predict(x_test)
        #y_test = scale_model.inverse_transform(y_test)
        y_test_predict = scale_model.inverse_transform(y_test_predict)
        pre_data[zb]=y_test_predict[-1]
    return pre_data


# In[48]:


pre_site(data,6)


# In[ ]:




