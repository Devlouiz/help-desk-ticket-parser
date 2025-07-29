import csv

with open('C:/Users/Ddr3/Documents/CyberSecurity/help desk ticket parser and reporter/intercom_report_csv.csv',
          'r') as file:
    read = csv.DictReader(file)

    for row in read:
        print(row['Subject'])
