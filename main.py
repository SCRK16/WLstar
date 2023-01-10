from collections import defaultdict
from z3 import *

from weighted_automaton import *
from WLstar import *

def closed_by_z3(wfa, S, E, t, membership_queries, SxE=None, txE=None, verbose=False):
	if SxE is not None or txE is not None:
		raise NotImplementedError("Supplying SxE and txE with arguments is not yet supported for Z3")
	s = Solver()
	xs = [Int(s) for s in S]
	for e in E:
		s.add(sum(membership_queries[s+e] * xs[i] for i,s in enumerate(S)) == membership_queries[t+e])
	if s.check() == sat:
		m = s.model()
		if verbose:
			print("S:", S, '\nE:', E, '\nt:', t, "\nsat", m)
		return [m[xs[i]].as_long() if m[xs[i]] is not None else 0 for i,s in enumerate(S)]
	else:
		if verbose:
			print(S, '\n', E, '\n', t, "\nunsat")
		return False

if __name__ == "__main__": #load("Examples/13o.txt")
	#aut = random_automaton(alphabet=['a', 'b'], min_states=5, max_states=5, pos_weights=list(range(1, 5)), min_transitions=5) 
	aut = load_automaton("Examples/benchmark/Automata/a4_92.txt")
	print(aut)
	res = weighted_Lstar(aut, check_closed=closed_by_z3, check_counterexample=random_counterexample, verbose=False, count=True)
	compare_machines(aut, res, prover=random_counterexample)