import csv


# Read an input csv file to a dictionary and return it
def csvToList(input_csv_file):
  data = []
  with open (input_csv_file) as file:
    reader = csv.DictReader(file)
    for row in reader:
      data.append(row)
  return data


def main():
  ...

if __name__ == "__main__":
  main()