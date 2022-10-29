import subprocess
import os
import threading
from xlwt import Workbook
import time
import logging
import sys
# docker run --name=clara_container -v E:\code\Clara_Data\Output:/data -it clara
# 
# 
def remove_unicode(fname):
    """ Run on just one file.
    """
    source = open(fname)
    dir_name = os.path.dirname(fname)
    pname = os.path.basename(fname).split("_")[0]
    print(pname)
    print(dir_name)
    with open(f'{dir_name}\{pname}_solution.py', "w") as mod:
        r = source.read().replace('\u00a0','')
        mod.write(r)
    source.close()

def get_problem_nums(path):
    correct = []
    for c in os.listdir(path):
        if ('solution.txt' in c):
            correct.append(c.split('_')[0])
            remove_unicode(c)
    return correct

for problem_name in sys.argv[1].split(","):

    rep_correct = 'All Repaired'
    rep_incorrect = 'Old Repairs were incomplete, apply these repairs too:'
    rep_error = 'There are issues with the suggested repairs. The new program may not run.'
    rep_not_needed = 'No repair!'
    rep_partial = 'Partial Repaired'
    timeout = 'TIMEOUT'

    graph_matching_options = [0, 1, 3]
    loc_add = 'Locs Added:'
    loc_del = 'Locs Deleted:'
    loc_same = 'Locs Same'

    test_available = 'Test Case Available'
    test_not_available = 'Test Case Not Available'

    # path = '/Users/towhidabsar/Documents/code/NSFwebscraper/Output/ScrapeData/'
    path = '/data/ScrapeData/'
    # problem_name = '1A'
    testcase = f'/data/{problem_name}/testcases/'
    corr_locs = 'Locs in Correct Program Model'
    corr_exp = 'Exprs in Correct Program Model'
    incorr_locs = 'Locs in Incorrect Program Model'
    incorr_exps = 'Exprs in Incorrect Program Model'
    old_incorr_locs = 'Locs in Old Incorrect Program Model'
    old_incorr_exps = 'Exprs in Old Incorrect Program Model'
    num_Reps = 'Number of Repairs '
    print(problem_name)

    correct = [
        "150875064",
        "144834824",
        "149760373",
        "136939961",
        "150604669",
        "145972490",
        "151337436",
        "140277461",
        "138642477",
        "144316167",
        "152715871",
        "147030676",
        "145345540",
        "137666902",
        "151486163",
        "144894998",
        "140042381",
        "141459535",
        "144895404",
        "143336552",
        "150979280",
        "148331386",
        "151476411",
        "151035792",
        "147987546",
        "148257236",
        "138273002",
        "150979254",
        "140046145",
        "150861729",
        "140360068",
        "148206075",
        "146718749",
        "138988901",
        "151574454",
        "150993704",
        "138719052",
        "143490076",
        "140510255",
        "138642406",
        "153508150",
        "151035791",
        "152715739",
        "150845401",
        "149601223",
        "142142583",
        "147892648",
        "146467345",
        "150210400",
        "150705258"
    ]



    correct_path = path + problem_name + '/OK/python.3/'
    incorrect_path = path + problem_name + '/REJECTED/python.3/'
    correct = get_problem_nums(correct_path)
    probs = get_problem_nums(incorrect_path)
    # ic = '/Users/towhidabsar/Documents/code/NSFwebscraper/Code/977Incorr.txt'
    # correct_path = path + 'correct/'
    # incorrect_path = path + 'incorrect/'
    # with open(ic) as ff:
    #     probs = ff.read().splitlines()
    # probs = os.listdir(incorrect_path)
    size = len(probs)
    start = time.time()


    def batch_run(a, b, name, problem):
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
            sheet1.write(0, 14, 'Percentage Repaired')
            sheet1.write(0, 15, 'Correct Locs')
            sheet1.write(0, 16, 'Incorrect Locs')
            sheet1.write(0, 17, 'Old incorrect Locs')
            sheet1.write(0, 18, 'Correct Exprs')
            sheet1.write(0, 19, 'Incorrect Exprs')
            sheet1.write(0, 20, 'Old Incorrect Exprs')
            sheet1.write(0, 21, 'Repairs')
            
            for cfile in correct:
                cdired = correct_path + cfile + '_solution.py'
                idired = incorrect_path + ifile + '_solution.py'
                print(cfile, ' ', ifile)

                for g in graph_matching_options:
                    if g == 0:
                        clara_call = subprocess.run(['clara repair ' + cdired + ' ' + idired + ' --argsfile ' + testcase + ' --checkAllRep 1 --verbose 1'],
                                                    stdout=subprocess.PIPE,
                                                    stderr=subprocess.PIPE,
                                                    shell=True)
                    else:
                        clara_call = subprocess.run(['clara graph ' + cdired + ' ' + idired + ' --argsfile ' + testcase + ' --checkAllRep 1 --verbose 1 --matchOp ' + str(g)],
                                                    stdout=subprocess.PIPE,
                                                    stderr=subprocess.PIPE,
                                                    shell=True)
                    output = clara_call.stdout.decode('utf-8')
                    print(output)
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

                    # Locs + Exp
                    temp = list(
                        filter(lambda x: corr_locs in x, formatted_output))
                    if len(temp):
                        temp = temp[0].split(corr_locs)[-1].strip()
                        sheet1.write(i, 15, temp)
                    temp = list(
                        filter(lambda x: incorr_locs in x, formatted_output))
                    if len(temp):
                        temp = temp[0].split(incorr_locs)[-1].strip()
                        sheet1.write(i, 16, temp)
                    temp = list(
                        filter(lambda x: old_incorr_locs in x, formatted_output))
                    if len(temp):
                        temp = temp[0].split(old_incorr_locs)[-1].strip()
                        sheet1.write(i, 17, temp)
                    temp = list(
                        filter(lambda x: corr_exp in x, formatted_output))
                    if len(temp):
                        temp = temp[0].split(corr_exp)[-1].strip()
                        sheet1.write(i, 18, temp)
                    temp = list(
                        filter(lambda x: incorr_exps in x, formatted_output))
                    if len(temp):
                        temp = temp[0].split(incorr_exps)[-1].strip()
                        sheet1.write(i, 19, temp)
                    temp = list(
                        filter(lambda x: old_incorr_exps in x, formatted_output))
                    if len(temp):
                        temp = temp[0].split(old_incorr_exps)[-1].strip()
                        sheet1.write(i, 20, temp)
                    temp = list(
                        filter(lambda x: num_Reps in x, formatted_output))
                    if len(temp):
                        temp = temp[0].split(num_Reps)[-1].strip()
                        sheet1.write(i, 21, temp)

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
                            temp = list(
                                filter(lambda x: loc_add in x, formatted_output))
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
                        temp = list(
                            filter(lambda x: 'Percentage of the model modified' in x, formatted_output))
                        if len(temp):
                            temp = temp[0].split(
                                'Percentage of the model modified')[-1].strip()
                            sheet1.write(i, 14, temp)
                    else:
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
            if (not os.path.exists(f'/data/batch_tests/{problem}/')):
                os.makedirs(f'/data/batch_tests/{problem}/')
            wb.save(f'/data/batch_tests/{problem}/' +
                    incorrect_file_no + "_" + str(g) + '.xls')


    threads = list()
    indexes = [0, size//4, size//2, 3*size//4, size]
    for i in range(4):
        x = threading.Thread(target=batch_run, args=(indexes[i], indexes[i+1], i, problem_name))
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
