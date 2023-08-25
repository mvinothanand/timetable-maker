import sys
import json
import random
from colorama import Fore, init, Back, Style
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
  course_schedule_json,
  fn_hrs,
  an_hrs,
  scheduling_preferences
)

init(autoreset=True)


def get_week_day_index(day):
  match day:
    case "Mon":
      return 1
    case "Tue":
      return 2
    case "Wed":
      return 3
    case "Thu":
      return 4
    case "Fri":
      return 5
    case _:
      return None


def get_course_list_scheduling_pref(courses):
  if scheduling_preferences["randomize_course_list"]:
    course_details = courses.copy()
    random.shuffle(course_details)
    return course_details
  else:
    if scheduling_preferences["bigger_blocks_first"]:
      return(list(sorted(courses,key = lambda course: course["max_block_size"], reverse = True)))
    else:
      return(list(sorted(courses,key = lambda course: course["max_block_size"])))
  
  return courses

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


def get_num_of_busy_first_hours(day_avail_bmap):
  # get the number of first hours the staff are already allocated
  fn_first_hours = 0
  an_first_hours = 0
  for bmap in day_avail_bmap:
    if bmap[0] == "1":
      fn_first_hours += 1

  for bmap in day_avail_bmap:
    if bmap[an_hrs[0]] == "1":
      an_first_hours += 1

  return (fn_first_hours, an_first_hours)


def should_skip_first_slot(no_of_first_hours):    
  return no_of_first_hours >= scheduling_preferences["max_first_hour_alloc"]


def should_skip_post_lunch_slot(no_of_post_lunch_hrs, course_type):
  return no_of_post_lunch_hrs >= scheduling_preferences["max_first_after_after_lunch"] and course_type != "lab"


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


def apply_course_mask(input_bmap, already_mapped_slots):
  no_of_slots = len(input_bmap)
  course_mask = ["0" for i in range(no_of_slots)]
  for i in range(no_of_slots):
    if i+1 in already_mapped_slots:
      course_mask[i] = "1"
      if i > 0:
        course_mask[i-1] = "1"
      if i < no_of_slots-1:
        course_mask[i+1] = "1"
    else:
      if course_mask[i] != "1":
        course_mask[i] = "0"
  
  return get_merged_bm_day(["".join(course_mask),input_bmap])


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

# rem_hours: total remaining hours to be allocated
# block_size: size of the slot needed
# day_avail_bmap: day's availability bitmap 
# session_pref: session preference - FN,AN - default: any
# skip_first_slot: if the first slot shouldn't be considered for allocation set it to True
def get_slot(rem_hours, block_size, day_avail_bmap, session_pref = "any", skip_first_slot = False, skip_post_lunch_slot = False):
  #print(f"get_slot: rem_hours: {rem_hours} block_size: {block_size} day_bmap: {day_avail_bmap}")
  fn_start_slot = 1 if skip_first_slot else 0
  an_start_slot = an_hrs[0] + 1 if skip_post_lunch_slot else an_hrs[0]

  slot_size = min(rem_hours, block_size)
  reqd_bmap = slot_size * "0"

  # Find a slot as per session preference
  matched_slot_fn = day_avail_bmap.find(reqd_bmap, fn_start_slot, fn_hrs[-1])
  matched_slot_an = day_avail_bmap.find(reqd_bmap, an_start_slot - 1, an_hrs[-1])

  if session_pref == "FN":
    matched_slot = matched_slot_fn
  elif session_pref == "AN":
    matched_slot = matched_slot_an
  else:
    matched_slot = matched_slot_fn if matched_slot_fn >= 0 else matched_slot_an   

  #print(f"get_slot: matched_slot = {matched_slot}, slot_size: {slot_size}")
  #return {"hour": matched_slot + 1, "slot_size": slot_size} if matched_slot >= 0 else None
  return list(range(matched_slot + 1, matched_slot + slot_size + 1)) if matched_slot >=0 else None


