import logging
import os

from Course import Course
from Curricula import Curricula
from Lecture import Lecture
from Room import Room
from Teacher import Teacher


class ProblemModel:
    def __init__(self):
        """
        Constructor to initialize a Model object.
        """
        self.model_name = None
        self.nr_days = 0
        self.nr_slots_per_day = 0
        self.courses = []
        self.rooms = []
        self.curriculas = []
        self.teachers = []

        # Penalties initialized to zero
        self.compact_penalty = 0
        self.room_penalty = 0
        self.min_days_penalty = 0
        self.room_cap_penalty = 0

        # Assignments for variables
        self.assigned_variables = None
        self.unassigned_variables = None
        self.perturb_variables = None

        # Logging setup
        #self.logger = logging.getLogger(CttModel.__name__)

        self.constraints = []  # To store all constraints

    def add_constraint(self, constraint):
        """Add a constraint to the model."""
        self.constraints.append(constraint)

    def get_name(self):
        """Return the name of the model instance."""
        return self.model_name

    def set_name(self, name):
        """Set the name of the model instance."""
        self.model_name = name

    def get_nr_days(self):
        """Return the number of days in the model."""
        return self.nr_days

    def set_nr_days(self, nr_days):
        """Set the number of days."""
        self.nr_days = nr_days

    def get_nr_slots_per_day(self):
        """Return the number of slots per day."""
        return self.nr_slots_per_day

    def set_nr_slots_per_day(self, nr_slots_per_day):
        """Set the number of slots per day."""
        self.nr_slots_per_day = nr_slots_per_day

    def get_courses(self):
        """Return the list of all courses."""
        return self.courses

    def get_course(self, course_id):
        """Return a course by its ID."""
        for course in self.courses:
            if course.get_id() == course_id:
                return course
        return None

    def get_rooms(self):
        """Return the list of all rooms."""
        return self.rooms

    def get_room(self, room_id):
        """Return a room by its ID."""
        for room in self.rooms:
            if room.get_id() == room_id:
                return room
        return None

    def get_curriculas(self):
        """Return the list of all curricula."""
        return self.curriculas

    def get_curricula(self, curricula_id):
        """Return a curricula by its ID."""
        for curricula in self.curriculas:
            if curricula.get_id() == curricula_id:
                return curricula
        return None

    def get_teachers(self):
        """Return the list of all teachers."""
        return self.teachers

    def get_teacher(self, teacher_id):
        """Return a teacher by its ID."""
        for teacher in self.teachers:
            if teacher.get_id() == teacher_id:
                return teacher
        teacher = Teacher(self, teacher_id)
        self.teachers.append(teacher)
        return teacher

    def get_conflict_graph(self):
        """
        Generate a conflict graph for courses.
        A conflict exists between two courses if:
        - They belong to the same curriculum.
        - They are taught by the same teacher.
        :return: List of tuples representing conflicting courses (course1, course2).
        """
        conflict_graph = []

        # Add conflicts for courses in the same curriculum
        for curriculum in self.get_curriculas():
            courses = curriculum.get_courses()
            for i, course1 in enumerate(courses):
                for course2 in courses[i + 1:]:
                    conflict_graph.append((course1, course2))

        # Add conflicts for courses taught by the same teacher
        for teacher in self.get_teachers():
            courses = teacher.courses
            for i, course1 in enumerate(courses):
                for course2 in courses[i + 1:]:
                    conflict_graph.append((course1, course2))

        return conflict_graph

    def get_compact_penalty(self, precise):
        """
        Curriculum compactness penalty.
        Lectures belonging to a curriculum should be adjacent to each other.
        """
        if not precise:
            return self.compact_penalty
        penalty = 0
        for curricula in self.curriculas:
            penalty += curricula.get_compact_penalty()
        return penalty

    def get_room_penalty(self, precise):
        """
        Room stability penalty.
        All lectures of a course should be in the same room.
        """
        if not precise:
            return self.room_penalty
        penalty = 0
        for course in self.courses:
            penalty += course.get_room_penalty()
        return penalty

    def get_min_days_penalty(self, precise):
        """
        Minimum working days penalty.
        The lectures of each course must be spread across a minimum number of days.
        """
        if not precise:
            return self.min_days_penalty
        penalty = 0
        for course in self.courses:
            penalty += course.get_min_days_penalty()
        return penalty

    def get_room_cap_penalty(self, precise):
        """
        Room capacity penalty.
        The number of students must be less than or equal to the room size.
        """
        if not precise:
            return self.room_cap_penalty
        penalty = 0
        for lecture in self.assigned_variables:
            if lecture.get_assignment() is not None:
                placement = lecture.get_assignment()
                penalty += placement.get_room_cap_penalty()
        return penalty

    def get_total_value(self, precise=False):
        """
        Compute the overall solution value.
        """
        return (
            self.get_compact_penalty(precise) +
            self.get_room_cap_penalty(precise) +
            self.get_min_days_penalty(precise) +
            self.get_room_penalty(precise)
        )

    def get_info(self):
        """Return basic solution info, including penalties."""
        info = {
            "RoomCapacity": str(self.get_room_cap_penalty(False)),
            "MinimumWorkingDays": str(self.get_min_days_penalty(False)),
            "CurriculumCompactness": str(self.get_compact_penalty(False)),
            "RoomStability": str(self.get_room_penalty(False))
        }
        return info

    def get_extended_info(self):
        """Return extended solution info with precise computations."""
        info = {
            "RoomCapacity [p]": str(self.get_room_cap_penalty(True)),
            "MinimumWorkingDays [p]": str(self.get_min_days_penalty(True)),
            "CurriculumCompactness [p]": str(self.get_compact_penalty(True)),
            "RoomStability [p]": str(self.get_room_penalty(True))
        }
        return info

    def after_unassigned(self, iteration, placement):
        """Update penalties after unassigning a placement."""
        lecture = placement.variable()
        self.room_penalty -= placement.get_room_penalty()
        self.room_cap_penalty -= placement.get_room_cap_penalty()
        self.min_days_penalty -= placement.get_min_days_penalty()
        for curricula in lecture.get_course().get_curriculas():
            self.compact_penalty -= curricula.get_compact_penalty(placement)

    def before_assigned(self, iteration, placement):
        """Update penalties before assigning a placement."""
        lecture = placement.variable()
        self.min_days_penalty += placement.get_min_days_penalty()
        self.room_penalty += placement.get_room_penalty()
        self.room_cap_penalty += placement.get_room_cap_penalty()
        for curricula in lecture.get_course().get_curriculas():
            self.compact_penalty += curricula.get_compact_penalty(placement)
