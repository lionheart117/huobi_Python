import os
import sys
a=os.system("nohup python3 -u /home/quant/project/huobi_Python/tests/trace_profit.py " + sys.argv[1] + " " + sys.argv[2] + " " + sys.argv[3] + " " + sys.argv[4] + " " + sys.argv[5] + " " + sys.argv[6] + " " + sys.argv[7] + " >log`date +%Y%m%d%H%M%S` 2>&1 &")
print(a)