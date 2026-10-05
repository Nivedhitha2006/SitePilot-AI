import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder,StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score,precision_score,recall_score,f1_score,roc_auc_score
NUM=['pages_visited','session_duration','previous_interactions']; CAT=['industry','company_size','form_submitted','pricing_page_visited','solution_page_visited','email_opened']
def train_predict(df):
    if 'converted' not in df: raise ValueError('CSV must contain converted')
    y=pd.to_numeric(df['converted'],errors='coerce').fillna(0).astype(int); X=df.drop(columns=['converted']).copy()
    for c in NUM:X[c]=pd.to_numeric(X[c],errors='coerce') if c in X else 0
    for c in CAT:
        if c not in X:X[c]='unknown'
    cols=NUM+CAT; X=X[cols]
    pre=ColumnTransformer([('num',Pipeline([('imp',SimpleImputer(strategy='median')),('sc',StandardScaler())]),NUM),('cat',Pipeline([('imp',SimpleImputer(strategy='most_frequent')),('oh',OneHotEncoder(handle_unknown='ignore'))]),CAT)])
    model=Pipeline([('pre',pre),('clf',RandomForestClassifier(n_estimators=180,random_state=42,class_weight='balanced'))])
    metrics={}
    if y.nunique()>1 and len(df)>=10:
        xt,xv,yt,yv=train_test_split(X,y,test_size=.25,random_state=42,stratify=y); model.fit(xt,yt); p=model.predict(xv); prob=model.predict_proba(xv)[:,1]; metrics={'accuracy':accuracy_score(yv,p),'precision':precision_score(yv,p,zero_division=0),'recall':recall_score(yv,p,zero_division=0),'f1':f1_score(yv,p,zero_division=0),'roc_auc':roc_auc_score(yv,prob)}
    else:model.fit(X,y)
    prob=model.predict_proba(X)[:,1]
    preds=[]
    for i,v in enumerate(prob): preds.append({'lead_id':str(df.iloc[i].get('lead_id',i+1)),'score':round(float(v*100),1),'probability':round(float(v),4),'intent':'High' if v>=.7 else 'Medium' if v>=.4 else 'Low'})
    return metrics,preds
