import matplotlib.pyplot as plt

if __name__ == "__main__":
	methods = ["GapHKCBasis", "GapHKCMinimal", "GapHKC"] #["GapRandom", "GapHKC"] #, "GapRandomMinimal"] 
	alph_todo = (['a'], ['a', 'b'], ['a', 'b', 'c'], ['a', 'b', 'c', 'd'])
	data = [[], [], []]
	for mi, method in enumerate(methods):
		for alph in alph_todo:
			for nstates in range(1, 11):
				#runtimes = []
				states = 0
				for i in range(1, 101):
					filename = "Examples/benchmark/Results" + method + "/" + "".join(alph) + str(nstates) + "_" + str(i) + ".txt"
					with open(filename, "r") as file:
						lines = file.read().split("\n")
						states += int(lines[6])
						#states = max(states, float(lines[1]) - float(lines[7]))
						#runtimes.append(float(lines[1]))
						
				#data[mi].append(states)
				#data[mi].append(states)
				print("Method:", method, ", alph:", alph, ", nstates:", nstates, ",average:", states/100)
				data[mi].append(states/100)

	x_lab = ["".join(alph) + " & " + str(n) for alph in alph_todo for n in range(1, 11)]
	#x_lab = [len(alph) + " & " + str(n) for alph in alph_todo for n in range(1, 11)]
	
	bar_width = 0.25
	data_len = len(data[0])
	
	fig, ax = plt.subplots(figsize=(12,10))
	#plt.bar([x - bar_width/2 for x in range(data_len)], data[0], color='#4E878C', width=bar_width, edgecolor='grey', label="Random Counterexamples")
	#plt.bar([x + bar_width/2 for x in range(data_len)], data[1], color='#65B891', width=bar_width, edgecolor='grey', label="HKC")
	#plt.bar([x - bar_width for x in range(data_len)], data[2], color='#B5FFE1', width=bar_width, edgecolor='grey', label="Minimal")
	
	plt.bar([x - bar_width for x in range(data_len)], data[0], color='#B5FFE1', width=bar_width, edgecolor='grey', label="Basis")
	plt.bar(range(data_len), data[1], color='#4E878C', width=bar_width, edgecolor='grey', label="Modified")
	plt.bar([x + bar_width for x in range(data_len)], data[2], color='#65B891', width=bar_width, edgecolor='grey', label="Original")

	
	plt.xlabel('Input alphabet & Number of states', fontweight='bold', fontsize=21)
	plt.ylabel('Average times closed after counterexample', fontweight='bold', fontsize=21)
	plt.xticks([x + bar_width/2 for x in range(data_len)], x_lab)
	
	plt.setp(ax.get_xticklabels(), rotation=45, horizontalalignment='right')
	plt.legend()
	plt.show()