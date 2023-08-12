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
  for staff in staff_availability:
    staff["availability_bitmap"] = []
    for day in ["Mon","Tue","Wed", "Thu", "Fri"]:
      #print(f"{staff['name']} availability on {day}: {staff[day]}")
      availability_string = staff[day]
      availability_dict = {hour:availability for (hour,availability) in zip(range(1,9), staff[day].split("*"))}
      #print(day_availability)
      staff[day] = availability_dict
      availability_bitmap = get_availablity_bitmap(availability_string,"*")
      print(availability_bitmap)
      staff["availability_bitmap"].append(availability_bitmap)
    #print("\n")

  print("\nstaff availability before allocation: ")
  print(staff_availability)

  # Find a slot for each course
  # for course in sorted(course_details,key = lambda course: course["min_block_size"], reverse = True):
  #   print(f"{course['class']} {course['name']}")



if __name__ == "__main__":
  main()