#!/bin/env python3
def translate(chip):
    print("Starting translation of chip: {}".format(line))
    d0l = []
    d1l = []
    dxorl = []
    for i in range(0, len(chip)-1):
       d0 = int(chip[i])
       d1 = int(chip[i+1])
       d0l.append(d0)
       d1l.append(d1)
       dxorl.append(d0 ^ d1)
    print('d0  {}'.format(d0l))
    print('d1  {}'.format(d1l))
    print('xor {}'.format(dxorl))
    negl = []
    negls = []
    for i in range(0, len(dxorl)):
        o = dxorl[i]
        if i % 2 == 0:
            if dxorl[i] == 0:
                o = 1
            else:
                o = 0;
        negl.append(o)
        negls.append(str(o))
    print('neg {}'.format(negl))

    print('translation result:',end="");
    for x in negl:
        print(x,end="");
    # dirty way to convert bin to int (using string)
    print(' {}'.format(int(''.join(negls),2)))

f = open("symbols.txt")
for line in f:
    translate(line.strip())


