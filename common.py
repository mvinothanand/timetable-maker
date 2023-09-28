import csv
import json
import os
from colorama import Fore, Back, Style, init

init(autoreset=True)


# generic function to take yes or no type of answers from user
def check_continue(prompt="Do you want to continue (y/n)?: "):
  while True:
    response = input(prompt).strip().lower()
    if response in ["y","n"]:
      return True if response == "y" else False
    else:
      print("Invalid response.")


# generic function to get a user response without any validation
def get_user_response(prompt="Response: "):
  print("\n")
  return input(Fore.CYAN + prompt).strip()


# function that searches for a input string in a given file
# returns the entire matching line. If not found returns None
def get_matched_content(input_file, search_string):
  #print(f"Searching {input_file} for {search_string}...")
  with open (input_file, "r") as file:
    for line in file:
      if search_string.lower() in line.lower():
        #print("Match found")
        return line
  return None


# verifies if the input file has a valid image extension
def check_valid_image_extn(input_file):
  return input_file.strip().split(".")[1] in ["jpeg", "jpg", "png"]


# convert an input comma separated string to dictionary
# works only for the daily movie record type as defined by fieldnames parameter
def map_to_dict(input_csv_string, fieldnames):
  mapped_dict = csv.DictReader([input_csv_string],fieldnames=fieldnames)
  return next(mapped_dict)


# Read an input csv file to a dictionary and return it
def csvToList(input_csv_file):
  data = []
  with open (input_csv_file) as file:
    reader = csv.DictReader(file)
    for row in reader:
      data.append(row)
  return data


# Dump contents of a list to a file as json
def dump_list_to_file(data, target_file):
  with open (target_file, "w") as file:
    file.write(json.dumps(data, indent=2, ensure_ascii=False))


# Join two file contents
# Appends the contents of second file to the first
# Absolute path with file name should be passed
# If the first record is to be skipped, set the skipFirst param to True. Default is True
# If a newline has to be appended first to the target file set the newline parameter to True/False. Default: True
def join_files(file_1, file_2, skipFirst = True, newline = True):
  counter = 1
  with open(file_1, "a") as target_fp:
    if newline:
      target_fp.write("\n")
    with open(file_2,"r") as source_fp:
      for line in source_fp:
        # if skipFirst was True, skip the first record
        if skipFirst and counter == 1:
          counter += 1
          continue
          
        target_fp.write(line)
        counter += 1


# Create a directory if it doesn't exist
def create_dir(full_dir_path):
  if not os.path.exists(full_dir_path):
    os.mkdir(full_dir_path)


# Write a dictionary to csv file
# In Params:
# input_list - input data as a list of dictionaries
# dest_file - target file to which the data is to be writtem
# headers - list of headers
def write_list_to_csv(input_list, dest_file, headers):
  with open(dest_file, "w") as fp:
    writer = csv.DictWriter(fp, headers)
    writer.writeheader()
    writer.writerows(input_list)


def main():
  target_file = "/home/vinoth/git-repositories/tci-data/data/av-reviews/dummy.csv"
  source_file = "/home/vinoth/git-repositories/tci-data/data/av-reviews/20230809.csv"
  join_files(target_file, source_file)


if __name__ == "__main__":
  main()
