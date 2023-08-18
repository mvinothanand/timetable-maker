import sys
import json
from colorama import Fore, init
from tabulate import tabulate

from common import (
  csvToList,
  dump_list_to_file
)

from config import (
  course_details_file,
  staff_availability_file,
  class_schedule_file,
  week_days,
  staff_details_json,
  class_schedule_json,
  course_schedule_json
)

init(autoreset=True)


# Enrich staff availability details
def enrich_staff_info(staff_info):
  for staff in staff_info:
    staff["availability_bitmap"] = []
    staff["courses"] = []
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
  #print(f"get_slot: rem_hours: {rem_hours} block_size: {block_size} day_bmap: {day_avail_bmap}")
  slot_size = min(rem_hours, block_size)
  reqd_bmap = slot_size * "0"
  matched_slot = day_avail_bmap.find(reqd_bmap)
  #print(f"get_slot: matched_slot = {matched_slot}")
  #return {"hour": matched_slot + 1, "slot_size": slot_size} if matched_slot >= 0 else None
  return list(range(matched_slot + 1, matched_slot + slot_size + 1)) if matched_slot >=0 else None


def find_slots(course, staff_avail_merged_bmap):
  #initializing required variables
  rem_hours = int(course["weekly_hours"])
  max_block_size = int(course["max_block_size"])
  min_block_size = int(course["min_block_size"])
  matched_slots = {"Mon": [], "Tue": [], "Wed": [], "Thu": [], "Fri": []}

  iteration_count = 1
  while(rem_hours > 0 and iteration_count <= int(course["weekly_hours"]) ):
    print(f"Iteration {iteration_count}: Avilability Bitmap: {staff_avail_merged_bmap}")
    iteration_count += 1
    for i, day in zip(range(5), week_days):
      if rem_hours <= 0:
        break
      curr_bmap = staff_avail_merged_bmap[i]
      # first check for max block size else for min_block_size
      matched_slot = get_slot(rem_hours, max_block_size,curr_bmap)
      #print(f"Matched Slot: {matched_slot}")
      if (not matched_slot) and min_block_size < max_block_size:
        matched_slot = get_slot(rem_hours, min_block_size,curr_bmap)

      if matched_slot:
        #matched_slots[day].append(matched_slot)
        matched_slots[day] = matched_slots[day] + matched_slot
        rem_hours = rem_hours - len(matched_slot)

      updated_staff_availability = ""
      for j in range(1,9):
        if j in matched_slots[day]:
          updated_staff_availability = updated_staff_availability + "1"
        else:
          updated_staff_availability = updated_staff_availability + staff_avail_merged_bmap[i][j-1]

      staff_avail_merged_bmap[i] = updated_staff_availability
  
  if rem_hours == 0:
    print(f"Successfully mapped.")
  else:
    print(f"Unable to find slots for {rem_hours}")

  print(f"Final Avilability Bitmap: {staff_avail_merged_bmap}")
  return matched_slots


def update_staff_availability(course_staff, staff_details_all, mapped_slots, course_name, class_name):
  staffs = [staff["name"] for staff in course_staff]
  for staff in staff_details_all:
    if staff["name"] in staffs:
      staff["courses"].append(f"{class_name} {course_name}") 
      for i, day in zip(range(5), week_days):
        #print(f"{Fore.LIGHTBLUE_EX}Initial Availability of {staff['name']}: {day} :{staff[day]}")
        updated_day_bitmap = ""
        for slot in mapped_slots[day]:
          staff[day][slot] = class_name + " " + course_name
        for slot in range(1,9):
          updated_day_bitmap = str(updated_day_bitmap) + str("0" if staff[day][slot] == "0" else "1")
        staff["availability_bitmap"][i] = updated_day_bitmap
        #print(f"{Fore.LIGHTRED_EX}Updated Availability of {staff['name']}: {day} :{staff[day]}")


def update_class_schedule(class_schedule, class_name, mapped_slots, course_name):
  for class_ in class_schedule:
    if class_["name"] == class_name:
      for i, day in zip(range(5), week_days):
        updated_day_bitmap = ""
        for slot in mapped_slots[day]:
          class_[day][slot] = course_name
        for slot in range(1,9):
          updated_day_bitmap = str(updated_day_bitmap + str("0" if class_[day][slot] == "0" else "1"))
        class_["schedule_bmap"][i] = updated_day_bitmap 


