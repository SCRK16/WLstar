from collections import defaultdict, deque
from sage.interfaces.gap import *
from math import gcd
from functools import reduce
from time import process_time

from weighted_automaton import *
from WLstar import *

# Calls to gap look like: result = gap("SolutionIntMat([[3,1], [2,4]], [5,5])")
def closed_by_gap(wfa, S, E, t, membership_queries, SxE=None, txE=None, verbose=False):
	if SxE is None:
		SxE = [[membership_queries[s+e] for e in E] for s in S]
	if txE is None:
		txE = [membership_queries[t+e] for e in E]
	input = "SolutionIntMat(" + str(SxE) + ", " + str(txE) + ")"
	result = gap(input)
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

def handle_counterexample(wfa, cex, S, E, transitions, membership_table, membership_queries, GCDs, verbose=False):
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
	return E, transitions, membership_table, membership_queries, GCDs
	
def check_table_closed_count(wfa, S, E, transitions, membership_queries, membership_table, GCDs, closed_count=0, cex_found=False, check_closed=closed_by_gap, verbose=False):
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
					if t+e not in membership_queries:
						membership_queries[t+e] = wfa.member(t+e)
				gcdt = GCDs[t[:-1]] if GCDs[t[:-1]] else 1 #Default to 1 if GCD is 0
				txE = [membership_queries[t+e] // gcdt for e in E]
				SxE = [[membership_table[s][e] for e in E] for s in S]
				c = check_closed(wfa, S, E, t, membership_queries, SxE=SxE, txE=txE, verbose=verbose)
				if c is False:
					closed = False
					cex_found = False
					GCDt = reduce(gcd, (membership_queries[t+e] for e in E))
					if GCDt % GCDs[t[:-1]] != 0:
						# Our assumption for the GCD of t[:-1] was wrong. This yields a counterexample, which we handle (which updates the GCD) 
						for e in E:
							if t+e not in membership_queries:
								membership_queries[t+e] = wfa.member(t+e)
							if membership_queries[t+e] % GCDs[t[:-1]] != 0:
								E, transitions, membership_table, membership_queries, GCDs = handle_counterexample(wfa, t+e, S, E, transitions, membership_table, membership_queries, GCDs, verbose=verbose)
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
	
def check_table_closed(wfa, S, E, transitions, membership_queries, membership_table, GCDs, check_closed=closed_by_gap, verbose=False):
	closed = False
	while not closed:
		closed = True
		SA = list(s + a for s in S for a in wfa.alphabet)
		lin_com = defaultdict(list)
		lin_com[""] = [0]*len(S)
		lin_com[""][0] = transitions[""]
		for t in SA:
			if t in S:
				lin_com[t] = [0]*len(S)
				lin_com[t][S.index(t)] = transitions[t]
			else:
				#print("Finding linear combination for", t)
				for e in E:
					if t+e not in membership_queries:
						membership_queries[t+e] = wfa.member(t+e)
				gcdt = GCDs[t[:-1]] if GCDs[t[:-1]] else 1 #Default to 1 if GCD is 0
				txE = [membership_queries[t+e] // gcdt for e in E]
				SxE = [[membership_table[s][e] for e in E] for s in S]
				c = check_closed(wfa, S, E, t, membership_queries, SxE=SxE, txE=txE, verbose=verbose)
				if c is False:
					closed = False
					GCDt = reduce(gcd, (membership_queries[t+e] for e in E))
					if GCDt % GCDs[t[:-1]] != 0:
						# Our assumption for the GCD of t[:-1] was wrong. This yields a counterexample, which we handle (which updates the GCD) 
						for e in E:
							if t+e not in membership_queries:
								membership_queries[t+e] = wfa.member(t+e)
							if membership_queries[t+e] % GCDs[t[:-1]] != 0:
								E, transitions, membership_table, membership_queries, GCDs = handle_counterexample(wfa, t+e, S, E, transitions, membership_table, membership_queries, GCDs, verbose=verbose)
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
	return lin_com, S, transitions, membership_queries, membership_table, GCDs

def remove_redundant(wfa, S, E, membership_queries, membership_table, GCDs, transitions, closed_count, cex_found, total_teacher_time, check_closed=closed_by_gap, check_counterexample=HKC, verbose=False):
	for i in range(len(S)-1, 0, -1): #Note: Stop at 1 so "" doesn't get removed from S
		SxE = [[membership_table[s][e] for e in E] for j, s in enumerate(S) if j != i]
		t = S[i]
		gcdt = GCDs[t[:-1]] if t[:-1] in GCDs else 1
		txE = [membership_queries[t+e] // gcdt for e in E]
		ci = check_closed(wfa, S, E, t, membership_queries, SxE=SxE, txE=txE, verbose=False)
		if ci is not False:
			if verbose:
				print("Removing", t, "ci:", list(ci))
			previously_removed.add(S[i])
			del S[i]
			del membership_table[t]
			del GCDs[t]
			del transitions[t]
	lin_com, S, transitions, membership_queries, membership_table, GCDs, closed_count, cex_found = check_table_closed_count(wfa, S, E, transitions, membership_queries, membership_table, GCDs, closed_count, cex_found, verbose=verbose)
	model = create_machine(wfa.alphabet, S, (membership_table[s][""] for s in S), lin_com)
	membership_count = len(membership_queries)
	teacher_start = process_time()
	cex = check_counterexample(wfa, model, membership_queries)
	teacher_stop = process_time()
	total_teacher_time += teacher_stop - teacher_start
	if cex is None:
		if verbose:
			print("S:", S, "E:", E)
			for s in S:
				print(s, [membership_queries[s+e] for e in E], GCDs[s])
			for t in (s + a for s in S for a in wfa.alphabet if s + a not in S):
				print(t, [membership_queries[t+e] for e in E])
		return model, membership_count, total_teacher_time
	elif verbose:
		print("Found counterexample after removing states:", cex)
	return None, membership_count, total_teacher_time

def modified_weighted_Lstar(wfa, check_closed=closed_by_gap, check_counterexample=HKC, verbose=False, count=False):
	"""
	Learns wfa using Lstar for weighted automata
	Makes two changes from the standard algorithm to get smaller results:
	1) The GCD of rows of SxE is computed. The GCD becomes the transition weight, the other factors are state weights
	2) At the end of the algorithm, check if any of the rows have become redundant by seeing if they are a linear combination of the other rows
	Also keeps track of statistics to be used in analysis of the algorithm
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
	total_teacher_time = 0
	while True:
		lin_com, S, transitions, membership_queries, membership_table, GCDs, closed_count, cex_found = check_table_closed_count(wfa, S, E, transitions, membership_queries, membership_table, GCDs, closed_count=closed_count, cex_found=cex_found, verbose=verbose)
		if cex_found and count:
			closed_after_counterexample += 1
		model = create_machine(wfa.alphabet, S, (membership_table[s][""] for s in S), lin_com)
		membership_count = len(membership_queries)
		equivalence_count += 1
		teacher_start = process_time()
		cex = check_counterexample(wfa, model, membership_queries)
		teacher_stop = process_time()
		total_teacher_time += teacher_stop - teacher_start
		if verbose:
			print("Counterexample:", cex)
			if cex is not None:
				print("WFA:", wfa.member(cex), "Model:", model.member(cex))
		if cex is None:
			model, membership_count, total_teacher_time = remove_redundant(wfa, S, E, membership_queries, membership_table, GCDs, transitions, closed_count, cex_found, total_teacher_time, check_closed=check_closed, check_counterexample=check_counterexample, verbose=False)
			return model, membership_count, closed_count, equivalence_count, closed_after_counterexample, total_teacher_time
		cex_found = True
		E, transitions, membership_table, membership_queries, GCDs = handle_counterexample(wfa, cex, S, E, transitions, membership_table, membership_queries, GCDs, verbose=verbose)

def basis_by_gap(wfa, S, E, membership_queries, membership_table, GCDs, total_teacher_time, check_closed=closed_by_gap, check_counterexample=HKC, verbose=False):
	E_ext = E + [a + e for a in wfa.alphabet for e in E]
	for s in S:
		for e in E_ext:
			if e not in membership_table[s]:
				membership_queries[s+e] = wfa.member(s+e)
				membership_table[s][e] = membership_queries[s+e] // GCDs[s]
	SxE = [[membership_table[s][e] for e in E_ext] for s in S]
	input = "BaseIntMat(" + str(SxE) + ")"
	gap_result = gap(input)
	basis_ext = [[int(y) for y in x] for x in gap_result]
	basis_map = {i: {e: basis_ext[i][j] for j, e in enumerate(E_ext)} for i in range(len(basis_ext))}
	basis = [[basis_map[i][e] for e in E] for i in range(len(basis_ext))]
	if verbose:
		for b in basis:
			print(b)
	epsilonxE = [membership_queries[e] for e in E]
	initial = closed_by_gap(wfa, S, E, "", membership_queries, SxE=basis, txE=epsilonxE, verbose=verbose)
	model = Weighted_Automaton(alphabet=wfa.alphabet, weights=[basis_map[i][""] for i in range(len(basis_ext))], initial=initial)
	for q0 in range(len(basis_ext)):
		for a in wfa.alphabet:
			txE = [basis_map[q0][a+e] for e in E]
			transitions = closed_by_gap(wfa, S, E, a, membership_queries, SxE=basis, txE=txE, verbose=verbose)
			for q1, w in enumerate(transitions):
				if w != 0:
					model.add_transition(q0, a, q1, w)
	teacher_start = process_time()
	cex = check_counterexample(wfa, model, membership_queries, verbose=verbose)
	teacher_stop = process_time()
	total_teacher_time += teacher_stop - teacher_start
	return cex, model, membership_queries, total_teacher_time
	
def minimal_weighted_Lstar(wfa, check_closed=closed_by_gap, check_counterexample=HKC, verbose=False):
	"""
	Learns wfa using Lstar for weighted automata
	Makes two changes from the standard algorithm to get smaller results:
	1) The GCD of rows of SxE is computed. The GCD becomes the transition weight, the other factors are state weights
	2) At the end of the algorithm, calculate basisvectors for the rows in S, then use those as the states instead of the rows themselves
	"""
	S = [""]
	E = [""]
	membership_queries = {}
	membership_queries[""] = wfa.member("")
	membership_table = {"": {"": 1}} # membership_queries divided by GCD of row
	GCDs = {"": membership_queries[""]}
	transitions = {"": membership_queries[""]}
	closed_count = 0
	equivalence_count = 0
	cex_found = False
	closed_after_counterexample = 0
	total_teacher_time = 0
	while True:
		lin_com, S, transitions, membership_queries, membership_table, GCDs, closed_count, cex_found = check_table_closed_count(wfa, S, E, transitions, membership_queries, membership_table, GCDs, closed_count=closed_count, cex_found=cex_found, check_closed=check_closed, verbose=verbose)
		if cex_found:
			closed_after_counterexample += 1
		model = create_machine(wfa.alphabet, S, (membership_table[s][""] for s in S), lin_com)
		equivalence_count += 1
		teacher_start = process_time()
		cex = check_counterexample(wfa, model, membership_queries, verbose=verbose)
		teacher_stop = process_time()
		total_teacher_time += teacher_stop - teacher_start
		if verbose:
			print("Counterexample:", cex)
			if cex is not None:
				print("WFA:", wfa.member(cex), "Model:", model.member(cex))
		if cex is None:
			while True:
				#Calculate basisvectors
				cex, model, membership_queries, total_teacher_time = basis_by_gap(wfa, S, E, membership_queries, membership_table, GCDs, total_teacher_time, check_closed=check_closed, check_counterexample=check_counterexample, verbose=verbose)
				if cex is None:
					return model, len(membership_queries), closed_count, equivalence_count, closed_after_counterexample, total_teacher_time
				E, transitions, membership_table, membership_queries, GCDs = handle_counterexample(wfa, cex, S, E, transitions, membership_table, membership_queries, GCDs, verbose=verbose)
		cex_found = True
		E, transitions, membership_table, membership_queries, GCDs = handle_counterexample(wfa, cex, S, E, transitions, membership_table, membership_queries, GCDs, verbose=verbose)

if __name__ == "__main__":
	#aut = random_automaton(alphabet=['a', 'b'], min_states=2, max_states=2, pos_weights=list(range(-5, 5)), min_transitions=2)
	aut = load_automaton("Examples/38o.txt")
	print(aut)
	res, membership_count, closed_count, equivalence_count, closed_after_counterexample, total_teacher_time = minimal_weighted_Lstar(aut, check_closed=closed_by_gap, check_counterexample=HKC, verbose=True)
	print(membership_count, closed_count, equivalence_count, closed_after_counterexample, total_teacher_time)
	#res = weighted_Lstar(aut, check_closed=closed_by_gap, check_counterexample=HKC, verbose=True)
	compare_machines(aut, res, prover=HKC)