def find_slots(course, staff_class_merged_bmap, fn_first_hours, an_first_hours):
  #initializing required variables
  rem_hours = int(course["weekly_hours"])
  max_block_size = int(course["max_block_size"])
  min_block_size = int(course["min_block_size"])
  session_pref = course["session_pref"]
  max_hrs_day = int(course["max_hrs_day"])
  course_type = course["type"]
  matched_slots = {"Mon": [], "Tue": [], "Wed": [], "Thu": [], "Fri": []}
  
  iteration_count = 1
  while(rem_hours > 0 and iteration_count <= int(course["weekly_hours"]) ):
    #print(f"Iteration {iteration_count}: Avilability Bitmap: {staff_class_merged_bmap}, num_of_first_hour_busy: {fn_first_hours}, num of busy after lunch: {an_first_hours}")
    iteration_count += 1
    week_days_shuffled = week_days.copy()
    random.shuffle(week_days_shuffled)
    for day in week_days_shuffled:
      #print(day, end = " ")
      if rem_hours <= 0:
        break
      i = get_week_day_index(day) - 1
      curr_bmap = apply_course_mask(staff_class_merged_bmap[i], matched_slots[day])
      #print(f"Course masked bmap: {curr_bmap}")
      
      # Set the flag to skip first hour or not
      skip_fn_first_hour = should_skip_first_slot(fn_first_hours)
      skip_an_first_hour = should_skip_post_lunch_slot(an_first_hours, course_type)
      #print(skip_fn_first_hour, skip_an_first_hour)
      
      # first check for max block size else for min_block_size
      matched_slot = get_slot(rem_hours, max_block_size,curr_bmap, session_pref,skip_fn_first_hour , skip_an_first_hour)
      if (not matched_slot) and min_block_size < max_block_size:
        matched_slot = get_slot(rem_hours, min_block_size,curr_bmap, session_pref,skip_fn_first_hour, skip_an_first_hour)

      if matched_slot:
        #print(f"{matched_slot}")
        #matched_slots[day].append(matched_slot)
        matched_slots[day] = matched_slots[day] + matched_slot
        rem_hours = rem_hours - len(matched_slot)

        updated_availability = ""
        for j in range(1,9):
          if j in matched_slots[day]:
            updated_availability = updated_availability + "1"
            if j == 1:
              fn_first_hours += 1
            if j == an_hrs[0]:
              an_first_hours += 1
          else:
            updated_availability = updated_availability + staff_class_merged_bmap[i][j-1]
        
        staff_class_merged_bmap[i] = updated_availability
  
  if rem_hours == 0:
    print(f"{Style.BRIGHT}{Fore.GREEN}Successfully mapped.")
  else:
    print(f"{Fore.RED}{Style.BRIGHT}Unable to find slots for {rem_hours}")

  print(f"Matched Slots: {matched_slots}")
  #print(f"{Fore.CYAN}Final Avilability Bitmap: {staff_class_merged_bmap}")
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

  for course in get_course_list_scheduling_pref(class_course_details):
    course_name = course["name"]
    print(f"\n{Style.BRIGHT}{Fore.CYAN}{course['class']} {course_name} {Fore.WHITE}{course['staff']}", \
      f"{Style.BRIGHT}{Fore.CYAN}week hours: {course['weekly_hours']} {Fore.WHITE}min/max: {course['min_block_size']}/{course['max_block_size']}", \
      f"{Fore.CYAN}session pref: {course['session_pref']} {Fore.WHITE}max/day: {course['max_hrs_day']}")
    #print(print_string)
    #print(f"\n{Style.BRIGHT}{Fore.CYAN}{course['class']} {course_name} {course['staff']} \
    #week hours: {course['weekly_hours']} min/max: {course['min_block_size']}/{course['max_block_size']} session pref: {course['session_pref']} max/day: {course['max_hrs_day']}")
  
    # For the staff mapped for the course, get a merged availability bitmap for the week
    staff_records = list(filter(lambda staff: staff['name'] in course['staff'].split("|"),staff_availability))
    staff_avail_merged_bmap = get_merged_bm_week(staff_records)
    #print(f"{Fore.GREEN}Merged Staff Availability bmap for the week : {staff_avail_merged_bmap}")

    # Get a merged bmap for the staff availability and class schedule
    staff_class_merged_bmap = get_staff_class_merged_bmap_week(staff_avail_merged_bmap, class_schedule[0]["schedule_bmap"])
    #print(f"Merged availability of staff and class: {staff_class_merged_bmap}")

    fn_first_hours, an_first_hours = get_num_of_busy_first_hours(staff_avail_merged_bmap)
    mapped_slots = find_slots(course, staff_class_merged_bmap, fn_first_hours, an_first_hours)
    #print(mapped_slots)
    
    # update staff availability
    update_staff_availability(staff_records, staff_availability, mapped_slots, course_name, class_name)
    
    # update class schedule
    update_class_schedule(class_schedule_all, class_name, mapped_slots, course_name)  
    #print(f"Updated class schedule: {class_schedule_curr}")
    
    enriched_course_info = dict(course)
    enriched_course_info.update({
      "allotted_slots": mapped_slots, 
      "faculty": [staff["name"] for staff in staff_records],
    })
    course_slot_mapping.append(enriched_course_info)
  
  return course_slot_mapping


# Print class schedule
# If schedule is to be printed for more than one class, provide the names as list
def pretty_print_class_schedule(class_schedule, classes):
  for class_ in classes:
    #print(class_)
    schedule_table = []
    schedule_table.append(["Day", "1", "2", "3", "4", "5", "6", "7", "8"])
    schedule = list(filter(lambda item: item["name"] == class_.strip(), class_schedule))[0]
    for day in week_days:
      row = [day]
      for i in range(1,9):
        row.append(schedule[day][i])
      schedule_table.append(row)
    print(f"\nSchedule for {class_}: ")
    print(tabulate(schedule_table, headers="firstrow", tablefmt="grid", maxcolwidths=[8,15,15,15,15,15,15,15,15]))


def main():
  # Validate input
  if len(sys.argv) < 2:
    sys.exit(Fore.RED + "Insufficient inputs")
  
  # Read the class for which the timetable is to be prepared
  sem = sys.argv[1]
  print(f"\n{Style.BRIGHT}{Fore.CYAN}Timetable to be prepared for {sem}")

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

  pretty_print_class_schedule(class_schedule_curr, [sem])

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