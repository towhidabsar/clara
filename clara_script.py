import subprocess
import os
from xlwt import Workbook
import time
import threading
import logging


rep_correct = 'All Repaired'
rep_incorrect = 'Old Repairs were incomplete, apply these repairs too:'
rep_error = 'There are issues with the suggested repairs. The new program may not run.'
rep_not_needed = 'No repair!'
rep_partial = 'Partial Repaired'

path = '/home/mc1927/codeForcesTests/NSF_WebScraper/Output/ScrapeData/'
probs = os.listdir(path)
size = len(probs)
start = time.time()

def batch_run(i, j, name):
    logging.info("Thread %s: starting", name)
    for x in range(i, j):
        problem_name = probs[x]
        if (problem_name == 'SolutionLists') or (problem_name == 'ProblemList.txt'):
            continue

        print(problem_name)
        wb = Workbook()

        sheet1 = wb.add_sheet('test 1')
        sheet1.write(0,0, 'Correct File')
        sheet1.write(0,1, 'Incorrect File')
        sheet1.write(0,2, 'Repair')
        sheet1.write(0,3, 'Structure Mismatch')
        sheet1.write(0,4, 'Repair Correct')
        sheet1.write(0,7, 'Partial Repair')
        sheet1.write(0,5, 'Match')
        sheet1.write(0,6, 'Parse Error')

        correct_path = path + problem_name + '/OK/python.3/'
        incorrect_path = path + problem_name + '/REJECTED/python.3/'

        runs = 0
        i = 1
        for cfile in os.listdir(correct_path):
            if cfile.endswith("_test_cases.txt"):
                continue
            
            iruns = 0

            for ifile in os.listdir(incorrect_path):
                if ifile.endswith("_test_cases.txt"):
                    continue

                # file_code = ifile.split('_')[0]
                testcase = path + problem_name + '/testcases/'
                # testcase = incorrect_path+file_code+'_test_cases.txt'

                cdired = correct_path + cfile
                idired = incorrect_path + ifile

                clara_call = subprocess.run(['clara repair '+ cdired + ' ' + idired + ' --argsfile '+ testcase + ' --verbose 1'], 
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    shell=True)
                output = clara_call.stdout.decode('utf-8')
                err = clara_call.stderr.decode('utf-8')
                exitcode = clara_call.returncode
                sheet1.write(i,0, cfile)
                sheet1.write(i, 1, ifile)
                if (exitcode == 0):
                    sheet1.write(i,2, 'Yes')
                    sheet1.write(i, 3, 'False')
                    sheet1.write(i, 6, 'No')
                    if (rep_not_needed in output):
                        sheet1.write(i, 4, 'Not Needed')
                    elif (rep_error in output):
                        sheet1.write(i, 4, 'Error')
                    elif (rep_correct in output):
                        sheet1.write(i, 4,'Yes')
                    elif (rep_incorrect in output):
                        sheet1.write(i, 4, 'No')
                    elif (rep_partial in output):
                        sheet1.write(i, 7, 'Yes')
                else:
                    if ('StructMismatch' in err):
                        sheet1.write(i, 3, 'True')
                    else:
                        sheet1.write(i, 3, 'False')
                    sheet1.write( i, 2, 'No')
                    sheet1.write( i, 7, 'Error')
                    sheet1.write(i, 4, 'Error')
                    if ("Parse Error!" in output):
                        sheet1.write(i, 6, 'Yes')
                    else:
                        sheet1.write(i, 6, 'No')

                clara_call_match = subprocess.run(['clara match '+ cdired + ' ' + idired + ' --argsfile ' + testcase ], 
                    stdout=subprocess.PIPE,
                    shell=True)
                output_match = clara_call_match.stdout.decode('utf-8')
                exitcode_match = clara_call_match.returncode

                if (exitcode_match == 0):
                    if ('No match!' in output_match):
                        sheet1.write(i, 5, 'No')
                    else:
                        sheet1.write(i, 5, 'Yes')
                else:
                    sheet1.write(i, 5, 'Error')
                
                i += 1
                iruns += 1
            runs += 1

        wb.save('batch_tests/' + problem_name + '.xls')
    logging.info("Thread %s: ending", name)

threads = list()
indexes = [0, size//4, size//2, 3*size//4, size]
for i in range(4):
    x = threading.Thread(target=batch_run, args=(indexes[i], indexes[i+1], i))
    threads.append(x)
    x.start()

for i, thread in enumerate(threads):
    logging.info("Main    : before joining thread %d.", i)
    thread.join()
    logging.info("Main    : thread %d done", i)

end = time.time()
hours, rem = divmod(end-start, 3600)
minutes, seconds = divmod(rem, 60)
print("{:0>2}:{:0>2}:{:05.2f}".format(int(hours),int(minutes),seconds))