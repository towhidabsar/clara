import datasets
from os.path import join as pjoin
import os
def display(result, outfile='out.txt'):
    with open(outfile, 'a') as f:
        print(result, file=f)
        print('\n', file=f)

clara_data = datasets.load_from_disk('/home/mac9908/clara/problems/dataset')

# display(clara_data)

clara_data['DEFAULT'].to_pandas().describe().to_csv(pjoin("analysis","default.csv"))

clara_data['DEFAULT'].filter(lambda x: x['Technique'] == 0).to_pandas().describe().to_csv(pjoin("analysis","technique_0.csv"))
clara_data['DEFAULT'].filter(lambda x: x['Technique'] == 1).to_pandas().describe().to_csv(pjoin("analysis","technique_1.csv"))
clara_data['DEFAULT'].filter(lambda x: x['Technique'] == 3).to_pandas().describe().to_csv(pjoin("analysis","technique_3.csv"))

clara_data['DEFAULT'].filter(lambda x: x['Technique'] == 0).to_pandas().groupby(['Problem']).describe().to_csv(pjoin("analysis","group_by_problem_technique_0.csv"))
clara_data['DEFAULT'].filter(lambda x: x['Technique'] == 1).to_pandas().groupby(['Problem']).describe().to_csv(pjoin("analysis","group_by_problem_technique_1.csv"))
clara_data['DEFAULT'].filter(lambda x: x['Technique'] == 3).to_pandas().groupby(['Problem']).describe().to_csv(pjoin("analysis","group_by_problem_technique_3.csv"))

# for folder in os.listdir('/home/mac9908/clara/problems/Output/ScrapeData/'):
#     if folder == 'SolutionLists' or folder == 'ProblemList.txt':
#         continue
    
#     num_ok = len(os.listdir(f'/home/mac9908/clara/problems/Output/ScrapeData/{folder}/OK/python.3'))
#     num_reject = len(os.listdir(f'/home/mac9908/clara/problems/Output/ScrapeData/{folder}/REJECTED/python.3'))
#     print(f'{folder}:   OK: {num_ok}   REJECTED: {num_reject}')
