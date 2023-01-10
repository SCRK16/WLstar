from collections import defaultdict, deque
from sage.interfaces.gap import *
from math import gcd
from functools import reduce

from weighted_automaton import *
from WLstar import *

# Calls to gap look like: result = gap("SolutionIntMat([[3,1], [2,4]], [5,5])")
def closed_by_gap(wfa, S, E, t, membership_queries, SxE=None, txE=None, verbose=False):
	if SxE is None:
		SxE = [[membership_queries[s+e] for e in E] for s in S]
	if txE is None:
		txE = [membership_queries[t+e] for e in E]
	input = "SolutionIntMat(" + str(SxE) + ", " + str(txE) + ")"
	#if verbose:
	#	print(input)
	result = gap(input)
	#if verbose:
	#	print(result)
	if str(result) == "fail":
		if verbose:
			print("GAP: Fail, len S/len E:", len(S), len(E), "t:", t)
		return False
	return map(int, list(result))

def HKC(wfa, model, membership_queries, verbose=False):
	if verbose:
		print("Running HKC to find a counterexample.")
	R = []
	todo = deque()
	m1 = wfa.member_distribution("")
	m2 = model.member_distribution("")
	if m1[0] != m2[0]:
		return ""
	todo.append(("", wfa.initial, model.initial))
	while todo:
		w, v1, v2 = todo.popleft()
		v = v1+v2
		input = "SolutionIntMat(" + str(R) + ", " + str(v) + ")"
		result = gap(input)
		if str(result) == "fail":
			for a in wfa.alphabet:
				m1 = wfa.member_distribution(a, distribution=v1)
				m2 = model.member_distribution(a, distribution=v2)
				if m1[0] != m2[0]:
					if verbose:
						print("Found counterexample:", w+a)
					return w+a
				todo.append((w+a, m1[1], m2[1]))
			R.append(v)
	if verbose:
		print("No counterxample found")
	return None
	
