import subprocess
import os
import threading
from xlwt import Workbook
import json
import time
import logging
import sys
from tqdm import tqdm

# GLOBAL
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
path = '/data/ScrapeData/'
corr_locs = 'Locs in Correct Program Model'
exit_code_text = 'Exitcode:'
corr_exp = 'Exprs in Correct Program Model'
incorr_locs = 'Locs in Incorrect Program Model'
incorr_exps = 'Exprs in Incorrect Program Model'
old_incorr_locs = 'Locs in Old Incorrect Program Model'
old_incorr_exps = 'Exprs in Old Incorrect Program Model'
num_Reps = 'Number of Repairs '
# docker run --name=clara_container -v E:\code\Clara_Data\Output:/data -it clara

def remove_unicode(fname):
    """ Run on just one file.
    """
    source = open(fname, 'r', encoding='utf-8')
    dir_name = os.path.dirname(fname)
    pname = os.path.basename(fname).split("_")[0]
    with open(os.path.join(dir_name,f'{pname}_solution.py'), 'w', encoding='utf-8') as mod:
        r = source.read().replace('\u00a0','')
        mod.write(r)
    source.close()


class ClaraResults():
    def __init__(self):
        self.data = {}
        self.row = {
            "Correct File": "", 
            "Incorrect File": "",
            "Repair": "",
            "Structure Mismatch": "",
            "Repair Correct": "",
            "Match": "",
            "Parse Error": "",
            "Test Available": "",
            "Timeout": "",
            "Locs": "",
            "Count": "",
            "Technique": "",
            "Cost": "",
            "GM Score": "",
            "Percentage Repaired": "",
            "Correct Locs": "",
            "Incorrect Locs": "",
            "Old incorrect Locs": "",
            "Correct Exprs": "",
            "Incorrect Exprs": "",
            "Old Incorrect Exprs": "",
            "Repairs": "",
            "First Output": "",
            "Second Output": "",
            "Error Output": ""
        }

    def new(self, index):
        self.data[index] = {}
        return index
    
    def add(self, index, key, data):
        self.data[index][key] = data

    def save(self, file):
        with open(file, "w") as f:
            json.dump(self.data, f)
    


def get_problem_nums(path):
    correct = []
    for c in os.listdir(path):
        if ('solution.txt' in c):
            correct.append(c.split('_')[0])
            remove_unicode(f'{path}{c}')
    return correct

