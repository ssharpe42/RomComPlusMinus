import seaborn as sns
import os
import numpy as np
import pandas as pd
import pickle
import random
from sklearn import linear_model
from pandas import DataFrame

os.chdir('/Users/Sam/Desktop/Projects/RomComPlusMinus/')
#load extract function
from extract import extract_movie_data

#Load movie dict data
with open('data/movie_info.pickle','r') as f:
   movie_dict = pickle.load(f)

#extract movie data for top 10 actors in credits
actors, raw_data, non_actor_data, X, y, lsi,corpus_tfidf = extract_movie_data(movie_dict, n_actors = 10, actor_min = 1)

#Create different data frames for male, female, and overall plus minus
Male_X = X.iloc[:,~X.columns.isin(['votes','female_votes'])]
Female_X = X.iloc[:,~X.columns.isin(['votes','male_votes'])]
Final_X = X.iloc[:,~X.columns.isin(['female_votes','male_votes'])]

#Set up rige regression models
Lin = linear_model.RidgeCV( alphas=np.logspace(-3, 3, 300),  cv = 4)
FemaleLin = linear_model.RidgeCV( alphas=np.logspace(-3, 3, 300),  cv = 4)
MaleLin = linear_model.RidgeCV( alphas=np.logspace(-3, 3, 300),  cv = 4)

#Fit ridge regression models
Lin.fit(Final_X, y['imdbscore'])
FemaleLin.fit(Female_X, y['female_score'])
MaleLin.fit(Male_X, y['male_score'])

#Index actor positions
actors = np.array(actors)
Appearances = X[X.columns.intersection(actors)].sum()
indx = np.where(X[X.columns.intersection(actors)].sum()>=4)[0]

# sorted([(MaleLin.coef_[i],Male_X.columns[i]) for i in range(0, len(Male_X.columns)) if Male_X.columns[i] in Appearances.index[indx]], key = lambda x: x[0])
# sorted([(MaleLin.coef_[i],Male_X.columns[i]) for i in range(0, len(Male_X.columns))], key = lambda x: x[0])[-20:]
# sorted([(FemaleLin.coef_[i],Female_X.columns[i]) for i in range(0, len(Female_X.columns))if Female_X.columns[i] in Appearances.index[indx]], key = lambda x: x[0])
# sorted([(Lin.coef_[i],Final_X.columns[i]) for i in range(0, len(Final_X.columns)) if Final_X.columns[i] in Appearances.index[indx]], key = lambda x: x[0])

MaleCoef = DataFrame({'Variable':Male_X.columns, 'Coef':MaleLin.coef_,
					'ActorIndicator': [1 if m in actors else 0 for m in Male_X.columns ],
					'ActorAppear': [Appearances[m] if m in Appearances.index else 0 for m in Male_X.columns ]})
FemaleCoef = DataFrame({'Variable':Female_X.columns, 'Coef':FemaleLin.coef_,
					'ActorIndicator': [1 if f in actors else 0 for f in Female_X.columns ],
					'ActorAppear': [Appearances[f] if f in Appearances.index else 0 for f in Female_X.columns ]})
AllCoef = DataFrame({'Variable':Final_X.columns, 'Coef':Lin.coef_,
					'ActorIndicator': [1 if v in actors else 0 for v in Final_X.columns ],
					'ActorAppear': [Appearances[v] if v in Appearances.index else 0 for v in Final_X.columns ]})

#Aggregate topic vectors
TopicVec0 = DataFrame({'word0':[tup[0] for tup in lsi.show_topic(0,50)],'value0':[tup[1] for tup in lsi.show_topic(0,50)]})
TopicVec1 = DataFrame({'word1':[tup[0] for tup in lsi.show_topic(1,50)],'value1':[tup[1] for tup in lsi.show_topic(1,50)]})
TopicVec = TopicVec0.merge(TopicVec1, how = 'inner', left_on='word0',right_on='word1')

#Write data to csvs for visualization in R
MaleCoef.to_csv('data/male_results.csv',header=True, index=False, encoding='utf-8')
FemaleCoef.to_csv('data/female_results.csv',header=True, index=False, encoding='utf-8')
AllCoef.to_csv('data/all_results.csv',header=True, index=False, encoding='utf-8')
raw_data.to_csv('data/raw_data.csv',header=True, index=False, encoding='utf-8')
non_actor_data.to_csv('data/non_actor_data.csv',header=True, index=False, encoding='utf-8')
TopicVec.to_csv('data/topic_vec.csv',header=True, index=False, encoding='utf-8')
