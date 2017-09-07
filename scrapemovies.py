import urllib2
import requests
from bs4 import BeautifulSoup
import re
import numpy as np
import pickle
import os


def get_cast(movie_page, url):

	see_more_links = movie_page.find_all('div',{'class':'see-more'})
	see_more_text = np.array(['full cast' in s.text for s in see_more_links])
	cast_link = see_more_links[np.where(see_more_text)[0][0]].find('a').get('href')
	cast_page = BeautifulSoup(urllib2.urlopen(url+ cast_link).read())

	#Get all tables and find director/writers
	#tables = np.array([header.text for header in cast_page.find_all('h4',{'class':'dataHeaderWithBorder'})])
	tables = cast_page.find_all('table',{'class':'simpleTable simpleCreditsTable'})
	writer_table = tables[1]

	writers = [row.find('td',{'class':'name'}).text.strip()  for row in writer_table.find_all('tr') if row.find('td',{'class':'name'})]
	writer_type =[re.findall('\(([^)]+)\)',row.find('td',{'class':'credit'}).text.strip())[0] for row in writer_table.find_all('tr') if row.find('td',{'class':'credit'})]

	cast_table = cast_page.find('table', {'class': 'cast_list'}).find_all('tr')[1:]
	cast = []
	for row in cast_table:
		if row.find('td').text == 'Rest of cast listed alphabetically:':
			break
		actor = row.find('td', {'class':'itemprop'}).find('a').find('span').text
		cast.append(actor)

	return cast, writers, writer_type

def get_plot(movie_page):

	#Scrape plots
	plots = movie_page.find_all('div',{'itemprop':'description'})
	short_plot = plots[0].text.split('Written by')[0].strip()
	plot = plots[1].text.split('Written by')[0].strip()

	return short_plot, plot

def get_director(movie_page):

	return movie_page.find('span',{'itemprop':'director'}).text.strip()


def get_specs(movie_page):

	specs = movie_page.find('div',{'class':'subtext'})

	genre = ' '.join([g.text for g in specs.find_all('span', {'itemprop':'genre'})])

	specs_list =[s.strip() for s in specs.text.split('|')]
	content_rating = specs_list[0]
	time = re.findall('[0-9]+',specs_list[1])
	if len(time)==1:
		time = int(time[0])*60
	else:
		time = int(time[0])*60 + int(time[1])
	year = int(re.findall('[0-9]{4}',specs_list[3])[0])

	return genre, content_rating, time, year

def get_budget_production(movie_page):

	text_blocks = movie_page.find_all('div',{'class','txt-block'})
	header_tags = [t.find('h4',{'class','inline'}) for t in text_blocks ]
	headers = np.array([h.text if h else None for h in header_tags])
	budget_indx = np.where(headers=='Budget:')[0]
	if budget_indx:
		budget_indx=budget_indx[0]
		budget = float(re.search('[0-9,]+', text_blocks[budget_indx].text).group().replace(',',''))
	else:
		budget='N/A'
	production_indx = np.where(headers=='Production Co:')[0][0]
	prod_co = text_blocks[production_indx].text.split(':')[1].split('See more')[0].split(',')[0].strip()

	return budget, prod_co

def get_imdbscore(movie_page):

	score = float(movie_page.find('span',{'itemprop':'ratingValue'}).text)
	votes = int(movie_page.find('div',{'itemprop':'aggregateRating'}).find('span',{'itemprop':'ratingCount'}).text.replace(',',''))

	score_page = BeautifulSoup(urllib2.urlopen('http://www.imdb.com/'+ movie_page.find('div',{'itemprop':'aggregateRating'}).find('a').get('href')).read())
	male_female_table = score_page.find_all('table')[1].find_all('tr')[1:3]
	male_votes = int(re.search('[0-9,]+',male_female_table[0].find_all('td')[1].text).group())
	female_votes = int(re.search('[0-9,]+',male_female_table[1].find_all('td')[1].text).group())
	male_score = float(re.search('[0-9\.]+',male_female_table[0].find_all('td')[2].text).group())
	female_score = float(re.search('[0-9\.]+',male_female_table[1].find_all('td')[2].text).group())

	return score, votes, male_score, male_votes, female_score, female_votes

def get_movie_info(url):

	movie_page = BeautifulSoup(urllib2.urlopen(url).read())

	#Retrieve cast
	cast, writers, writer_type= get_cast(movie_page, url)

	#Scrape plots
	short_plot, plot = get_plot(movie_page)

	#Iterate through credit info (director, writer, etc)
	director = get_director(movie_page)

	#get IMDB score
	score, votes, male_score, male_votes, female_score, female_votes = get_imdbscore(movie_page)

	#Content Rating
	genre, content_rating, time, year = get_specs(movie_page)

	budget, prod_co = get_budget_production(movie_page)

	return({'url': url, 'score':score, 'votes':votes, 'male_score':male_score, 'male_votes':male_votes,
			'female_score':female_score,'female_votes':female_votes,'cast':cast, 'plot':plot, 'year':year,
			'short_plot':plot, 'director':director,'writers':writers,'writer_type':writer_type,'genre':genre,
			'content_rating':content_rating, 'budget':budget,'production co':prod_co, 'time':time})

if __name__ == "__main__":

	top200 = 'http://www.imdb.com/list/ls059288416/?start=1&view=compact&sort=listorian:asc&defaults=1&scb='
	top200soup = BeautifulSoup(urllib2.urlopen(top200).read())

	movie_table =  top200soup.find('table')
	movie_items = movie_table.find_all('tr')[1:]
	movie_dict= dict()

	for row in movie_items:
		info = row.find('td',{'class':'title'})
		print(info.text)
		movie_dict[info.text] = get_movie_info('http://www.imdb.com'+ info.find('a').get('href'))

	os.chdir('/Users/Sam/Desktop/Projects/RomComPlusMinus/')

	with open('data/movie_info.pickle','wb') as f:
		pickle.dump(movie_dict, f)

