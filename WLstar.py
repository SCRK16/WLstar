from collections import defaultdict
import random

from weighted_automaton import *

def closed_by_hand(wfa, S, E, t, membership_queries, SxE=None, txE=None, verbose=True):
	"""
	Asks the user to check if t x E is a linear combination of the rows in S x E
	Return the linear combination if it exists, otherwise return false
	For example: If S x E = [[0, 1, 0], [1, 0, 1]] and t = [1, 1, 1], return [1, 1]
		but if t = [1, 0, 2], return False
	"""
	if verbose:
		print("S:", S)
		print("E:", E)
	if SxE is None:
		for s in S:
			print(list(membership_queries[s+e] for e in E))
	else:
		print(SxE)
	print("t:", t)
	if txE is None:	
		print(list(membership_queries[t+e] for e in E))
	else:
		print(txE)
	res = input("Please enter the linear combination (or False if it does not exist): ")
	if res.lower() == "false":
		return False
	return list(int(x) for x in res.split())

def counterexample_by_hand(wfa, model, membership_queries):
	"""
	Asks the user to create a counterexample w by hand,
	which demonstrates that wfa and model are not equivalent,
	because wfa.member(w) is not equal to model.member(w)
	Return the counterexample if it exists, otherwise return None
	"""
	print("\nWfa:", wfa)
	print("\nModel:", model)
	found = False
	while not found:
		cex = input("\nPlease enter the counterexample (or None if it does not exist): ")
		found = True
		if cex == "None":
			return None
		if cex not in membership_queries:
			membership_queries[cex] = wfa.member(cex)
		print(membership_queries[cex])
		print(model.member(cex))
		if membership_queries[cex] == model.member(cex):
			found = False
			print(cex, " was not a counterexample.")
	return cex

def random_counterexample(wfa, model, membership_queries, tries=None, min_size=0, verbose=False):
	if verbose:
		print("Trying random words to find a counterexample.")
	if tries is None:
		tries = 2*len(wfa.alphabet)*len(wfa.weights) + 3
	n = len(wfa.weights)
	for k in range(1, tries):
		cex = ''.join(random.choices(wfa.alphabet, k=k+min_size))
		if cex not in membership_queries:
			membership_queries[cex] = wfa.member(cex)
		if membership_queries[cex] != model.member(cex):
			if verbose:
				print("Found counterexample:", cex)
			return cex
		elif verbose:
			print("Tried:", cex)
	return None

# If performance becomes an issue, try replacing lists with sets for S, E, SA
# Be careful: Some functions (like create machine) may depend on the ordering of the elements
def weighted_Lstar(wfa, check_closed=closed_by_hand, check_counterexample=counterexample_by_hand, verbose=False, count=False):
	"""Learns wfa using Lstar for weighted automata"""
	S = [""]
	E = [""]
	membership_queries = {} #Keep a dictionary of all previous membership queries to avoid repeated calls
	membership_count = 0
	closed_count = 0
	equivalence_count = 0
	cex_found = False
	closed_after_counterexample = 0
	while True:
		closed = False
		while not closed:
			closed = True
			for s in S:
				for e in E:
					se = s+e
					if se not in membership_queries:
						membership_queries[se] = wfa.member(se)
			SA = list(s + a for s in S for a in wfa.alphabet)
			lin_com = defaultdict(list)
			closed_count += 1
			for t in SA:
				if t in S: #Check if t is in S: cases of the form 0 0 ... 0 1 0 ... 0 0
					i = S.index(t)
					lin_com[t] = list(1 if j == i else 0 for j in range(0, len(S)))
				else:
					if verbose:
						print("Checking:", t)
					for e in E:
						te = t+e
						if te not in membership_queries:
							membership_queries[te] = wfa.member(te)
					c = check_closed(wfa, S, E, t, membership_queries, verbose=verbose)
					if c is False:
						closed = False
						cex_found = False
						S.append(t)
						break
					else:
						lin_com[t] = c
		if cex_found and count:
				closed_after_counterexample += 1
		model = create_machine(wfa.alphabet, S, (wfa.member(s) for s in S), lin_com)
		membership_count = len(membership_queries)
		equivalence_count += 1
		if verbose:
			print("Finding counterexample")
		cex = check_counterexample(wfa, model, membership_queries)
		if verbose:
			print("Counterexample:", cex)
		if cex is None:
			if verbose:
				print("S:", S, "E:", E)
				if count:
					print("Number of membership queries (excluding the last equivalence query):", membership_count)
					print("Times we checked if the table is closed:", closed_count)
					print("Number of equivalence queries:", equivalence_count)
					print("Number of times the table was closed after finding a counterexample:", closed_after_counterexample)
			if count:
				return model, membership_count, closed_count, equivalence_count, closed_after_counterexample
			return model
		cex_found = True
		E.extend(e for e in suffixes(cex) if e not in E)
		
	
def compare_machines(aut, res, prover=random_counterexample):
	"""Used to compare the orginal machine aut with the result of model learning res"""
	print("Number of states of the result:", len(res.weights), "\nNumer of states of the original:", len(aut.weights))
	print("Enter Result or Original to see the result or original automaton.")
	print("Enter Save to save the original automaton and the result.")
	print("Enter Prove to check if there are any counterexamples.")
	while True:
		aut_input = input("\nEnter some input string to try (or Stop to stop): ")
		if aut_input == "Stop":
			break
		elif aut_input == "Original":
			print(aut)
		elif aut_input == "Result":
			print(res)
		elif aut_input == "Save":
			print(save_automaton(aut, original=True, update_counter=False))
			print(save_automaton(res))
		elif aut_input == "Prove":
			print(prover(aut, res, {}, verbose=True))
		else:
			print("Original:", aut.member(aut_input))
			print("Model:   ", res.member(aut_input))