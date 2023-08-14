import sys

from common import (
  csvToList,
)

from config import (
  course_details_file,
  staff_availability_file
)


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

  for i,day in zip(range(5), ["Mon", "Tue", "Wed", "Thu", "Fri"]):
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


def find_slots(course, staff_avail_merged_bmap):
  rem_hours = int(course["weekly_hours"])
  max_block_size = int(course["max_block_size"])
  min_block_size = int(course["min_block_size"])
  matched_slots = {"Mon": [], "Tue": [], "Wed": [], "Thu": [], "Fri": []}
  for i, day in zip(range(5), ["Mon", "Tue", "Wed", "Thu", "Fri"]):
    if rem_hours <= 0:
      break
    # first check if there is a slot for max_block_size
    slot_size = min(rem_hours, max_block_size)
    reqd_bmap = slot_size * "0"
    matched_slot = staff_avail_merged_bmap[i].find(reqd_bmap)
    print(matched_slot)
    if matched_slot >= 0:
      #matched_slots.append({day: [{"hour": matched_slot + 1, "slot_size": slot_size}]})
      matched_slots[day].append({"hour": matched_slot + 1, "slot_size": slot_size})
      rem_hours = rem_hours - slot_size
    else: 
      if max_block_size > min_block_size:
        # Check if there is a slot or min block size
        slot_size = min(rem_hours, min_block_size)
        reqd_bmap = slot_size * "0"
        matched_slot = staff_avail_merged_bmap[i].find(reqd_bmap)
        if matched_slot >= 0:
          matched_slots[day].append({"hour": matched_slot + 1, "slot_size": slot_size})
          rem_hours = rem_hours - slot_size
  return matched_slots


# find a slot for a course
# looks at the staff avaiability
def get_slot(course, staff_availability):
  print(f"finding slot for {course['name']}")
  print([staff['name'] for staff in staff_availability])
  # duration = course['max_block_size']
  # while duration >= course['min_block_size']:
  #   required_bitmap = duration * "0"
  #   day_counter = 1
  #   for day_bm in staff['availability_bitmap']:
  #     if match_slot := day_bm.find(required_bitmap):
  #       return match_slot
  #   duration -= 1


def main():
  # Validate input
  if len(sys.argv) < 2:
    sys.exit("Insufficient inputs")
  
  # Read the class for which the timetable is to be prepared
  sem = sys.argv[1]
  print(f"Timetable to be prepared for {sem}")

  # Get the course details for the class
  course_details_all = csvToList(course_details_file)
  #print(course_details)

  # Filter the courses specific for the input class
  course_details = list(filter(lambda course: course["class"] == sem, course_details_all))
  #print(course_details)

  # Get the staff availability
  staff_availability = csvToList(staff_availability_file)
  #print(staff_availability)

  # Parse the daily availability and enrich the staff_availability dictionary
  print("\nstaff availability before allocation: ")
  for staff in staff_availability:
    staff["availability_bitmap"] = []
    for day in ["Mon","Tue","Wed", "Thu", "Fri"]:
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
 
  #print(staff_availability)

  # Find a slot for each course
  course_slot_mapping = []
  counter = 1
  for course in sorted(course_details,key = lambda course: course["max_block_size"], reverse = True):
    print(f"{course['class']} {course['name']} {course['staff']}")
    staff_records = list(filter(lambda staff: staff['name'] in course['staff'].split("|"),staff_availability))
    staff_curr_avail_bmap = get_merged_bm_week(staff_records)
    print(f"Merged Staff Availability bmap for the week : {staff_curr_avail_bmap}")
    mapped_slots = find_slots(course, staff_curr_avail_bmap)
    print(mapped_slots)
    counter += 1
    if counter > 2:
      break


if __name__ == "__main__":
  main()