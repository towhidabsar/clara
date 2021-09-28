import xlrd
import os
from xlwt import Workbook

path = "/home/mc1927/clara/batch_tests/"

wb = Workbook()
sheet1 = wb.add_sheet('test 1')
sheet1.write(0,0, 'File')
sheet1.write(0,1, 'Repairs')
sheet1.write(0,2, 'Correct Repairs')
sheet1.write(0,3, 'Structure Mismatchs')
sheet1.write(0,4, 'Parse Errors')
sheet1.write(0,5, 'Incorrect Testcase')
sheet1.write(0,6, 'Incorrect Files')
sheet1.write(0,7, 'Correct Files')
sheet1.write(0,8, 'Total runs')
i = 1
probs = ['1551A.xls', '1560B.xls', '1554A.xls', '276A.xls', '716A.xls', '1467A.xls', '977C.xls']
for probname in probs:
# for probname in os.listdir(path):
    print(probname)

    prob_wb = xlrd.open_workbook(path+probname)
    prob_sheet = prob_wb.sheet_by_index(0)
    reps = 0
    correct_reps = 0
    mismatch = 0
    parse_err = 0
    partial_reps = 0
    runs = 0
    wrongTestCase = set()
    incorrect_files = set()
    correct_files = set()
    for j in range(1,prob_sheet.nrows):
        name = prob_sheet.cell_value(j,1)
        name_c = prob_sheet.cell_value(j,0)
        correct_files.add(name_c)
        incorrect_files.add(name)
        if prob_sheet.cell_value(j, 7) != 'Yes' :
            wrongTestCase.add(name)
            continue
        runs += 1
        if (prob_sheet.cell_value(j, 2) == 'Yes'):
            reps += 1
        if (prob_sheet.cell_value(j, 3) == 'True'):
            mismatch += 1
        if (prob_sheet.cell_value(j, 4) == 'Yes'):
            correct_reps += 1
        if (prob_sheet.cell_value(j, 4) == 'Partial'):
            partial_reps += 1
        if (prob_sheet.cell_value(j, 6) == 'Yes'):
            parse_err += 1

    sheet1.write(i, 0, probname)
    sheet1.write(i, 1, reps)
    sheet1.write(i, 2, correct_reps)
    sheet1.write(i, 3, mismatch)
    sheet1.write(i, 4, parse_err)
    sheet1.write(i, 5, len(wrongTestCase))
    sheet1.write(i, 6, len(incorrect_files))
    sheet1.write(i, 7, len(correct_files))
    sheet1.write(i, 8, runs)
    i += 1

wb.save('summary.xls')