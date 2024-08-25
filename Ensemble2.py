#!/usr/bin/env python
# coding: utf-8

# In[9]:


from numpy import mean, std
import pandas as pd
from sklearn.model_selection import train_test_split, RepeatedStratifiedKFold, cross_val_score, GridSearchCV
from sklearn.ensemble import StackingClassifier
from sklearn.svm import SVC
from sklearn.neighbors import KNeighborsClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
import matplotlib.pyplot as plt
import joblib

# Load the dataset
data = pd.read_csv("C:/Users/Administrator/Documents/mail_classification_env/Files/dataset_HP_Sel.csv")

# Split data into features and target variable
X = data.drop(columns=['label'])
y = data['label']
print(X.head())
# Split data into train and test sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

def get_stacking():
# Define base models

 level0 = list()
 level0.append(('knn', KNeighborsClassifier()))
 level0.append(('ann', MLPClassifier()))
 level0.append(('c50', DecisionTreeClassifier()))
 
 # Define meta-model
 level1 = SVC()
 # Define ensemble model using stacking
 model = StackingClassifier(estimators=level0, final_estimator=level1, cv=5)
 return model
 
# get a list of models to evaluate
def get_models():
 models = dict()
 models['knn'] = KNeighborsClassifier()
 models['ann'] = MLPClassifier()
 models['c50'] = DecisionTreeClassifier()
 models['stacking'] = get_stacking()
 return models

parameters = {"degree" : [3], "C": [10], "gamma": [0.01]}
# evaluate a give model using cross-validation
def evaluate_model(model, X, y):
 cv = RepeatedStratifiedKFold(n_splits=10, n_repeats=3, random_state=42)
 scores = cross_val_score(model, X, y, scoring='accuracy', cv=5, n_jobs=-1, error_score='raise')
 return scores

precision_score
# get the models to evaluate
models = get_models()
# evaluate the models and store results
results, names = list(), list()
for name, model in models.items():
 scores = evaluate_model(model, X, y)
 results.append(scores)
 names.append(name)
 print('>%s %.3f (%.3f)' % (name, mean(scores), std(scores)))

# Train the stacking model on the entire training dataset
stacking_model = get_stacking()
stacking_model.fit(X_train, y_train)

# Save the trained stacking model
joblib.dump(stacking_model, 'stacking_model.pkl')

# In[ ]:




