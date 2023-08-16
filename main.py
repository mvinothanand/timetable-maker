import sys
from colorama import Fore, init

from common import (
  csvToList,
)

from config import (
  course_details_file,
  staff_availability_file,
  class_schedule_file,
  week_days
)

init(autoreset=True)


# Enrich staff availability details
def enrich_staff_info(staff_info):
  for staff in staff_info:
    staff["availability_bitmap"] = []
    for day in week_days:
      #print(f"{staff['name']} availability on {day}: ")
      availability_string = staff[day]  
      availability_dict = {hour:availability for (hour,availability) in zip(range(1,9), staff[day].split("*"))}
      #print(day_availability)
      staff[day] = availability_dict
      availability_bitmap = get_availablity_bitmap(availability_string,"*")
      #print(availability_bitmap)
      staff["availability_bitmap"].append(availability_bitmap)
    #print("\n")
    print(f"{staff['name']}: {staff['availability_bitmap']}")


def enrich_class_schedule_info(class_schedule):
  for class_ in class_schedule:
    class_["schedule_bmap"] = []
    for day in week_days:
      schedule_string = class_[day]
      schedule_dict = {hour:course for (hour, course) in zip(range(1,9), class_[day].split("*"))}
      class_[day] = schedule_dict
      schedule_bmap = get_availablity_bitmap(schedule_string,'*')
      class_["schedule_bmap"].append(schedule_bmap)
    print(f"{class_['name']}: {class_['schedule_bmap']}")



def get_availablity_bitmap(input_string, separator = "*"):
  bitmap = ""
  if len(input_string.strip()) > 0:
    for item in input_string.split(separator):
      if item == "0":
        bitmap += "0"
      else:
        bitmap += "1"
  return bitmap


def get_merged_bm_week(staff_records):
  staff_merged_bm_week = []

  for i,day in zip(range(5), week_days):
    staff_avail_bm_day = []
    for staff in staff_records:
      #print(staff["availability_bitmap"])
      staff_avail_bm_day.append(staff["availability_bitmap"][i])
    #print(f"Day {i + 1} availability bm: {staff_avail_bm_day}")
    staff_day_merged_bm = get_merged_bm_day(staff_avail_bm_day)
    #print(f"{day} merged bm: {staff_day_merged_bm}")
    staff_merged_bm_week.append(staff_day_merged_bm)
  
  return staff_merged_bm_week

def get_merged_bm_day(input_list):
  merged_bm_day = ""
  for i in range(8):
    result = 0
    for item in input_list:
      result += int(item[i])
    #print(f"{i} {result}")
    merged_bm_day = str(merged_bm_day) + str("0" if result == 0 else "1")
    #print(day_merged_bm)
  return merged_bm_day


def get_staff_class_merged_bmap_week(staff_availability_bmap, class_schedule_bmap):
  merged_bmap = []
  #print(staff_availability_bmap)
  for i in range(5):
    merged_day_bmap = ""
    staff_day = staff_availability_bmap[i]
    class_day = class_schedule_bmap[i]
    merged_day_bmap = get_merged_bm_day([staff_day, class_day])
    merged_bmap.append(merged_day_bmap)
  return merged_bmap

def get_slot(rem_hours, block_size, day_avail_bmap):
  slot_size = min(rem_hours, block_size)
  reqd_bmap = slot_size * "0"
  matched_slot = day_avail_bmap.find(reqd_bmap)
  #return {"hour": matched_slot + 1, "slot_size": slot_size} if matched_slot >= 0 else None
  return list(range(matched_slot + 1, slot_size + 1)) if matched_slot >=0 else None


def find_slots(course, staff_avail_merged_bmap):
  #initializing required variables
  rem_hours = int(course["weekly_hours"])
  max_block_size = int(course["max_block_size"])
  min_block_size = int(course["min_block_size"])
  matched_slots = {"Mon": [], "Tue": [], "Wed": [], "Thu": [], "Fri": []}

  for i, day in zip(range(5), week_days):
    if rem_hours <= 0:
      break
    curr_bmap = staff_avail_merged_bmap[i]
    # first check for max block size else for min_block_size
    matched_slot = get_slot(rem_hours, max_block_size,curr_bmap)
    if (not matched_slot) and min_block_size < max_block_size:
      matched_slot = get_slot(rem_hours, min_block_size,curr_bmap)

    if matched_slot:
      #matched_slots[day].append(matched_slot)
      matched_slots[day] = matched_slots[day] + matched_slot
      rem_hours = rem_hours - len(matched_slot)
  
  return matched_slots


def update_staff_availability(course_staff, staff_details_all, mapped_slots, course_name = "1"):
  for staff in course_staff:
    for i, day in zip(range(5), week_days):
      print(f"{Fore.LIGHTBLUE_EX}Initial Availability of {staff['name']}: {day} :{staff[day]}")
      for slot in mapped_slots[day]:
        staff[day][slot] = course_name
      print(f"{Fore.LIGHTRED_EX}Updated Availability of {staff['name']}: {day} :{staff[day]}")


def main():
  # Validate input
  if len(sys.argv) < 2:
    sys.exit(Fore.RED + "Insufficient inputs")
  
  # Read the class for which the timetable is to be prepared
  sem = sys.argv[1]
  print(f"{Fore.CYAN}Timetable to be prepared for {sem}")

  # Get the course details for the class
  course_details_all = csvToList(course_details_file)
  #print(course_details)

  # Filter the courses specific for the input class
  course_details = list(filter(lambda course: course["class"] == sem, course_details_all))
  #print(course_details)

  # Get the staff availability
  staff_availability_init = csvToList(staff_availability_file)
  #print(staff_availability)
  # Create a copy of staff availability - this will be updated as the program
  # adds allocations
  staff_availability_curr = staff_availability_init.copy()

  # Get the class schedule
  class_schedule_init = list(filter(lambda class_: class_["name"] == sem, csvToList(class_schedule_file)))
  if len(class_schedule_init) > 1:
    sys.exit(Fore.RED + "More than one entry found for the class {sem}")
  if len(class_schedule_init) == 0:
    sys.exit(Fore.RED + "Class Schedule not found for {sem}")
  # Create a working copy of the class schedule
  class_schedule_curr = class_schedule_init.copy()

  # Parse the daily availability and enrich the staff_availability dictionary
  print(Fore.CYAN + "\nStaff availability before allocation: ")
  enrich_staff_info(staff_availability_curr)

  # PArse the class schedule and enrich it
  print(Fore.CYAN + "\nClass Schedule before allocation: ")
  enrich_class_schedule_info(class_schedule_curr)

  # Find a slot for each course
  course_slot_mapping = []
  counter = 1
  for course in sorted(course_details,key = lambda course: course["max_block_size"], reverse = True):
    print(f"\n{Fore.CYAN}{course['class']} {course['name']} {course['staff']}")
    
    # For the staff mapped for the course, get a merged availability bitmap for the week
    staff_records = list(filter(lambda staff: staff['name'] in course['staff'].split("|"),staff_availability_curr))
    staff_avail_merged_bmap = get_merged_bm_week(staff_records)
    print(f"{Fore.GREEN}Merged Staff Availability bmap for the week : {staff_avail_merged_bmap}")
    
    # Get a merged bmap for the staff availability and class schedule
    #print(class_schedule_curr[0]["schedule_bmap"])
    staff_class_merged_bmap = get_staff_class_merged_bmap_week(staff_avail_merged_bmap, class_schedule_curr[0]["schedule_bmap"])
    print(f"Merged availability of staff and class: {staff_class_merged_bmap}")

    mapped_slots = find_slots(course, staff_class_merged_bmap)
    print(mapped_slots)
    #course_slot_mapping.add({"course_name": course["name"]})
    # update staff availability
    update_staff_availability(staff_records, staff_availability_curr, mapped_slots, course['name'])
    counter += 1
    if counter > 3:
      break


if __name__ == "__main__":
  main()