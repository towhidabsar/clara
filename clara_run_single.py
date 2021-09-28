import subprocess
import os
from xlwt import Workbook
import time


rep_correct = 'All Repaired'
rep_incorrect = 'Old Repairs were incomplete, apply these repairs too:'
rep_error = 'There are issues with the suggested repairs. The new program may not run.'
rep_not_needed = 'No repair!'
rep_partial = 'Partial Repaired'

test_available = 'Test Case Available'
test_not_available = 'Test Case Not Available'

path = '/home/mc1927/codeForcesTests/NSF_WebScraper/Output/ScrapeData/'
problem_name = '1551A'
start = time.time()
# if ((problem_name + '.xls') in os.listdir('batch_tests/')):
#     continue
print(problem_name)
wb = Workbook()

sheet1 = wb.add_sheet('test 1')
sheet1.write(0,0, 'Correct File')
sheet1.write(0,1, 'Incorrect File')
sheet1.write(0,2, 'Repair')
sheet1.write(0,3, 'Structure Mismatch')
sheet1.write(0,4, 'Repair Correct')
sheet1.write(0,5, 'Match')
sheet1.write(0,6, 'Parse Error')
sheet1.write(0,7, 'Test Available')

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
        # testcase = incorrect_path+file_code+'_test_cases.txt'
        testcase = path + problem_name + '/testcases/'

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
        
        if (test_available in output):
            sheet1.write(i, 7, 'Yes')
        elif (test_not_available in output):
            sheet1.write(i, 7, 'No')

        if (exitcode == 0):
            sheet1.write(i,2, 'Yes')
            sheet1.write(i, 3, 'False')
            sheet1.write(i, 6, 'No')
            if (rep_correct in output):
                sheet1.write(i, 4,'Yes')
            elif (rep_partial in output):
                sheet1.write(i, 4, 'Partial')
            elif (rep_not_needed in output):
                sheet1.write(i, 4, 'Not Needed')
            elif (rep_error in output):
                sheet1.write(i, 4, 'Error')
            elif (rep_incorrect in output):
                sheet1.write(i, 4, 'No')
        else:
            # print("ifile ", ifile, " cfile ", cfile, " err ", err)
            if ('StructMismatch' in err):
                sheet1.write(i, 3, 'True')
            else:
                sheet1.write(i, 3, 'False')
            sheet1.write( i, 2, 'No')
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
        # print("exitcode repair",exitcode)
        # print("exitcode match ", exitcode_match)
        # if (iruns == 2):
            # break
    runs += 1
    # if (runs == 2):
    #     break

wb.save('batch_tests/' + problem_name + '.xls')
end = time.time()
hours, rem = divmod(end-start, 3600)
minutes, seconds = divmod(rem, 60)
print("{:0>2}:{:0>2}:{:05.2f}".format(int(hours),int(minutes),seconds))