from Lecture import Lecture
class Course:
    def __init__(self, model, course_id, teacher, nr_lectures, min_days, nr_students):
        """
        Constructor to initialize a course object.
        
        :param model: The problem model.
        :param course_id: Unique identifier for the course.
        :param teacher: Teacher object associated with this course.
        :param nr_lectures: Number of lectures in the course.
        :param min_days: Minimum number of days over which the lectures should be spread.
        :param nr_students: Number of students taking the course.
        """
        self.model = model
        self.course_id = course_id
        self.teacher = teacher
        self.nr_lectures = nr_lectures
        self.min_days = min_days
        self.nr_students = nr_students
        self.available = [[True for _ in range(self.model.nr_slots_per_day)] for _ in range(self.model.nr_days)]
        self.unavailable_periods = []
        self.lectures = None
        self.curriculas = []

    def init(self):
        """
        Initialize the lectures if not already initialized.
        """
        if self.lectures is not None:
            return
        self.lectures = [Lecture(self, i) for i in range(self.nr_lectures)]

    def get_lecture(self, idx):
        """
        Return the lecture at the given index.
        
        :param idx: The index of the lecture (0 to nr_lectures-1).
        """
        return self.lectures[idx]

    def get_model(self):
        """Return the problem model."""
        return self.model

    def add_curriculum(self, curriculum):
        """Add a course to the curriculum."""
        self.curriculas.append(curriculum)

    def get_id(self):
        """Return the unique identifier of the course."""
        return self.course_id

    def get_teacher(self):
        """Return the teacher associated with this course."""
        return self.teacher

    def get_nr_lectures(self):
        """Return the number of lectures in the course."""
        return self.nr_lectures

    def get_min_days(self):
        """Return the minimal number of days over which the lectures should be spread."""
        return self.min_days

    def get_nr_students(self):
        """Return the number of students taking this course."""
        return self.nr_students

    def is_available(self, day, slot):
        """
        Check if the course can have a lecture on the given day and time slot.
        
        :param day: The day index.
        :param slot: The slot index.
        """
        return self.available[day][slot]

    def add_unavailability(self, day, slot):
        """
        Add an unavailable period for this course.
        
        :param day: The day index.
        :param slot: The slot index.
        """
        self.unavailable_periods.append((day, slot))
        

    def set_available(self, day, slot, av):
        """
        Set whether the course can have a lecture on the given day and time slot.
        
        :param day: The day index.
        :param slot: The slot index.
        :param av: Availability status (True/False).
        """
        self.available[day][slot] = av

    def get_priority(self, day, slot):
        """
        Compute a priority or penalty for scheduling this course at the given day and slot.
        
        :param day: The day index.
        :param slot: The slot index.
        :return: An integer priority score (lower is better).
        """
        priority = 0

        # Penalize unavailable slots heavily
        if not self.is_available(day, slot):
            return 100  # High penalty for unavailable slots
        """
        # Example: Penalize early or late slots (if preferences exist)
        if slot == 0:  # First slot in the day
            priority += 10
        elif slot == self.model.nr_slots_per_day - 1:  # Last slot in the day
            priority += 10

        # Example: Penalize for overused slots in the teacher's schedule
        teacher = self.get_teacher()
        if teacher and not teacher.is_available(day, slot):
            priority += 50
        """
        # Add any custom logic for curriculum conflicts or other factors
        for curriculum in self.get_curriculas():
            for course in curriculum.get_courses():
                if course != self and not course.is_available(day, slot):
                    priority += 5

        return priority


    def __eq__(self, other):
        """Check if two courses are equal based on their ID."""
        if not isinstance(other, Course):
            return False
        return self.get_id() == other.get_id()

    def __hash__(self):
        """Return the hash code based on the course ID."""
        return hash(self.get_id())

    def __str__(self):
        """String representation of the course."""
        return f"{self.get_id()} {self.get_teacher().get_id()} {self.get_nr_lectures()} {self.get_min_days()} {self.get_nr_students()}"

    def get_min_days_penalty(self):
        """
        Compute the minimal days penalty. The lectures of each course must be spread into a minimum number of days. 
        Each day below the minimum counts as 5 points of penalty.
        """
        days = 0
        nr_days = 0
        for lecture in self.lectures:
            if lecture.get_assignment() is None:
                nr_days += 1
            else:
                day = 1 << lecture.get_assignment().get_day()
                if (days & day) == 0:
                    nr_days += 1
                days |= day
        return 5 * max(0, self.get_min_days() - nr_days)

    def get_room_penalty(self):
        """
        Compute room penalty. All lectures of a course should be given in the same room.
        Each distinct room used for the lectures of a course, but the first, counts as 1 point of penalty.
        """
        return max(0, len(self.get_rooms()) - 1)

    def get_rooms(self):
        """
        Compute all rooms into which lectures of this course are assigned.
        """
        rooms = set()
        for lecture in self.lectures:
            placement = lecture.get_assignment()
            if placement:
                rooms.add(placement.get_room())
        return rooms

    def get_curriculas(self):
        """Return the curriculas associated with this course."""
        return self.curriculas
