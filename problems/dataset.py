# https://drive.google.com/file/d/1D6UCjkcV3BoWJNNq8BPgz5w4Ciai-Q_x/view?usp=share_link
# https://drive.google.com/uc?id=1D6UCjkcV3BoWJNNq8BPgz5w4Ciai-Q_x
import datasets
from os.path import join as pjoin
from ast import literal_eval
from tqdm import tqdm
import os
import json
import pandas as pd
import gdown
import sys
logger = datasets.logging.get_logger(__name__)

# spack load py-pip/u64kqpe py-torch/tymduoi && pip install -U datasets gdown
class ClaraDataConfig(datasets.BuilderConfig):
  def __init__(self, url, data_dir, **kwargs):
    super(ClaraDataConfig, self).__init__(**kwargs)
    self.URL = url
    self.DATASET_DIRECTORY = data_dir

class ClaraDataBuilder(datasets.GeneratorBasedBuilder):
    '''
    '''
    BUILDER_CONFIG_CLASS = ClaraDataConfig
    DATA_SOURCES = ["CLARA"]
    BUILDER_CONFIGS = [
        ClaraDataConfig(name='ClaraDataset', 
            version=datasets.Version("1.0.0"), 
            description="Parsed output of Clara program repair 1.",
            url="default",
            data_dir="default2")
    ]
    
    test_dummy_data = False
    def _info(self):
      print("HERE YOU GO")
      print(self.config)
      return datasets.DatasetInfo(
          description="Parsed output of Clara program repair 2.",
          features=datasets.Features(
            {
              "Problem": datasets.Value("string"),
              "First Output": datasets.Value("string"),
              "Error Output": datasets.Value("string"),
              "Correct File": datasets.Value("string"),
              "Incorrect File": datasets.Value("string"),
              "Test Available": datasets.Value("string"),
              "Correct Locs": datasets.Value("int32"),
              "Incorrect Locs": datasets.Value("int32"),
              "Old Incorrect Locs": datasets.Value("int32"),
              "Correct Exprs": datasets.Value("int32"),
              "Incorrect Exprs": datasets.Value("int32"),
              "Old Incorrect Exprs": datasets.Value("int32"),
              "Repairs": datasets.Value("int32"),
              "Technique": datasets.Value("int32"),
              "GM Score": datasets.Value("float64"),
              "Locs": datasets.Value("string"),
              "Count": datasets.Value("int64"),
              "Structure Mismatch": datasets.Value("bool"),
              "Repair": datasets.Value("bool"),
              "Repair Correct": datasets.Value("string"),
              "Parse Error": datasets.Value("string"),
              "Cost": datasets.Value("float64"),
              "Second Output": datasets.Value("string"),
              "Match": datasets.Value("string"),
              "Percentage Repaired": datasets.Value("string"),
              "Timeout": datasets.Value("bool")
            }
          ),
          supervised_keys=None
      )
    
    def get_specific_value(self, value_str, formatted_output, default='', s_idx=0, e_idx=-1):
      temp = list(filter(lambda x: value_str in x, formatted_output))
      if len(temp):
        return temp[s_idx].split(value_str)[e_idx].strip()
      else:
        return default

    def parse_raw_clara_output_file(self, output, error, problem_name, cnum, inum, g, rerun=False):
      # All text based captures
      rep_correct = 'All Repaired'
      rep_incorrect = 'Old Repairs were incomplete, apply these repairs too:'
      rep_error = 'There are issues with the suggested repairs. The new program may not run.'
      rep_not_needed = 'No repair!'
      rep_partial = 'Partial Repaired'
      graph_matching_options = [0, 1, 3]
      timeout = 'TIMEOUT'
      loc_add = 'Locs Added:'
      loc_del = 'Locs Deleted:'
      loc_same = 'Locs Same'
      test_available = 'Test Case Available'
      test_not_available = 'Test Case Not Available'
      corr_locs = 'Locs in Correct Program Model'
      exit_code_text = 'Exitcode:'
      corr_exp = 'Exprs in Correct Program Model'
      incorr_locs = 'Locs in Incorrect Program Model'
      incorr_exps = 'Exprs in Incorrect Program Model'
      old_incorr_locs = 'Locs in Old Incorrect Program Model'
      old_incorr_exps = 'Exprs in Old Incorrect Program Model'
      num_Reps = 'Number of Repairs '    

      formatted_output = output.split("\n")
      if len(formatted_output) <= 1:
        return None
      parsed_output = {
        "Problem": None,
        "First Output": None,
        "Error Output": None,
        "Correct File": None,
        "Incorrect File": None,
        "Test Available": None,
        "Correct Locs": None,
        "Incorrect Locs": None,
        "Old Incorrect Locs": None,
        "Correct Exprs": None,
        "Incorrect Exprs": None,
        "Old Incorrect Exprs": None,
        "Repairs": None,
        "Technique": None,
        "GM Score": None,
        "Locs": None,
        "Count": None,
        "Structure Mismatch": None,
        "Repair": None,
        "Repair Correct": None,
        "Parse Error": None,
        "Cost": None,
        "Second Output": None,
        "Match": None,
        "Percentage Repaired": None,
        "Timeout": None
      }

      # Save the raw output for future reference and tuning
      parsed_output["Problem"] = problem_name
      parsed_output["First Output"] = output
      parsed_output["Error Output"] = error

      exitcode = self.get_specific_value(exit_code_text, formatted_output, default=0)
      # if exitcode == '':
      #   # print(f'Formatted: {formatted_output}')
      #   print(f'Raw: {output}')
      exitcode = int(exitcode)
      if ((g == 1 or g == 3) and 'SCORE TOO LESS' in output):
        return None
      parsed_output["Correct File"] = cnum
      parsed_output["Incorrect File"] = inum

      if (test_available in output):
          parsed_output['Test Available'] = 'Yes'
      elif (test_not_available in output):
          parsed_output['Test Available'] = 'No'
        
      
      # Locs + Exp
      parsed_output["Correct Locs"] = self.get_specific_value(corr_locs, formatted_output, default=None)
      parsed_output["Incorrect Locs"] = self.get_specific_value(incorr_locs, formatted_output, default=None)
      parsed_output["Old Incorrect Locs"] = self.get_specific_value(old_incorr_locs, formatted_output, default=None)
      parsed_output["Correct Exprs"] = self.get_specific_value(corr_exp, formatted_output, default=None)
      parsed_output["Incorrect Exprs"] = self.get_specific_value(incorr_exps, formatted_output, default=None)
      parsed_output["Old Incorrect Exprs"] = self.get_specific_value(old_incorr_exps, formatted_output, default=None)
      parsed_output["Repairs"] = self.get_specific_value(num_Reps, formatted_output, default=None)
      parsed_output["Technique"] = g


      if g == 0:
        parsed_output["Locs"] = 0
        parsed_output["Count"] = 0
      else:
        parsed_output["GM Score"] = self.get_specific_value("Score:", formatted_output, default=None)
        if loc_add in output:
          parsed_output["Locs"] = "Add"
          parsed_output["Count"] = self.get_specific_value(loc_add, formatted_output, default=None)
        elif loc_same in output:
          parsed_output["Locs"] = "Same"
          parsed_output["Count"] = 0
        elif loc_del in output:
          parsed_output["Locs"] = "Del"
          parsed_output["Count"] = self.get_specific_value(loc_del, formatted_output, default=None)

      parsed_output["Timeout"] = True if timeout in output else False

      if exitcode == 0:
        parsed_output["Repair"] = True
        parsed_output["Structure Mismatch"] = False
        parsed_output["Parse Error"] = False
        if rep_correct in output:
          parsed_output["Repair Correct"] = "Yes"
        elif rep_partial in output:
          parsed_output["Repair Correct"] = "Partial"
        elif rep_not_needed in output:
          parsed_output["Repair Correct"] = "Not Needed"
        elif rep_error in output:
          parsed_output["Repair Correct"] = "Error"
        elif rep_incorrect in output:
          parsed_output["Repair Correct"] = "No"
        parsed_output["Cost"] = self.get_specific_value('Cost:', formatted_output, default=None)
        parsed_output["Percentage Repaired"] = self.get_specific_value('Percentage of the model modified', formatted_output, default=None)

      else:
        parsed_output["Repair"] = False
        parsed_output["Structure Mismatch"] = True if "StructMismatch" in error else False
        parsed_output["Timeout"] = True if (timeout in error or 'Timeout' in error) else False
        parsed_output["Repair Correct"] = "Error"
        parsed_output["Parse Error"] = True if "Parse Error!" in output else False
        parsed_output["Cost"] = 0

      if rerun:
        # @TODO input the rerun code
        pass
      else:
        parsed_output["Match"] = ""
        parsed_output["Second Output"] = ""
      return parsed_output


    def _generate_examples(self, split):
      '''
      Parse the raw clara output from the files
      '''
      print(f"generating examples from {split}")
      directory = '/home/mac9908/clara/problems/Output'
      with open(pjoin(directory, 'combinations.json'), 'r') as f:
          combinations = json.loads(f.read())
      # if start is not None and end is not None:
      #     combinations = combinations[start:end]
      for c in tqdm(combinations):
          problem_name = c['problem_name']
          cfile = f'{c["correct_file"]}_solution.py'
          cnum = c["correct_num"]
          ifile = f'{c["incorrect_file"]}_solution.py'
          inum = c["incorrect_num"]
          g = c["g"]
          outfolder = pjoin(directory, 'batch_tests_output', problem_name)
          output_file = pjoin(outfolder, f'{inum}_{cnum}_{str(g)}.txt')
          error_file = pjoin(outfolder, f'{inum}_{cnum}_{str(g)}_err.txt')

          if not (os.path.exists(output_file) and os.path.exists(error_file)):
              continue
          output = open(output_file, 'r').read()
          err = open(error_file, 'r').read()
          # print(output)
          # print(err)
          parsed_output = self.parse_raw_clara_output_file(output=output, error=err, problem_name=problem_name, cnum=cnum, inum=inum, g=g)
          # print(parsed_output)
          if parsed_output is not None:
            yield f'{inum}-{cnum}-{str(g)}', parsed_output

    def _split_generators(self, dl_manager):
        return [
            datasets.SplitGenerator(
                name=datasets.Split("DEFAULT"),
                gen_kwargs={"split": "default"},
            )
        ]
      

    def old_generate_examples(self, split):
        # print(split)
        print(f"generating examples from {split}")
        # print(self.data)
        
        for problem in os.listdir(pjoin(self.extracted_files, 'parsed_results')):
          for json_f in os.listdir(pjoin(self.extracted_files, 'parsed_results', problem)):
            data = json.load(open(pjoin(self.extracted_files, 'parsed_results', problem, json_f)))
            for id in data.keys():
              if data[id].get("Correct File", None) is None:
                continue 
              # print(f'{problem}_{json_f}_{id}')
              yield f'{problem}_{json_f}_{id}', {
                "Problem": problem,
                "First Output": data[id]['First Output'],
                "Error Output": data[id]["Error Output"],
                "Correct File": data[id].get("Correct File", id.split("_")[0]),
                "Incorrect File": data[id].get("Incorrect File", json_f.split("_")[0]),
                "Test Available": True if data[id].get("Test Available", False) == "Yes" else False,
                "Correct Locs": data[id].get("Correct Locs", None),
                "Incorrect Locs": data[id].get("Incorrect Locs", None),
                "Old Incorrect Locs": data[id].get("Old Incorrect Locs", None),
                "Correct Exprs": data[id].get("Correct Exprs", None),
                "Incorrect Exprs": data[id].get("Incorrect Exprs", None),
                "Old Incorrect Exprs": data[id].get("Old Incorrect Exprs", None),
                "Repairs": data[id].get("Repairs", None),
                "Technique": data[id]["Technique"],
                "GM Score": data[id].get("GM Score", None),
                "Locs": data[id].get("Locs", None),
                "Count": data[id].get("Count",None),
                "Structure Mismatch": data[id]["Structure Mismatch"],
                "Repair": data[id]["Repair"],
                "Repair Correct": data[id]["Repair Correct"],
                "Parse Error": data[id]["Parse Error"],
                "Cost": data[id]["Cost"],
                "Second Output": data[id]["Second Output"],
                "Match": data[id]["Match"]
              }

if __name__=='__main__':
  home_dir = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
  print(f'The home directory is {home_dir}')
  # num_proc = sys.argv[3] if len(sys.argv) > 3 else None
  print(f'Creating CLARA dataset in the following folder: {home_dir}')
  datasets.utils.logging.set_verbosity_debug()
  dt = datasets.load_dataset(pjoin(home_dir, 'dataset.py'), 
        cache_dir=pjoin(home_dir, '.cache'),
        url='https://drive.google.com/uc?id=1D6UCjkcV3BoWJNNq8BPgz5w4Ciai-Q_x',
        data_dir=home_dir
      )
  print("Dataset created:\n", dt)
  print("Saving dataset")
  dt.save_to_disk(pjoin(home_dir, 'dataset'))