def get_class_schedule(class_name, staff_availability, course_details_all, class_schedule_all):
  # Filter the courses specific for the input class
  class_course_details = list(filter(lambda course: course["class"] == class_name, course_details_all))
  #print(course_details)

  class_schedule = list(filter(lambda class_: class_["name"] == class_name, class_schedule_all))
  if len(class_schedule) > 1:
    sys.exit(Fore.RED + "More than one entry found for the class {class_name}")
  if len(class_schedule) == 0:
    sys.exit(Fore.RED + "Class Schedule not found for {class_name}")

  course_slot_mapping = []
  for course in sorted(class_course_details,key = lambda course: course["max_block_size"], reverse = True):
    course_name = course["name"]
    print(f"""
    {Fore.CYAN}{course['class']} {course_name} {course['staff']} week hours: {course['weekly_hours']} 
    min/max: {course['min_block_size']}/{course['max_block_size']} session pref: {course['session_pref']} max/day: {course['max_hrs_day']}""")
  
    # For the staff mapped for the course, get a merged availability bitmap for the week
    staff_records = list(filter(lambda staff: staff['name'] in course['staff'].split("|"),staff_availability))
    staff_avail_merged_bmap = get_merged_bm_week(staff_records)
    #print(f"{Fore.GREEN}Merged Staff Availability bmap for the week : {staff_avail_merged_bmap}")
  
    # Get a merged bmap for the staff availability and class schedule
    staff_class_merged_bmap = get_staff_class_merged_bmap_week(staff_avail_merged_bmap, class_schedule[0]["schedule_bmap"])
    #print(f"Merged availability of staff and class: {staff_class_merged_bmap}")

    mapped_slots = find_slots(course, staff_class_merged_bmap)
    #print(mapped_slots)
    
    # update staff availability
    update_staff_availability(staff_records, staff_availability, mapped_slots, course_name, class_name)
    
    # update class schedule
    update_class_schedule(class_schedule_all, class_name, mapped_slots, course_name)  
    #print(f"Updated class schedule: {class_schedule_curr}")
    
    enriched_course_info = {
      "allotted_slots": mapped_slots, 
      "faculty": [staff["name"] for staff in staff_records],
    }
    enriched_course_info.update(course)
    course_slot_mapping.append(enriched_course_info)
  
  return course_slot_mapping


# Print class schedule
# If schedule is to be printed for more than one class, provide the names as list
def pretty_print_class_schedule(class_schedule, classes):
  for class_ in classes:
    print(class_)
    schedule_table = []
    schedule_table.append(["Day", "1", "2", "3", "4", "5", "6", "7", "8"])
    schedule = list(filter(lambda item: item["name"] == class_.strip(), class_schedule))[0]
    for day in week_days:
      row = [day]
      for i in range(1,9):
        row.append(schedule[day][i])
      schedule_table.append(row)
    print(f"Schedule for {class_}: ")
    print(tabulate(schedule_table, headers="firstrow", tablefmt="grid"))


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

  # Get the staff availability
  staff_availability_init = csvToList(staff_availability_file)
  #print(staff_availability)
  # Create a copy of staff availability - this will be updated as the program
  staff_availability_curr = staff_availability_init.copy()

  # Get the class schedule
  class_schedule_init = csvToList(class_schedule_file)
  # Create a working copy of the class schedule
  class_schedule_curr = class_schedule_init.copy()

  # Parse the daily availability and enrich the staff_availability dictionary
  print(Fore.CYAN + "\nStaff availability before allocation: ")
  enrich_staff_info(staff_availability_curr)

  # PArse the class schedule and enrich it
  print(Fore.CYAN + "\nClass Schedule before allocation: ")
  enrich_class_schedule_info(class_schedule_curr)

  # Get schedule for a class
  course_slot_mapping = get_class_schedule(sem, staff_availability_curr, course_details_all, class_schedule_curr)

  #print(f"{Fore.CYAN}Updated class schedule: {class_schedule_curr}")
  dump_list_to_file(class_schedule_curr, class_schedule_json)
  #print(Fore.CYAN + "Updated Staff Availability:")
  #for staff in staff_availability_curr:
  #  print(f"{staff['name']}: {staff['availability_bitmap']}")
  dump_list_to_file(staff_availability_curr, staff_details_json)
  #print(f"{Fore.CYAN}Course Allocation:\n{course_slot_mapping}")
  dump_list_to_file(course_slot_mapping, course_schedule_json)

  pretty_print_class_schedule(class_schedule_curr, ["SEM-II"])

if __name__ == "__main__":
  main()
  #class,name,staff,weekly_hours,min_block_size,max_block_size,session_pref,max_hrs_day
  # print(find_slots(
  #   {
  #     "class": "sem-II",
  #     "name": "subject",
  #     "staff": "staff-1|staff-5",
  #     "weekly_hours": 5,
  #     "min_block_size": 1,
  #     "max_block_size": 1,
  #     "session_pref": "FN",
  #     "max_hrs_day": 2
  #   }, 
  #   ['11111100', '11111111', '11111111', '00000000', '00000000']
  #   )
  # )