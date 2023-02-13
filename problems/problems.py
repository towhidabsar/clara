import gdown
import zipfile
import os
from os.path import join as pjoin

def load_data(URL, DATASET_DIRECTORY, filename='codeforce_problems.zip'):
    # URL = 'https://drive.google.com/uc?id=1D6UCjkcV3BoWJNNq8BPgz5w4Ciai-Q_x'
    downloaded = os.path.isfile(pjoin(DATASET_DIRECTORY, filename))
    if not downloaded:
        gdown.download(URL, pjoin(DATASET_DIRECTORY, filename), quiet=False)
    # extracted_files = dl_manager.extract(pjoin(DATASET_DIRECTORY, 'parsed_results.zip'))
    with zipfile.ZipFile(pjoin(DATASET_DIRECTORY, filename),"r") as zip_ref:
        zip_ref.extractall(pjoin(DATASET_DIRECTORY))
    # print("Extracted Files", extracted_files)
    # self.extracted_files = extracted_files

url='https://drive.google.com/uc?id=1dqF1_YDqTFTANeGRGZBDUF1JU2uLqHIm'
data_dir='/home/mac9908/clara/problems'

load_data(url, data_dir)