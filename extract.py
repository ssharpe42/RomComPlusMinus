""" Extracts scraped data prduced in 'scrapemovies.py' to prepare for RAPM models """

import os
import numpy as np
import pandas as pd
import pickle
from pandas import DataFrame
from sklearn.feature_extraction.text import CountVectorizer,TfidfTransformer
import nltk
import spacy
from gensim import corpora, models, similarities

#Tokenize plots from imdb
def tokenize_plot(text, nlp_mod):

	doc = nlp_mod(text)

	tokens = [d.lemma_ for d in doc if d.pos_ not in ['PUNCT', 'PROPN'] and not d.is_stop and not d.lemma_ in ["'s","be"]]

	pos_map = dict([(d.lemma_, d.pos_) for d in doc])

	bigrams =[' '.join(bigram) for bigram in nltk.ngrams(tokens, 2) if pos_map[bigram[0]]in ['ADJ','VERB'] and pos_map[bigram[1]]=='NOUN']

	return tokens

#Latent semantic indexing on plots
def get_topics(plots):

	dictionary = corpora.Dictionary(plots)
	corpus = [dictionary.doc2bow(text) for text in plots]
	tfidf = models.TfidfModel(corpus, normalize = True)
	corpus_tfidf = tfidf[corpus]
	np.random.seed(123)
	lsi = models.LsiModel(corpus_tfidf, id2word=dictionary, num_topics=3)

	return lsi, corpus_tfidf, dictionary

#Extract all movie data
#n_actors - include top n actors from closing credits
#actor_min - include actors appearing in at least n romcoms
#log_votes - log transform imdb votes
def extract_movie_data(movie_dict, n_actors = 20,  actor_min = 1, log_votes = True):

	data_list = []
	actors= []
	plots = []
	nlp = spacy.load('en')

	#Get list of all actors
	for movie in movie_dict:
		current = movie_dict[movie]

		if n_actors == 'All':
			actors.extend(current['cast'])
		else:
			actors.extend(current['cast'][0:n_actors])

	actors = list(set(actors))

	for movie in movie_dict:

		print movie

		current = movie_dict[movie]
		if n_actors == 'All':
			current_actors = current['cast']
		else:
			current_actors = current['cast'][0:n_actors]

		df = DataFrame({key: 0 if key not in current_actors else 1 for key in actors}, index = [1])

		df = df.assign(movie = movie,
					   imdbscore = current['score'],
					   votes = current['votes'],
					   male_score = current['male_score'],
					   female_score = current['female_score'],
					   male_votes = current['male_votes'],
					   female_votes = current['female_votes'],
					   content_rating = current['content_rating'],
					   genre = current['genre'],
					   time = current['time'],
					   year = current['year'],
					   budget = current['budget'],
					   director = current['director'],
					   writer = current['writers'][0],
					   productionco = current['production co'])
		data_list.append(df)


		#Tokenize and clean plot text
		plot_tokens = tokenize_plot(current['plot'],nlp)
		plots.append(plot_tokens)


	#concatenate dataframes
	raw_data = pd.concat(data_list)

	#remove sparse actors
	raw_data = pd.concat([raw_data[raw_data.columns.intersection(actors)].loc[:,raw_data[raw_data.columns.intersection(actors)].sum()>=actor_min], raw_data[raw_data.columns.difference(actors)]], axis=1)

	#replace missing budget numbers
	raw_data['budget'] = pd.to_numeric(raw_data['budget'], errors = 'coerce')

	#avg budget per production company - fill missing values
	avg_budget = raw_data[['productionco','budget']].groupby('productionco').mean().reset_index()
	avg_budget.loc[np.isnan(avg_budget.budget),'budget'] = raw_data.budget.mean()
	avg_budget.columns = ['productionco','fill_budget']

	#merge avg budget by production company
	raw_data = raw_data.merge(avg_budget, 'left', 'productionco')
	raw_data['budget'] = raw_data.apply(lambda row: row['fill_budget'] if np.isnan(row['budget']) else row['budget'], axis = 1)
	del raw_data['fill_budget']

	if log_votes:
		raw_data[['votes','female_votes','male_votes']] = np.log(raw_data[['votes','female_votes','male_votes']])


	#Compute topics
	lsi, corpus_tfidf, dictionary = get_topics(plots)

	#Compute topic probabilities
	topic_dict= {t:[] for t in range(0, lsi.num_topics)}
	for i,movie in enumerate(movie_dict):
		topics  = lsi[corpus_tfidf[i]]
		for t,p in topics:
			topic_dict[t].append(p)

	#Label topics
	topic_df = DataFrame(topic_dict)
	topic_df.columns = ['Topic' + str(t) for t in topic_dict.keys()]

	#Add topics to raw data
	raw_data = pd.concat([raw_data, topic_df], axis =1)

	#Data other than actors
	non_actor_data = raw_data[raw_data.columns.difference(actors)]

	#Predictor data
	X = pd.get_dummies(raw_data[raw_data.columns.difference(['movie','imdbscore','male_score','female_score'])], drop_first = True)
	#target data
	y = raw_data[['movie','imdbscore','male_score','female_score']]

	return actors, raw_data, non_actor_data, X, y, lsi, corpus_tfidf

