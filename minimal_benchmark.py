from weighted_automaton import *
from WLstar import random_counterexample
from sage_main import closed_by_gap, modified_weighted_Lstar, minimal_weighted_Lstar, HKC

from time import perf_counter, process_time

if __name__ == "__main__":
	method = "GapHKC"
	version = "Basis/"
	closed = closed_by_gap
	#counterexample = random_counterexample
	counterexample = HKC

	progress_name = "Examples/benchmark/Results" + method + version + "progress.txt"
	with open(progress_name, "r") as progress_file:
		progress = progress_file.read().split(" ")
	progress[0] = list(progress[0])
	progress[1] = int(progress[1])
	progress[2] = int(progress[2])
	alph_todo = list(filter(lambda x: x >= progress[0], (['a'], ['a', 'b'], ['a', 'b', 'c'], ['a', 'b', 'c', 'd'])))

	for alph in alph_todo:
		print("aplh", alph)
		for nstates in range(progress[1] if alph == progress[0] else 1, 11):
			print("nstates", nstates)
			for i in range(progress[2] if alph == progress[0] and nstates == progress[1] else 1, 101):
				print("i", i)
				aut_file = "Examples/benchmark/Automata/" + "".join(alph) + str(nstates) + "_" + str(i) + ".txt"
				aut = load_automaton(filename=aut_file)
				start_time = process_time()
				start_perf = perf_counter()
				result = minimal_weighted_Lstar(aut, check_closed=closed, check_counterexample=counterexample)
				stop_time = process_time()
				stop_perf = perf_counter()
				total_time = stop_time - start_time
				total_perf = stop_perf - start_perf
				if result[0] is None:
					print(alph, nstates, i, "basis automaton invalid")
					raise Exception
				if len(result[0].weights) > len(aut.weights):
					print(alph, nstates, i, "result not minimal, result & target:", len(result[0].weights), len(aut.weights))
					raise Exception
				result_name = "Examples/benchmark/Results" + method + version + "".join(alph) + str(nstates) + "_" + str(i) + ".txt"
				result_str = str(total_perf) + "\n" + str(total_time) + "\n" + str(len(result[0].weights)) + "\n" 
				result_str += str(result[1]) + "\n" + str(result[2]) + "\n" + str(result[3]) + "\n" + str(result[4])
				result_str += "\n" + str(float(result[5]))
				with open(result_name, "w") as result_file:
					result_file.write(str(result_str))
				result_aut_name = "Examples/benchmark/Results" + method + version + "".join(alph) + str(nstates) + "_" + str(i) + "A.txt"
				with open(result_aut_name, "w") as result_aut_file:
					result_aut_file.write(str(result[0]))
				with open(progress_name, "w") as progress_file:
					progress_file.write("".join(alph) + " " + str(nstates) + " " + str(i))