def parse_output(problem, correct, problems, correct_path, incorrect_path, graph_matching_options, testcase):
    outfolder = f'/data/batch_tests_output/{problem}/'
    for ifile in tqdm(problems, desc="incorrect", position=0):
        results = ClaraResults()
        for cfile in tqdm(correct, desc="correct", position=1, leave=False):
            cdired = correct_path + cfile + '_solution.py'
            idired = incorrect_path + ifile + '_solution.py'
            for g in graph_matching_options:
                idx = results.new(f'{cfile}_{str(g)}')
                output = open(f'{outfolder}{ifile}_{cfile}_{str(g)}.txt', 'r').read()
                err = open(f'{outfolder}{ifile}_{cfile}_{str(g)}_err.txt', 'r').read()
                results.add(idx,"First Output", output)
                # err = clara_call.stderr.decode('utf-8')
                results.add(idx,"Error Output", err)
                formatted_output = output.split('\n')
                temp = list(
                    filter(lambda x: exit_code_text in x, formatted_output))
                temp = temp[0].split(exit_code_text)[-1].strip()
                exitcode = temp
                if ((g == 1 or g == 3) and 'SCORE TOO LESS' in output):
                    continue
                results.add(idx,'Correct File', cfile)
                results.add(idx,'Incorrect File', ifile)
                if (test_available in output):
                    results.add(idx,'Test Available', 'Yes')
                elif (test_not_available in output):
                    results.add(idx,'Test Available', 'No')

                # Locs + Exp
                temp = list(
                    filter(lambda x: corr_locs in x, formatted_output))
                if len(temp):
                    temp = temp[0].split(corr_locs)[-1].strip()
                    results.add(idx,"Correct Locs", temp)
                temp = list(
                    filter(lambda x: incorr_locs in x, formatted_output))
                if len(temp):
                    temp = temp[0].split(incorr_locs)[-1].strip()
                    results.add(idx,"Incorrect Locs", temp)
                temp = list(
                    filter(lambda x: old_incorr_locs in x, formatted_output))
                if len(temp):
                    temp = temp[0].split(old_incorr_locs)[-1].strip()
                    results.add(idx,"Old incorrect Locs", temp)
                temp = list(
                    filter(lambda x: corr_exp in x, formatted_output))
                if len(temp):
                    temp = temp[0].split(corr_exp)[-1].strip()
                    results.add(idx,"Correct Exprs", temp)
                temp = list(
                    filter(lambda x: incorr_exps in x, formatted_output))
                if len(temp):
                    temp = temp[0].split(incorr_exps)[-1].strip()
                    results.add(idx, "Incorrect Exprs", temp)
                temp = list(
                    filter(lambda x: old_incorr_exps in x, formatted_output))
                if len(temp):
                    temp = temp[0].split(old_incorr_exps)[-1].strip()
                    results.add(idx,"Old Incorrect Exprs", temp)
                temp = list(
                    filter(lambda x: num_Reps in x, formatted_output))
                if len(temp):
                    temp = temp[0].split(num_Reps)[-1].strip()
                    results.add(idx, "Repairs", temp)

                results.add(idx,"Technique", g)
                if g == 0:
                    results.add(idx,"Locs", 0)
                    results.add(idx,"Count", 0)
                else:
                    temp = list(
                        filter(lambda x: 'Score:' in x, formatted_output))
                    if len(temp):
                        temp = temp[0].split("Score:")[-1].strip()
                        results.add(idx,"GM Score", temp)
                    if loc_add in output:
                        results.add(idx,"Locs", 'Add')
                        temp = list(
                            filter(lambda x: loc_add in x, formatted_output))
                        temp = temp[0].split(loc_add)[-1].strip()
                        results.add(idx,"Count", temp)
                    elif loc_same in output:
                        results.add(idx,"Locs", 'Same')
                    elif loc_del in output:
                        results.add(idx,"Locs", 'Del')
                        temp = list(
                            filter(lambda x: loc_del in x, formatted_output))
                        temp = temp[0].split(loc_del)[-1].strip()
                        results.add(idx,"Count", temp)
                if (timeout in output):
                    results.add(idx,"Timeout", 'Yes')

                if (exitcode == 0):
                    results.add(idx,"Repair", 'Yes')
                    results.add(idx,"Structure Mismatch", 'False')
                    results.add(idx,"Parse Error", 'No')
                    if (rep_correct in output):
                        results.add(idx,"Repair Correct", 'Yes')
                    elif (rep_partial in output):
                        results.add(idx,"Repair Correct", 'Partial')
                    elif (rep_not_needed in output):
                        results.add(idx,"Repair Correct", 'Not Needed')
                    elif (rep_error in output):
                        results.add(idx,"Repair Correct", 'Error')
                    elif (rep_incorrect in output):
                        results.add(idx,"Repair Correct", 'No')
                    temp = list(
                        filter(lambda x: 'Cost:' in x, formatted_output))
                    if len(temp):
                        temp = temp[0].split("Cost:")[-1].strip()
                        results.add(idx,"Cost", temp)
                    temp = list(
                        filter(lambda x: 'Percentage of the model modified' in x, formatted_output))
                    if len(temp):
                        temp = temp[0].split(
                            'Percentage of the model modified')[-1].strip()
                        results.add(idx,"Percentage Repaired", temp)
                else:
                    if ('StructMismatch' in err):
                        results.add(idx,"Structure Mismatch", 'True')
                    else:
                        results.add(idx,"Structure Mismatch", 'False')
                    if (timeout in err or 'Timeout' in err):
                        results.add(idx,"Timeout", 'Yes')
                    results.add(idx,"Repair", 'No')
                    results.add(idx,"Repair Correct", 'Error')
                    if ("Parse Error!" in output):
                        results.add(idx,"Parse Error", 'Yes')
                    else:
                        results.add(idx,"Parse Error", 'No')
                    results.add(idx,"Cost", 0)
                clara_call_match = subprocess.run(['clara match ' + cdired + ' ' + idired + ' --argsfile ' + testcase],
                                                stdout=subprocess.PIPE,
                                                shell=True)
                output_match = clara_call_match.stdout.decode('utf-8')
                exitcode_match = clara_call_match.returncode
                results.add(idx,"Second Output", output_match)
                if (exitcode_match == 0):
                    if ('No match!' in output_match):
                        results.add(idx,"Match", 'No')
                    else:
                        results.add(idx,"Match", 'Yes')
                else:
                    results.add(idx,"Match", 'Error')
    
        incorrect_file_no = ifile.split('_')[0]
        if (not os.path.exists(f'/data/parsed_results/{problem}/')):
            os.makedirs(f'/data/parsed_results/{problem}/')
        results.save(f'/data/parsed_results/{problem}/{incorrect_file_no}_{str(g)}.json')


