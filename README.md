# clara

Adding features to the tool CLARA by https://github.com/iradicek/clara

Please refer to the PDF Clara__User_Manual for detailed instructions.

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
