
if __name__ == "__main__":
	method = "GapHKC"
	alph_todo = (['a'], ['a', 'b'], ['a', 'b', 'c'], ['a', 'b', 'c', 'd'])
	for alph in alph_todo:
		for nstates in range(1, 11):
			result_states = 0
			max_states = 0
			for i in range(1, 101):
				filename = "Examples/benchmark/Results" + method + "/" + "".join(alph) + str(nstates) + "_" + str(i) + ".txt"
				with open(filename, "r") as file:
					data = file.read().split("\n")
					result_states += int(data[2])
					max_states = max(max_states, int(data[2]))
			print(str(alph) + " " + str(nstates) + " " + str(result_states / 100) + " " + str(max_states))
