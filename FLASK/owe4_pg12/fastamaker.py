import json
bestand = open('dataset.txt')

header = []
seq = []
for line in bestand:
    line = line.split()
    print(line)
    header.append(line[0].replace('@', '>') + '\n')
    seq.append(line[1] + '\n')
dictionary = dict(zip(header, seq))
print(dictionary)
fo = open('fastaoutput.txt', 'w')
for k, v in dictionary.items():
    fo.write(str(k) + str(v))
fo.close()