def check_table_closed(wfa, S, E, transitions, membership_queries, membership_table, GCDs, closed_count, cex_found, check_closed=closed_by_gap, verbose=False):
	closed = False
	while not closed:
		closed = True
		SA = list(s + a for s in S for a in wfa.alphabet)
		lin_com = defaultdict(list)
		lin_com[""] = [0]*len(S)
		lin_com[""][0] = transitions[""]
		closed_count += 1
		for t in SA:
			if t in S:
				lin_com[t] = [0]*len(S)
				lin_com[t][S.index(t)] = transitions[t]
			else:
				#print("Finding linear combination for", t)
				for e in E:
					te = t+e
					if te not in membership_queries:
						membership_queries[te] = wfa.member(te)
				gcdt = GCDs[t[:-1]] if GCDs[t[:-1]] else 1 #Default to 1 if GCD is 0
				txE = [membership_queries[t+e] // gcdt for e in E]
				SxE = [[membership_table[s][e] for e in E] for s in S]
				c = check_closed(wfa, S, E, t, membership_queries, SxE=SxE, txE=txE, verbose=verbose)
				if c is False:
					closed = False
					cex_found = False
					GCDt = reduce(gcd, (membership_queries[t+e] for e in E))
					#Should also update for all prefixes of t
					if GCDt % GCDs[t[:-1]] != 0:
						new_gcd = gcd(GCDt, GCDs[t[:-1]])
						if verbose:
							print("Updating GCD for", t[:-1], "from", GCDs[t[:-1]], "to", new_gcd)
						GCDs[t[:-1]] = new_gcd
						for e in E:
							membership_table[t[:-1]][e] = membership_queries[t[:-1]+e] // new_gcd
						gcds = GCDs[t[:-2]] if t[:-2] in GCDs and t[:-2] != t[:-1] else 1
						transitions[t[:-1]] = GCDs[t[:-1]] // gcds
					else:
						S.append(t)
						GCDs[t] = GCDt
						transitions[t] = GCDs[t] // GCDs[t[:-1]]
						membership_table[t] = {}
						for e in E:
							membership_table[t][e] = membership_queries[t+e] // GCDs[t]
					break
				else:
					lin_com[t] = list(c)
	return lin_com, S, transitions, membership_queries, membership_table, GCDs, closed_count, cex_found
	
def minimal_weighted_Lstar(wfa, check_closed=closed_by_gap, check_counterexample=HKC, verbose=False, count=False):
	"""
	Learns wfa using Lstar for weighted automata
	Makes two changes from the standard algorithm to get smaller results:
	1) The GCD of rows of SxE is computed. The GCD becomes the transition weight, the other factors are state weights
	2) When a new row is added, we check if a previously added row is now a linear combination of the other rows
	For the moment, assumes that the inital distribution is (1, 0, 0, 0, ...) 
	"""
	S = [""]
	E = [""]
	membership_queries = {}
	membership_queries[""] = wfa.member("")
	membership_table = {"": {"": 1}}
	GCDs = {"": membership_queries[""]}
	transitions = {"": membership_queries[""]}
	previously_removed = set()
	membership_count = 0
	closed_count = 0
	equivalence_count = 0
	cex_found = False
	closed_after_counterexample = 0
	while True:
		lin_com, S, transitions, membership_queries, membership_table, GCDs, closed_count, cex_found = check_table_closed(wfa, S, E, transitions, membership_queries, membership_table, GCDs, closed_count, cex_found, verbose=verbose)
		if cex_found and count:
			closed_after_counterexample += 1
		model = create_machine(wfa.alphabet, S, (membership_table[s][""] for s in S), lin_com)
		membership_count = len(membership_queries)
		equivalence_count += 1
		# Finding counterexample
		cex = check_counterexample(wfa, model, membership_queries)
		if verbose:
			print("Counterexample:", cex)
			if cex is not None:
				print("WFA:", wfa.member(cex), "Model:", model.member(cex))
		if cex is None:
			#Check if states have become redundant
			for i in range(len(S)-1, 0, -1): #Note: Stop at 1 so "" doesn't get removed from S
				SxE = [[membership_table[s][e] for e in E] for j, s in enumerate(S) if j != i]
				t = S[i]
				gcdt = GCDs[t[:-1]] if t[:-1] in GCDs else 1
				txE = [membership_queries[t+e] // gcdt for e in E]
				ci = closed_by_gap(wfa, S, E, t, membership_queries, SxE=SxE, txE=txE, verbose=False)
				if ci is not False:
					if verbose:
						print("Removing", t, "ci:", list(ci))
					previously_removed.add(S[i])
					del S[i]
					del membership_table[t]
					del GCDs[t]
					del transitions[t]
			lin_com, S, transitions, membership_queries, membership_table, GCDs, closed_count, cex_found = check_table_closed(wfa, S, E, transitions, membership_queries, membership_table, GCDs, closed_count, cex_found, verbose=verbose)
			model = create_machine(wfa.alphabet, S, (membership_table[s][""] for s in S), lin_com)
			membership_count = len(membership_queries)
			cex = check_counterexample(wfa, model, membership_queries)
			if cex is None:
				if verbose:
					print("S:", S, "E:", E)
					for s in S:
						print([membership_queries[s+e] for e in E], GCDs[s])
					for t in (s + a for s in S for a in wfa.alphabet if s + a not in S):
						print(t, [membership_queries[t+e] for e in E])
				if count:
					return model, membership_count, closed_count, equivalence_count, closed_after_counterexample
				return model
			elif verbose:
				print("Found counterexample after removing states:", cex)
		cex_found = True
		suff = [e for e in suffixes(cex) if e not in E]
		for s in reversed(S):
			gcdo = GCDs[s]
			GCDs[s] = reduce(gcd, (GCDs[s+a] for a in wfa.alphabet if s+a in GCDs), GCDs[s])
			if verbose and gcdo != GCDs[s]:
				print("Changed GCD for", s, "from", gcdo, "to", GCDs[s])
			for e in suff:
				if s+e not in membership_queries:
					membership_queries[s+e] = wfa.member(s+e)
			gcds = reduce(gcd, (membership_queries[s+e] for e in suff), GCDs[s])
			if gcds != gcdo:
				gcdo = gcds
				if verbose:
					print("New gcd for '", s, "'", GCDs[s], gcds)
				GCDs[s] = gcds
				for e in E:
					membership_table[s][e] = membership_queries[s+e] // GCDs[s]
			for e in suff:
				membership_table[s][e] = membership_queries[s+e] // GCDs[s]
			#Below: Special case for if suff is empty (which happens when we made a bad assumption about the GCDS)
			if gcdo != GCDs[s]:
				for e in E:
					se = s+e
					membership_table[s][e] = membership_queries[se] // GCDs[s]
		for s in S:
			gcds = GCDs[s[:-1]] if s[:-1] in GCDs and s[:-1] != s else 1 #Need check s[:-1] != s because ""[:-1] == ""
			transitions[s] = GCDs[s] // gcds
		E.extend(suff)

if __name__ == "__main__":
	#aut = random_automaton(alphabet=['a', 'b'], min_states=2, max_states=2, pos_weights=list(range(-5, 5)), min_transitions=2)
	#aut = load_automaton("Examples/benchmark/Automata/abc10_65.txt")
	aut = load_automaton("Examples/benchmark/Automata/a6_91.txt")
	#aut = load_automaton("Examples/benchmark/Automata/ab4_18.txt")
	print(aut)
	res, membership_count, closed_count, equivalence_count, closed_after_counterexample = minimal_weighted_Lstar(aut, check_closed=closed_by_gap, check_counterexample=HKC, verbose=False, count=True)
	#res = weighted_Lstar(aut, check_closed=closed_by_gap, check_counterexample=HKC, verbose=True)
	compare_machines(aut, res, prover=HKC)