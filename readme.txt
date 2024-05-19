python version - 3.10 or above
Git Repos: https://github.com/mvinothanand/timetable-maker.git

Configurations:
1. Set the configurations in config.py file
     Change only those needed. Else, leave the defaults in the provided sample.
2. Update the course details in <project-folder>/data/course-details.csv
3. Update the staff availability in <project-folder>/data/staff-availability.csv
4. Update the class schedule (fixed slots if any) in <project-folder>/data/class-schedule.csv

Running the scheduler:
1. Go to the <project-folder> path
2. Run the command:
     python3 main.py <class name for which time table is to be genrated>

Output:
1. Post Allocation staff availability will be available in the <project-folder>/output/staff folder.
2. Generated class schedule CSV will be available in <project-folder>/output/class-schedule folder.
