class Curricula:
    def __init__(self, model, curricula_id):
        """
        Constructor to initialize a curricula object.
        
        :param model: The problem model.
        :param curricula_id: Unique identifier for the curricula.
        """
        self.model = model
        self.curricula_id = curricula_id
        self.courses = []
        self.constraint = self.CurriculaConstraint(model)
        model.add_constraint(self.constraint)

    def get_model(self):
        """Return the problem model."""
        return self.model

    def get_id(self):
        """Return the unique identifier of the curricula."""
        return self.curricula_id

    def add_course(self, course):
        """Add a course to the curriculum."""
        self.courses.append(course)
        
    def get_courses(self):
        """Return the list of courses associated with this curricula."""
        return self.courses

    def __eq__(self, other):
        """Check if two curricula are equal based on their ID."""
        if not isinstance(other, Curricula):
            return False
        return self.get_id() == other.get_id()

    def __hash__(self):
        """Return the hash code based on the curricula ID."""
        return hash(self.get_id())

    def __str__(self):
        """String representation of the curricula."""
        return f"{self.get_id()} {self.get_courses()}"

    def get_constraint(self):
        """Return the curricula constraint."""
        return self.constraint

    def get_compact_penalty(self):
        """
        Compute the curriculum compactness penalty.
        Lectures belonging to a curriculum should be adjacent to each other.
        For each isolated lecture, we count a penalty of 2 points.
        """
        penalty = 0
        for day in range(self.model.nr_days):
            for slot in range(self.model.nr_slots_per_day):
                placement = self.constraint.placement[day][slot]
                if not placement:
                    continue
                prev = self.prev(placement, None)
                next_ = self.next(placement, None)
                if not next_ and not prev:
                    penalty += 2
        return penalty

    def prev(self, placement, eq_check):
        """Get the previous placement of a lecture."""
        if not placement:
            return None
        prev = None
        if placement.slot > 0:
            prev = self.constraint.placement[placement.day][placement.slot - 1]
        if eq_check and prev and eq_check.variable() == prev.variable():
            return None
        return prev

    def next(self, placement, eq_check):
        """Get the next placement of a lecture."""
        if not placement:
            return None
        next_ = None
        if placement.slot + 1 < self.model.nr_slots_per_day:
            next_ = self.constraint.placement[placement.day][placement.slot + 1]
        if eq_check and next_ and eq_check.variable() == next_.variable():
            return None
        return next_

    def get_compact_penalty_for_placement(self, placement):
        """
        Compute the compact penalty for a given placement.
        A penalty of 2 points is added for isolated lectures, and -4 for a pair of non-adjacent lectures.
        """
        prev = self.prev(placement, placement)
        next_ = self.next(placement, placement)
        if not prev and not next_:
            return 2
        if prev and self.prev(prev, placement) is None:
            if next_ and self.next(next_, placement) is None:
                return -4
            return -2
        if next_ and self.next(next_, placement) is None:
            return -2
        return 0

    class CurriculaConstraint:
        def __init__(self, model):
            """Constructor for the curricula constraint."""
            self.model = model  # Set the model in RoomConstraint
            self.placement = [[None for _ in range(self.model.nr_slots_per_day)] for _ in range(self.model.nr_days)]

        def get_placement(self, day, slot):
            """Return the placement of a lecture for the given day and slot."""
            return self.placement[day][slot]

        def compute_conflicts(self, p, conflicts):
            """Compute conflicts, i.e., if another lecture is placed at the same day and time."""
            if self.placement[p.day][p.slot] and self.placement[p.day][p.slot].variable() != p.variable():
                conflicts.add(self.placement[p.day][p.slot])

        def in_conflict(self, p):
            """Check if a lecture is in conflict by being placed at the same time as another."""
            return self.placement[p.day][p.slot] and self.placement[p.day][p.slot].variable() != p.variable()

        def is_consistent(self, p1, p2):
            """Check if two lectures are consistent (not placed at the same day and slot)."""
            return p1.day != p2.day or p1.slot != p2.slot

        def assigned(self, iteration, p):
            """Update the placement when a lecture is assigned."""
            if self.placement[p.day][p.slot]:
                conflicts = {self.placement[p.day][p.slot]}
                self.placement[p.day][p.slot].variable().unassign(iteration)
                self.placement[p.day][p.slot] = p
                if self.constraint_listeners:
                    for listener in self.constraint_listeners:
                        listener.constraint_after_assigned(iteration, self, p, conflicts)
            else:
                self.placement[p.day][p.slot] = p

        def unassigned(self, iteration, p):
            """Update the placement when a lecture is unassigned."""
            self.placement[p.day][p.slot] = None

        def __str__(self):
            """String representation of the curricula constraint."""
            return str(self)

        def __hash__(self):
            """Return the hash code of the curricula constraint."""
            return hash(self)
