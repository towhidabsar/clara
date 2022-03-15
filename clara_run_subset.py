import subprocess
import os
import threading
from xlwt import Workbook
import time
import logging


rep_correct = 'All Repaired'
rep_incorrect = 'Old Repairs were incomplete, apply these repairs too:'
rep_error = 'There are issues with the suggested repairs. The new program may not run.'
rep_not_needed = 'No repair!'
rep_partial = 'Partial Repaired'
timeout = 'TIMEOUT'

graph_matching_options = [1]
loc_add = 'Locs Added:'
loc_del = 'Locs Deleted:'
loc_same = 'Locs Same'

test_available = 'Test Case Available'
test_not_available = 'Test Case Not Available'

path = '/home/mc1927/codeForcesTests/NSF_WebScraper/Output/ScrapeData/'
problem_name = '1554A'
testcase = '/home/mc1927/codeForcesTests/NSF_WebScraper/Output/ScrapeData/1554A/testcases/'

print(problem_name)

correct = [
"134421801",
"137593443",
"139037081",
"136136048",
"141824639",
"141364911",
"142772825",
"133904059",
"136299250",
"137791508",
"146510580",
"143543133",
"141611511",
"134507857",
"140296382",
"138699322",
"142115909",
"134490571",
"144809421",
"142616589",
"134365073",
"146280589",
"142944908",
"137714968",
"133380987",
"133259378",
"134779401",
"142038218",
"145962497",
"141735863",
"136304768",
"135896521",
"133124953",
"137197832",
"136176581",
"136221644",
"142116020",
"145146319",
"146495296",
"139981511",
"140372751",
"143138890",
"134364994",
"142243406",
"133090666",
"132701466",
"132628055",
"131116158",
"130978389",
"130794595"
]

correct_path = path + problem_name + '/OK/python.3/'
incorrect_path = path + problem_name + '/REJECTED/python.3/'
ic = '/home/mc1927/codeForcesTests/NSF_WebScraper/Code/c.txt'
with open(ic) as ff:
    probs = ff.read().splitlines()
size = len(probs)
start = time.time()


def batch_run(a, b, name):
    logging.info("Thread %s: starting", name)
    for x in range(a, b):
        ifile = probs[x]
        i = 1
        wb = Workbook()

        sheet1 = wb.add_sheet('test 1')
        sheet1.write(0, 0, 'Correct File')
        sheet1.write(0, 1, 'Incorrect File')
        sheet1.write(0, 2, 'Repair')
        sheet1.write(0, 3, 'Structure Mismatch')
        sheet1.write(0, 4, 'Repair Correct')
        sheet1.write(0, 5, 'Match')
        sheet1.write(0, 6, 'Parse Error')
        sheet1.write(0, 7, 'Test Available')
        sheet1.write(0, 8, 'Timeout')
        sheet1.write(0, 9, 'Locs')
        sheet1.write(0, 10, 'Count')
        sheet1.write(0, 11, 'Technique')
        sheet1.write(0, 12, 'Cost')
        sheet1.write(0, 13, 'GM Score')

        # if ifile.endswith("_test_cases.txt"):
        #     continue

        for cfile in correct:
            # if cfile.endswith("_test_cases.txt"):
            #     continue

            # file_code = ifile.split('_')[0]
            # testcase = incorrect_path+file_code+'_test_cases.txt'

            cdired = correct_path + cfile + '_solution.txt'
            idired = incorrect_path + ifile
            print(cfile, ' ', ifile)

            for g in graph_matching_options:
                if g == 0:
                    clara_call = subprocess.run(['clara repair ' + cdired + ' ' + idired + ' --argsfile ' + testcase + ' --c 1 --verbose 1'],
                                                stdout=subprocess.PIPE,
                                                stderr=subprocess.PIPE,
                                                shell=True)
                else:
                    clara_call = subprocess.run(['clara graph ' + cdired + ' ' + idired + ' --argsfile ' + testcase + ' --c 1 --verbose 1 --matchOp ' + str(g)],
                                                stdout=subprocess.PIPE,
                                                stderr=subprocess.PIPE,
                                                shell=True)
                output = clara_call.stdout.decode('utf-8')
                err = clara_call.stderr.decode('utf-8')
                exitcode = clara_call.returncode
                formatted_output = output.split('\n')
                if ((g == 1 or g == 3) and 'SCORE TOO LESS' in output):
                    continue
                sheet1.write(i, 0, cfile)
                sheet1.write(i, 1, ifile)
                if (test_available in output):
                    sheet1.write(i, 7, 'Yes')
                elif (test_not_available in output):
                    sheet1.write(i, 7, 'No')

                sheet1.write(i, 11, g)
                if g == 0:
                    sheet1.write(i, 9, 0)
                    sheet1.write(i, 10, 0)
                else:
                    temp = list(
                    filter(lambda x: 'Score:' in x, formatted_output))
                    if len(temp):
                        temp = temp[0].split("Score:")[-1].strip()
                        sheet1.write(i, 13, temp)
                    if loc_add in output:
                        sheet1.write(i, 9, 'Add')
                        temp = list(filter(lambda x: loc_add in x, formatted_output))
                        temp = temp[0].split(loc_add)[-1].strip()
                        sheet1.write(i, 10, temp)
                    elif loc_same in output:
                        sheet1.write(i, 9, 'Same')
                    elif loc_del in output:
                        sheet1.write(i, 9, 'Del')
                        temp = list(
                            filter(lambda x: loc_del in x, formatted_output))
                        temp = temp[0].split(loc_del)[-1].strip()
                        sheet1.write(i, 10, temp)
                if (timeout in output):
                    sheet1.write(i, 8, 'Yes')

                if (exitcode == 0):
                    sheet1.write(i, 2, 'Yes')
                    sheet1.write(i, 3, 'False')
                    sheet1.write(i, 6, 'No')
                    if (rep_correct in output):
                        sheet1.write(i, 4, 'Yes')
                    elif (rep_partial in output):
                        sheet1.write(i, 4, 'Partial')
                    elif (rep_not_needed in output):
                        sheet1.write(i, 4, 'Not Needed')
                    elif (rep_error in output):
                        sheet1.write(i, 4, 'Error')
                    elif (rep_incorrect in output):
                        sheet1.write(i, 4, 'No')
                    temp = list(
                        filter(lambda x: 'Cost:' in x, formatted_output))
                    if len(temp):
                        temp = temp[0].split("Cost:")[-1].strip()
                        sheet1.write(i, 12, temp)
                else:
                    # print("ifile ", ifile, " cfile ", cfile, " err ", err)
                    if ('StructMismatch' in err):
                        sheet1.write(i, 3, 'True')
                    else:
                        sheet1.write(i, 3, 'False')
                    if (timeout in err or 'Timeout' in err):
                        sheet1.write(i, 8, 'Yes')
                    sheet1.write(i, 2, 'No')
                    sheet1.write(i, 4, 'Error')
                    if ("Parse Error!" in output):
                        sheet1.write(i, 6, 'Yes')
                    else:
                        sheet1.write(i, 6, 'No')
                    sheet1.write(i, 12, 0)
                clara_call_match = subprocess.run(['clara match ' + cdired + ' ' + idired + ' --argsfile ' + testcase],
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

        incorrect_file_no = ifile.split('_')[0]
        wb.save('batch_tests/1554A/' + incorrect_file_no + "_"+ str(g) + '.xls')


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
print("{:0>2}:{:0>2}:{:05.2f}".format(int(hours), int(minutes), seconds))
