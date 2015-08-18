#!/usr/bin/env python
import sys, re, json, random 
from collections import defaultdict, Counter # to use hashable dict for probability map
try: import cPickle as pickle # to save db 
except: import pickle

reload(sys)
sys.setdefaultencoding('utf-8')

class MarkovNGramChain:
	def __init__(self, n):
		self.map = defaultdict(Counter) # use hashed dict to higher performance
		self.norm_map = defaultdict(Counter) # use hashed dict to higher performance
		self.starts = []
		if (n < 2): raise Exception("Allowed only n>=2 for n-grams")
		self.n = n

	# prepare text, break it into parts (sentences)
	def _tokenize(self, text):
		# use separators to split str into parts
		parts = []
		text = text.replace('\n', ' ')
		
		for p in re.split(r'\.|\;|\:|\ - |\!|\?|\"|\(|\)|\.\.\.|\[|\]', text):
			body = p.decode('utf-8').lower().split()
			s = ['#'] +	body + ['.'] # sharp is begin, dot is end 

			# process ',' at the end of word
			s2 = []
			for i in s: 
				if i.endswith(','): s2 += [i[0:-1]] + [',']
				else: s2 += [i]

			if body: parts.append(s2)
		return parts
		
	# markov chain learning for one part of text (sentence)
	def _train_part(self, line):
		n = self.n
		ngrams = zip(*[line[i:] for i in range(n + 1)])
		
		# calculate n-grams frequencies
		for t in ngrams:
			a, b = t[:-1], t[-1]
			a = ' '.join(a)
			self.map[a][b] += 1
			
	# common train for all text
	def train(self, text):
		# prepare text
		lines = self._tokenize(text)
		# train line by line
		[self._train_part(line) for line in lines] 
		
		# normalize frequencies to get probabilities
		for a in self.map:
			sum = 0.0
			map_a = self.map[a]
			norm_map_a = self.norm_map[a]
			
			for b in map_a: sum += map_a[b]
			for b in map_a: norm_map_a[b] = map_a[b] / sum
		
		# calculate sentences starts
		self._calculate_starts()
	
	# scan map and get n-grams are starting from '#'
	def _calculate_starts(self):			
		self.starts = [s for s in self.norm_map if len(s)>0 and s[0]=='#']
	
	def	_generate_sentence(self):
		norm_map = self.norm_map
		start = random.choice(list(self.starts)) # sentence start ngram
		result = last = start
		
		for i in xrange(42): # use magic number 42 :-) This is maximal lenght of generated sentence.
			sample = random.random()
			node = self.norm_map[last]
			maximum = 0.0
			bestword = ''
			candidates = []
			
			for word, prob in node.items():
				if maximum < prob: # if we don't find word(sample>prob), use maximum 
					bestword = word
					maximum = prob
				if sample > prob:
					candidates += [word]
					
			# select from word which sample > prob, use maximum prob if no candidates
			if candidates:
				bestword = random.choice(candidates)
			
			# process '.' as predicted word
			if bestword == '.':
				if i>1: break # stop if '.' and '.' is not only one
				else: continue # escape if '.' in sentence only
			
			# concantenate result + bestword
			result += (' ' if bestword != ',' else '') + bestword
			
			# evaluate next n-gram: take off the first word and plus best word
			last = ' '.join(last.split()[1:] + [bestword]) 
				
		if result.endswith(','): result = result[:-1]
		return result[2:].capitalize() + '.' # remove '#' and capitalize first symbol
	
	# generate text
	def generate(self, seed, length): 
		random.seed(seed)
		return ' '.join([self._generate_sentence() for l in xrange(length)])
		
	# convert map to str to control the train result
	def __str__(self):
		s = ''
		c = 0; 
		# walk by begin of ngram
		for a in self.map:
			printed = False
			
			# walk by end of ngram
			for b in self.map[a]:
				if self.map[a][b] > 1: # print only interesting variants
					if not printed: 
						s += a + '\n'; 
						printed = True
					
					s += '\t' + b + '\t' + str(self.map[a][b])+'\n'
					c += 1
					if c>1000: return s
			
		return s
		
	# save map into json db 
	def save(self, filename):
		pickle.dump(self.norm_map, open(filename, 'wb'))
		
	# save map into json db 
	def load(self, filename):
		try: self.norm_map = pickle.load(open(filename, 'rb'))
		except: return False
		self._calculate_starts()
		return True
				
if __name__ == '__main__':
	# read texts from all txt files in base dir 
	import os
	base_dir = 'base'
	texts = [unicode(open(base_dir+'/'+f).read()) for f in os.listdir(base_dir) if f.endswith('.txt')]

	# build MarkovNGramChain model 
	db_file = 'db.pickle'
	chain = MarkovNGramChain(2) # init with N (N-gram)
	if not chain.load(db_file):
		print 'Train MarkovNGramChain'
		[chain.train(text) for text in texts] # train file by file 
		chain.save(db_file) # save map model into file 
		#open('db.txt', 'w').write(str(chain).encode('windows-1251')) # write control portion of map to file
		
	# load MarkovNGramChain model
	else: print 'MarkovNGramChain have been loaded from file', db_file
	
	# generate text
	print 'Generate text'
	text = chain.generate(42, 100) # seed and sentences number at input
	open('out.txt', 'w').write(text)