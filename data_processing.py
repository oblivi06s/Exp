import pandas as pd
from Course import Course
from Room import Room
from Curricula import Curricula
from Teacher import Teacher

class DataProcessor:
    def __init__(self, file_path):
        self.file_path = file_path

    def load_data(self):
        """
        Load data from the Excel file for the specified instance.
        """
        try:
            self.metadata_df = pd.read_excel(self.file_path, sheet_name='Metadata')
            self.courses_df = pd.read_excel(self.file_path, sheet_name='Courses')
            self.rooms_df = pd.read_excel(self.file_path, sheet_name='Rooms')
            self.curricula_df = pd.read_excel(self.file_path, sheet_name='Curricula')
            self.unavailability_df = pd.read_excel(self.file_path, sheet_name='Unavailability_constraints')
        except Exception as e:
            print(f"Error loading data from {self.file_path}: {e}")
            raise

    def process_courses(self, model):
        courses = {}

        for _, row in self.courses_df.iterrows():
            course_id = row["CourseID"]
            teacher_id = row["Teacher"]
            num_lectures = row["# Lectures"]
            min_working_days = row["MinWorkingDays"]
            num_students = row["# Students"]

            # Retrieve or create the teacher object
            teacher = model.get_teacher(teacher_id)

            # Create the Course object
            course = Course(
                model=model,
                course_id=course_id,
                teacher=teacher,
                nr_lectures=num_lectures,
                min_days=min_working_days,
                nr_students=num_students
            )
            
            # Assign the course to the teacher
            teacher.add_course(course)
            course.init()
            model.courses.append(course)

    def process_rooms(self, model):
        """
        Process and return rooms. Populates the rooms in the model.
        """
        for _, row in self.rooms_df.iterrows():
            room_id = row["RoomID"]
            capacity = row["Capacity"]

            # Create Room object and populate model
            room = Room(model=model, room_id=room_id, size=capacity)
            model.rooms.append(room)

    def process_curricula(self, model):
        """
        Process and return curricula with their associated courses.
        Populates the curricula in the model.
        """
        for _, row in self.curricula_df.iterrows():
            curriculum_id = row["CurriculumID"]
            curriculum = Curricula(curricula_id=curriculum_id, model=model)

            # Add courses to the curriculum and populate model
            for i in range(1, int(row["# Courses"]) + 1):
                course_id = row.get(f"Course_{i}")
                if pd.notna(course_id):
                    course = model.get_course(course_id)
                    if course is not None:
                        curriculum.add_course(course)
                        course.add_curriculum(curriculum)
            model.curriculas.append(curriculum)

    def process_unavailability(self, model):
        """
        Process the unavailability constraints and assign them to the respective teachers.
        """
        for _, row in self.unavailability_df.iterrows():
            course_id = row["CourseID"]
            day = row["Day"]
            slot = row["Period_Per_Day"]

            course = model.get_course(course_id)
            if course:
                teacher = course.teacher
                teacher.add_unavailability(day, slot)
                course.add_unavailability(day, slot)

    def initialize_model(self, model):
        """
        Load and process data from the Excel file, returning structured data objects.
        """
        # Step 1: Load data
        self.load_data()

        # Step 2: Extract metadata values
        num_days = int(self.metadata_df.loc[self.metadata_df['Parameter'] == 'Days', 'Value'].values[0])
        periods_per_day = int(self.metadata_df.loc[self.metadata_df['Parameter'] == 'Periods_per_day', 'Value'].values[0])

        # Step 3: Set the model metadata
        model.set_nr_days(num_days)
        model.set_nr_slots_per_day(periods_per_day)

        # Step 4: Process each sheet and populate the model
        self.process_courses(model)
        self.process_rooms(model)
        self.process_curricula(model)
        self.process_unavailability(model)

        # Step 5: Return processed data as part of the model
        return model
