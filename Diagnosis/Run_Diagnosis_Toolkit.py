'''
#run Diagnosis toolk
#has different levels of diagnosis
python3 diagnostic_toolkit.py --quick
python3 diagnostic_toolkit.py --report
python3 diagnostic_toolkit.py --service pattern --report
python3 diagnostic_toolkit.py --service pattern --report && echo "Report saved to /content/diagnostic_reports/"

These 4 options require it to have the following format (expample shows the full i.e no parameter like --quick):

!cd /conten./Diagnosis && python3 diagnostic_toolkit.py

'''

!cd /conten./Diagnosis && python3 diagnostic_toolkit.py
