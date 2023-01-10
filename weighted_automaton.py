from collections import defaultdict
import random

class Weighted_Automaton:
	""""
	Weighted automaton with states q0...q(len(weights))
	alphabet: list of strings, the alphabet the weighted automata is working on
	weights: list of elements of a semiring, giving the weights of each state (q0 has weight weights[0], etc.)
	transitions: dictionary of transitions mapping (q0, a) to a list of (q1, w) where:
		q0: integer, the starting state
		a: element of the alphabet, letter read by the transition
		q1: integer, the ending state
		w: semiring element, weight of the transition
	initial: list of semiring elements, initial distributions of weights over the state
	"""
	def __init__(self, alphabet=None, weights=None, transitions=None, initial=None):
		if alphabet is None:
			self.alphabet = []
		else:
			self.alphabet = list(alphabet)
		if weights is None:
			self.weights = []
		else:
			self.weights = list(weights)
		if transitions is None:
			self.transitions = defaultdict(list)
		else:
			self.transitions = transitions
		if initial is None:
			self.initial = [0] * len(self.weights)
			if len(self.weights) > 0:
				self.initial[0] = 1
		else:
			self.initial = list(initial)
			
	def __str__(self):
		return "Alphabet: {0}\nWeights: {1}\nTransitions: {2}\nInitial: {3}".format(str(self.alphabet), str(self.weights),
			str([(k[0], k[1], r[0], r[1]) for k, v in self.transitions.items() for r in v]), str(self.initial))
	
	def add_state(self, weight, initial=0, verbose=False):
		self.weights.append(weight)
		self.initial.append(initial)
		if confirm:
			print("State {0} has weight {1}".format(len(self.weights)-1, weight))
	
	def add_transition(self, q0, a, q1, w):
		if q0 < len(self.weights) and q1 < len(self.weights) and a in self.alphabet:
			self.transitions[(q0, a)].append((q1, w))
		else:
			print("Invalid transition: Not added to the automaton")
			if q0 >= len(self.weights):
				print("Initial state {0} does not exist, there are {1} states".format(q0, len(self.weights)-1))
			if q1 >= len(self.weights):
				print("Ending state {0} does not exist, there are {1} states".format(q1, len(self.weights)-1))
			if a not in self.alphabet:
				print("Letter {0} not in alphabet, alphabet is {1}".format(a, self.alphabet))
	
	def member(self, word, verbose=False):
		distribution = self.initial
		for a in word:
			next_distribution = [0] * len(self.weights)
			for q0, w1 in enumerate(distribution):
				ts = self.transitions[(q0, a)]
				for q1, w2 in ts:
					next_distribution[q1] += w1 * w2
			distribution = next_distribution
		if verbose:
			print(word, distribution, self.weights)
		return sum(a*b for a, b in zip(distribution, self.weights))
		
	def member_distribution(self, word, distribution = None, verbose=False):
		if distribution is None:
			distribution = self.initial
		for a in word:
			next_distribution = [0] * len(self.weights)
			for q0, w1 in enumerate(distribution):
				ts = self.transitions[(q0, a)]
				for q1, w2 in ts:
					next_distribution[q1] += w1 * w2
			distribution = next_distribution
		if verbose:
			print(word, distribution, self.weights)
		return sum(a*b for a, b in zip(distribution, self.weights)), distribution
		
def random_automaton(alphabet=['a'], min_states=1, max_states=5, pos_weights=list(range(1, 5)), min_transitions=0, max_transitions=5):
	"""The number of transitions will be max_states*len(alphabet) + max_transitions"""
	weights = []
	num_states = random.randint(min_states, max_states)
	for i in range(num_states):
		weights.append(random.choice(pos_weights))
	aut = Weighted_Automaton(alphabet, weights)
	for a in alphabet:
		for q0 in range(num_states):
			w = random.choice(pos_weights)
			q1 = random.randint(0, num_states-1)
			aut.add_transition(q0, a, q1, w)
	extra_transitions = random.randint(min_transitions, max_transitions)
	for i in range(extra_transitions):
		q0 = random.randint(0, num_states-1)
		a = random.choice(alphabet)
		q1 = random.randint(0, num_states-1)
		w = random.choice(pos_weights)
		aut.add_transition(q0, a, q1, w)
	return aut
	
def save_automaton(aut, filename=None, original=False, update_counter=True):
	if filename is None:
		with open("Examples/counter.txt", "r") as counter_file:
			c = int(counter_file.read())
		if update_counter:
			with open("Examples/counter.txt", "w") as counter_file:
				counter_file.write(str(c+1))
		filename = "Examples/{0}{1}.txt".format(str(c), 'o' if original else 'r')
	a = ' '.join(aut.alphabet)
	w = ' '.join(map(str, aut.weights))
	t = ''.join(map(str, ((k[0], k[1], r[0], r[1]) for k, v in aut.transitions.items() for r in v)))
	i = ' '.join(map(str, aut.initial))
	aut_str = "{0}\n{1}\n{2}\n{3}".format(a, w, t, i)
	with open(filename, "w") as file:
		file.write(aut_str)
	return aut_str
	
def load_automaton(filename):
	with open(filename, "r") as file:
		result = file.read().split('\n')
	result[0] = result[0].split(' ')
	result[1] = (int(x) for x in result[1].split(' '))
	result[3] = (int(x) for x in result[3].split(' '))
	result[2] = result[2].strip(')').split(')')
	result[2] = [r[1:].split(", ") for r in result[2]]
	result[2] = [(int(r[0]), r[1].replace('"', "").replace("'", ""), int(r[2]), int(r[3])) for r in result[2]]
	aut = Weighted_Automaton(alphabet=result[0], weights=result[1], initial=result[3])
	for q0, a, q1, w in result[2]:
		aut.add_transition(q0, a, q1, w)
	return aut
	
def create_machine(A, S, weights, lin_com):
	initial = lin_com[""] if "" in lin_com else None
	aut = Weighted_Automaton(alphabet=A, weights=weights, initial=initial)
	for q0, s in enumerate(S):
		for a in A:
			for q1, w in enumerate(lin_com[s + a]):
				if w != 0:
					aut.add_transition(q0, a, q1, w)
	return aut
	
def suffixes(w):
	"""
	The suffixes of w, including w itself
	Excludes the empty string, unless w is the empty string,
	in which case the iterator will only contain the empty string
	Example: suffixes("abc") = ("c", "bc", "abc")
	Example: suffixes("") = ("")
	"""
	if w == "":
		return ("", )
	return (w[-i:] for i in range(1, len(w) + 1))

def prefixes(w):
	"""
	The prefixes of w, excluding w, including the empty string
	Example: prefixes("abc") = ("", "a", "ab")
	Example: prefixes("") = ("")
	"""
	if w == "":
		return ("", )
	return (w[:i] for i in range(len(w)))