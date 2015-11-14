# Python script for predicting the scores of comments
from __future__ import division
import numpy as np 
import sqlite3
import pdb
import random
import string
from collections import defaultdict
from sklearn.linear_model import Ridge
from sklearn.svm import SVR
from sklearn import svm
import matplotlib.pyplot as plt

conn = sqlite3.connect('../data/database.sqlite')
data_size = 1000

# Calculates the entropy of a comment's body
def calc_entropy(word_array):
	entropy = 0
	num_words = len(word_array)
	frequencies = defaultdict(int)
	for word in word_array:
		frequencies[word] += 1
	for word in word_array:
		entropy += (frequencies[word] / num_words) * (np.log10(num_words) - np.log10(frequencies[word]))
	entropy *= (1/num_words)
	return entropy

# Strips punctuation and converts comment body to array of words
def convert_to_word_array(body):
	exclude = set(string.punctuation)
	body = ''.join(ch for ch in body if ch not in exclude).lower()
	tokens = body.split()
	return tokens

# Returns a dictionary of usernames -> number of comments by that user
def get_num_comments(data):
	num_comments = defaultdict(int)
	for entry in data:
		num_comments[entry[2]] += 1
	return num_comments

# Returns a class label from a comment's score:
# 0 = score <-10
# 1 = -10 <= score <= 0
# 2 = 0 < score < 10
# 3 = score >= 10
def get_class_label(score):
	if score < -10:
		return 0
	elif score <= 0:
		return 1
	elif score < 10:
		return 2
	return 3

# Modifies the data such that every feature value is between 0 and 1 inclusive
def normalize(data):
	data = data - np.tile(data.min(axis=0), (len(data), 1))
	maxes = data.max(axis=0)
	maxes[maxes == 0] = 1
	data = data / maxes
	return data

def load_data():

	cursor = conn.execute("SELECT created_utc, gilded, author, body, controversiality, edited, score FROM May2015 WHERE subreddit = 'aww' LIMIT "+str(data_size));
	data = cursor.fetchall()
	random.shuffle(data)
	samples = len(data)

	num_comments_dict = get_num_comments(data)

	for i in range(samples):
		entry = data[i]
		body = convert_to_word_array(entry[3])
		entropy = calc_entropy(body) if len(body) > 0 else 0
		comment_length = len(body)
		num_comments = num_comments_dict[entry[2]]

		entry = list(entry)
		del entry[2]
		del entry[2]
		entry = [entropy, comment_length, num_comments] + entry
		entry[-1] = get_class_label(entry[-1])
		data[i] = entry

	data = np.array(data)
	scores = data[:,-1]
	data = data[:, :-1]
	# Normalizing seemed to decrease accuracy, for now
	# data = normalize(data)
	train = data[(samples/2):, :-1]
	test = data[:(samples/2), :-1]
	train_scores = scores[(samples/2):]
	test_scores = scores[:(samples/2)]

	print 'Created train and test sets'
	return train, test, train_scores, test_scores

def train(train_set, scores):
	print 'Training model'
	model = svm.LinearSVC().fit(train_set, scores)
	print 'Finished training model'
	return model

def test(model, test_set, scores):
	print 'Computing generalization error'
	return model.score(test_set, scores), model.predict(test_set)

def plot(predictions, actual):
	samples = range(0, len(predictions))
	plt.plot(samples, predictions, 'ro')
	plt.plot(samples, actual, 'bo')
	plt.axis([0, samples[-1], -20, 20])
	plt.show()

if __name__=='__main__':
	random.seed(1000)
	train_set, test_set, train_scores, test_scores = load_data()
	model = train(train_set, train_scores)
	score, predictions = test(model, test_set, test_scores)
	# plot(predictions, test_scores)
	pdb.set_trace()

