course_details_file = "./data/course-details.csv"
staff_availability_file = "./data/staff-availability.csv"
class_schedule_file = "./data/class-schedule.csv"
week_days = ["Mon", "Tue", "Wed", "Thu", "Fri"]
backup_folder = "./data/backup/"
staff_details_json = "./db/staff_details.json"
class_schedule_json = "./db/class_schedule.json"
course_schedule_json = "./db/course_schedule.json"
fn_hrs=[1,2,3,4]
an_hrs=[5,6,7,8]
scheduling_preferences = {
  "randomize_course_list": False,
  "bigger_blocks_first": True,
  "max_first_hour_alloc": 2,
  "max_first_after_lunch": 2,
  "max_hours_per_staff_per_day": 6
}
# Result files
output_folder = "./output/"