def batch_run_json(problem, correct, problems, correct_path, incorrect_path, graph_matching_options, testcase):
    for ifile in tqdm(problems, desc="incorrect", position=0):
        # incorrect file
        # ifile = problems[x]
        outfolder = f'/data/batch_tests_output/{problem}/'
        if (not os.path.exists(outfolder)):
            os.makedirs(outfolder)

        for cfile in tqdm(correct, desc="correct", position=1, leave=False):
            cdired = correct_path + cfile + '_solution.py'
            idired = incorrect_path + ifile + '_solution.py'
            # go through each graph matching options
            for g in graph_matching_options:
                if os.path.exists(f'{outfolder}{ifile}_{cfile}_{str(g)}.txt') or os.path.exists(f'{outfolder}{ifile}_{cfile}_{str(g)}_err.txt'):
                    continue
                else:
                    outfile = open(f'{outfolder}{ifile}_{cfile}_{str(g)}.txt', "w")
                    outfile_err = open(f'{outfolder}{ifile}_{cfile}_{str(g)}_err.txt', 'w')
                    if g == 0:
                        clara_call = subprocess.run(['clara repair ' + cdired + ' ' + idired + ' --argsfile ' + testcase + ' --checkAllRep 1 --verbose 1'],
                                                    stdout=outfile, stderr=outfile_err,
                                                    shell=True)
                    else:
                        clara_call = subprocess.run(['clara graph ' + cdired + ' ' + idired + ' --argsfile ' + testcase + ' --checkAllRep 1 --verbose 1 --matchOp ' + str(g)],
                                                    stdout=outfile, stderr=outfile_err,
                                                    shell=True)
                    outfile.close()
                    outfile_err.close()
                    outfile = open(f'{outfolder}{ifile}_{cfile}_{str(g)}.txt', "a")
                    outfile.write(f'\nExitcode: {clara_call.returncode}')
                    outfile.close()
    



def thread_run(lst, thread):
    # logging.info("Thread %s: starting", thread)
    for problem_name in lst:
        if problem_name not in ['ProblemList.txt', 'SolutionLists']:
            # problem_name = '1A'
            testcase = f'/data/ScrapeData/{problem_name}/testcases/'

            correct_path = path + problem_name + '/OK/python.3/'
            incorrect_path = path + problem_name + '/REJECTED/python.3/'
            correct = get_problem_nums(correct_path)
            probs = get_problem_nums(incorrect_path)
            size = len(probs)


            # batch_run_json(problem_name, correct, probs, correct_path, incorrect_path, graph_matching_options, testcase)
            parse_output(problem_name, correct, probs, correct_path, incorrect_path, graph_matching_options, testcase)

def main(lst, thread_num=6):
    threads = list()
    splits = [[] for i in range(thread_num)]
    # Ceiling division
    per_array = -(len(lst)// -thread_num)
    j = 0
    for i, problem_name in enumerate(lst):
        splits[j].append(problem_name)
        if i % per_array == 0 and i > 0:
            j+=1

    start = time.time()
    for i in range(thread_num):
        x = threading.Thread(target=thread_run, args=(splits[i], i))
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


if __name__=='__main__':
    arg = sys.argv[1]
    if os.path.exists(arg):
        if (len(sys.argv) >= 3):
            start = int(sys.argv[2])
            end = int(sys.argv[3])
            main(os.listdir(arg[start:end]))
        else:
            main(os.listdir(arg))
    else:
        main(arg.split(','))