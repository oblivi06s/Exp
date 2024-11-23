from Placement import Placement

class Lecture:
    def __init__(self, course, idx):
        """
        Constructor to initialize a lecture object.
        
        :param course: The course to which this lecture belongs.
        :param idx: The index of this lecture within the course.
        """
        self.idx = idx
        self.course = course
        self.model = course.get_model()

        # Register lecture with rooms, teacher, and curricula
        for room in self.course.get_model().get_rooms():
            room.get_constraint().add_variable(self)
        self.course.get_teacher().get_constraint().add_variable(self)
        for curricula in self.course.get_curriculas():
            curricula.get_constraint().add_variable(self)
        
        self.values = self.compute_values()
        #self.model.add_variable(self)

    def get_course(self):
        """Return the course to which this lecture belongs."""
        return self.course

    def compute_values(self):
        """
        Compute the domain for the lecture: Cartesian product of all available days and times,
        and all rooms.
        """
        values = []
        for d in range(self.course.get_model().nr_days):
            for s in range(self.course.get_model().nr_slots_per_day):
                if self.course.is_available(d, s):
                    for room in self.course.get_model().get_rooms():
                        values.append(Placement(self, room, d, s))
        return values

    def get_name(self):
        """Return the name of the lecture: course ID / index."""
        return f"{self.course.get_id()}/{self.idx}"

    def __str__(self):
        """String representation of the lecture."""
        return self.get_name()

    def get_idx(self):
        """Return the index of the lecture within the course."""
        return self.idx

    def __eq__(self, other):
        """Check equality of two lectures based on their course and index."""
        if not isinstance(other, Lecture):
            return False
        return self.idx == other.idx and self.course == other.get_course()

    def __hash__(self):
        """Return the hash code for the lecture."""
        return hash(self.get_name())

    def compare_to(self, other):
        """Compare two lectures. The one with more curricula or smaller domain/constraint ratio is 'harder'."""
        if self.course == other.get_course():
            return self.idx - other.get_idx()

        cmp = len(self.course.get_curriculas()) - len(other.get_course().get_curriculas())
        if cmp != 0:
            return cmp

        cmp = len(self.values()) / len(self.constraints()) - len(other.values()) / len(other.constraints())
        if cmp != 0:
            return cmp

        return 0
    """
    def find_swap(self, another):
        
        Find a swap with another lecture, ensuring that the swap is valid according to various constraints.
        
        :param another: The other lecture to swap with.
        :return: A swap object if valid, otherwise None.
    
        if not isinstance(another, Lecture):
            return None
        if self.get_course() == another.get_course():
            return None

        p1 = self.get_assignment()
        p2 = another.get_assignment()
        if not p1 or not p2:
            return None
        if not self.course.is_available(p2.get_day(), p2.get_slot()):
            return None
        if not another.get_course().is_available(p1.get_day(), p1.get_slot()):
            return None
        if self.get_course().get_teacher() != another.get_course().get_teacher():
            if self.get_course().get_teacher().get_constraint().get_placement(p2.get_day(), p2.get_slot()) is not None:
                return None
            if another.get_course().get_teacher().get_constraint().get_placement(p1.get_day(), p1.get_slot()) is not None:
                return None

        # Check curricula conflicts for the swap
        for curricula in self.course.get_curriculas():
            conflict = curricula.get_constraint().get_placement(p2.get_day(), p2.get_slot())
            if conflict and conflict.variable() != another:
                return None
        for curricula in another.get_course().get_curriculas():
            conflict = curricula.get_constraint().get_placement(p1.get_day(), p1.get_slot())
            if conflict and conflict.variable() != self:
                return None

        # Create placements for swapped lectures
        np1 = Placement(self, p2.get_room(), p2.get_day(), p2.get_slot())
        np2 = Placement(another, p1.get_room(), p1.get_day(), p1.get_slot())
        return LazySwap(np1, np2)
    """

    def assign(self, iteration, value):
        """
        Assign a placement to this lecture and notify appropriate constraints.
        
        :param iteration: The iteration of the assignment.
        :param value: The value (placement) to assign.
        """
        self.model.before_assigned(iteration, value)
        if self.value is not None:
            self.unassign(iteration)
        if value is None:
            return
        self.value = value
        value.get_room().get_constraint().assigned(iteration, value)
        for curricula in self.course.get_curriculas():
            curricula.get_constraint().assigned(iteration, value)
        self.course.get_teacher().get_constraint().assigned(iteration, value)
        value.assigned(iteration)
        self.model.after_assigned(iteration, value)

    def unassign(self, iteration):
        """
        Unassign a placement from this lecture and notify appropriate constraints.
        
        :param iteration: The iteration of the unassignment.
        """
        if self.value is None:
            return
        self.model.before_unassigned(iteration, self.value)
        old_value = self.value
        self.value = None
        old_value.get_room().get_constraint().unassigned(iteration, old_value)
        for curricula in self.course.get_curriculas():
            curricula.get_constraint().unassigned(iteration, old_value)
        self.course.get_teacher().get_constraint().unassigned(iteration, old_value)
        self.model.after_unassigned(iteration, old_value)
