# CLARA
## About
Adding features to the tool CLARA by https://github.com/iradicek/clara. 
Please refer to the PDF Clara__User_Manual for detailed instructions for running CLARA.

In this version of CLARA (a datadriven automated repair approach that is open source), we present several modifications to deal with real-world
introductory programs. 
We extend CLARA’s abstract syntax tree processor to handle common introductory programming constructs. Additionally, we propose a flexible alignment algorithm over control flow graphs where we enrich nodes with semantic annotations extracted from programs using operations and calls. Using this alignment, we modify an incorrect program’s control flow graph to match the correct programs to apply CLARA’s original repair process.

## Experimental Evaluation of Improvements Introduced to Clara

### Access To Data
The full dataset for all the raw experiments can be downloaded using one of the following methods:
1. Progammatically:
```
<!-- Utilizes Huggingface dataset library -->
pip install -U datasets

python dataset/dataset.py
```
2. Google Drive:
[Dataset Folder](https://drive.google.com/drive/folders/1Q1sG1yoAppbwSQ5p1EtwtPMJq0M21rI9?usp=drive_link)
- Download either the parsed csv/json files under the csv/json folder which does not contain the raw output for the runs
- Trimmed version of the results are available [here](https://github.com/towhidabsar/clara/tree/master/dataset). 
- Download the entire directory to keep a `Huggingface Dataset` folder with raw text data of all the runs

### Evaluation Results
[Click Here](https://github.com/towhidabsar/clara/blob/master/notebook/Experimental%20Analysis.ipynb)
## Installation Instructions
### Docker
The easiest way to use and try clara is to use the provided `Dockerfile` to have a container with everything set up.

### Instructions - Build from Source
These are the instructions for Ubuntu 20.04:
```
RUN apt update -y

RUN apt upgrade -y

RUN apt install -y lp-solve liblpsolve55-dev python3 python3-pip git

Clone the repository

RUN py_site_package=$(python3 -m site --user-site)

RUN copy contents of clara/libs/lpsolve_python3.4/site-packages/* to where ever the site package is 
$(python3 -m site --user-site)

RUN pip3 install Cython networkx xlwt pandas tqdm

<!-- if you have sudo access do this -->
RUN export LD_LIBRARY_PATH="$LD_LIBRARY_PATH:/usr/lib/lp_solve/"
<!-- if no sudo access do this -->
RUN export LD_LIBRARY_PATH="$LD_LIBRARY_PATH:<path-to-clara>/libs/lp_solve_5.5/lpsolve55/bin/ux64:<path-to-clara>/libs/lp_solve_dev"

RUN export PATH="$PATH:<path-to-clara>/bin"

RUN make in the clara directory
```



### Old Instructions
#### This may not work in a lot of cases but a good reference to have in case the above runs into trouble
Run the following:
apt-get install lp-solve
apt-get install liblpsolve55-dev

Install Python, Cython, networkx

export LD_LIBRARY_PATH=/usr/lib/lp_solve/

1) Download lpsolve source code [lp_solve_5.5.2.0_source.tar.gz](http://sourceforge.net/projects/lpsolve/files/lpsolve/5.5.2.0/lp_solve_5.5.2.0_source.tar.gz/download)

2) Extract the archive and copy extra/Python folder into lp_solve_5.5

3) cd lp_solve_5.5/lpsolve55 and execute following command

        $ sh ccc (on linux)
        $ sh ccc.osx (on Mac)
    Refer to readme.txt under same folder for more information (lp_solve_5.5/lpsolve55/).

3) cd lp_solve_5.5/extra/Python/

4) change lpsolve55 path in extra/Pythpn/setup.py to point to appropriate directory.
    
        LPSOLVE55 = '../../lpsolve55/bin/ux64'  #change path to reflect appropriate path.
> Note: In my case, I used linux 64 bit machine so folder 'bin/ux64/' created under lpsolve55 directory when executed "sh ccc" command from terminal. The folder contains the lpsolve library files. The LPSOLVE55 path in setup.py should point to the newly generated directory which contains the required lpsolve libraries(liblpsolve55.a).

5) Use following command to install lpsolve extension into site-packages.
    
        $python setup.py install --user

6) Run make, in case of error check clara/setup.py and ensure all the libraries are added in include_dirs.

Should be good if not check these two links out:
https://github.com/chandu-atina/lp_solve_python_3x
https://stackoverflow.com/questions/48765299/how-to-install-lpsolve-for-python-3-6
