class Teacher:
    def __init__(self, model, teacher_id):
        """
        Constructor to initialize a teacher object.
        
        :param model: The problem model.
        :param teacher_id: The unique identifier for the teacher.
        """
        self.model = model
        self.teacher_id = teacher_id
        self.courses = []
        self.unavailability = []
        self.constraint = self.TeacherConstraint(model)  # Pass model to TeacherConstraint
        model.add_constraint(self.constraint)

    def add_course(self, course):
        """Add a course to the teacher's course list."""
        self.courses.append(course)

    def get_model(self):
        """Return the problem model."""
        return self.model

    def add_unavailability(self, day, slot):
        """
        Add a period when the teacher is unavailable.
        """
        self.unavailability.append((day, slot))
    
    def get_unavailability(self):
        return self.unavailability

    def is_available(self, day, slot):
        """
        Check if the teacher is available at the given day and slot.
        """
        return (day, slot) not in self.unavailability
    
    def get_id(self):
        """Return the unique identifier of the teacher."""
        return self.teacher_id

    def __eq__(self, other):
        """Compare two teachers for equality."""
        if not isinstance(other, Teacher):
            return False
        return self.get_id() == other.get_id()

    def __hash__(self):
        """Return the hash code for the teacher."""
        return hash(self.get_id())

    def __str__(self):
        """String representation of the teacher."""
        return self.get_id()

    def get_constraint(self):
        """Return the teacher's constraint."""
        return self.constraint

    class TeacherConstraint:
        def __init__(self, model):
            """Constructor for TeacherConstraint class."""
            super().__init__()  # Call the constructor of the parent (Constraint) class
            self.model = model  # Initialize model for TeacherConstraint
            self.placement = [[None for _ in range(self.model.nr_slots_per_day)] for _ in range(self.model.nr_days)]
            self.assigned_variables = None
            self.variables = []  # This will hold the lectures assigned to the teacher

        def add_variable(self, lecture):
            """Add a lecture (variable) to the teacher's constraint."""
            self.variables.append(lecture)

        def get_placement(self, day, slot):
            """Return the placement of a lecture that is taught by this teacher at the given day and time."""
            return self.placement[day][slot]

        def compute_conflicts(self, placement, conflicts):
            """Compute conflicts, i.e., another lecture that is taught by this teacher and placed at the same time."""
            if self.placement[placement.get_day()][placement.get_slot()] is not None and \
                    self.placement[placement.get_day()][placement.get_slot()].variable() != placement.variable():
                conflicts.add(self.placement[placement.get_day()][placement.get_slot()])

        def in_conflict(self, placement):
            """Check for conflict, i.e., another lecture that is taught by this teacher at the same day and time."""
            return self.placement[placement.get_day()][placement.get_slot()] is not None and \
                   self.placement[placement.get_day()][placement.get_slot()].variable() != placement.variable()

        def is_consistent(self, placement1, placement2):
            """Two lectures taught by the same teacher are consistent only if placed on different days or slots."""
            return placement1.get_day() != placement2.get_day() or placement1.get_slot() != placement2.get_slot()

        def assigned(self, iteration, placement):
            """Assign a placement to this teacher."""
            if self.placement[placement.get_day()][placement.get_slot()] is not None:
                conflicts = {self.placement[placement.get_day()][placement.get_slot()]}
                self.placement[placement.get_day()][placement.get_slot()].variable().unassign(iteration)
                self.placement[placement.get_day()][placement.get_slot()] = placement
                if self.assigned_variables is not None:
                    for listener in self.assigned_variables:
                        listener.constraint_after_assigned(iteration, self, placement, conflicts)
            else:
                self.placement[placement.get_day()][placement.get_slot()] = placement

        def unassigned(self, iteration, placement):
            """Unassign a placement from this teacher."""
            self.placement[placement.get_day()][placement.get_slot()] = None

        def __str__(self):
            """String representation of the teacher constraint."""
            return str(Teacher.this)

        def __hash__(self):
            """Return the hash code of the teacher constraint."""
            return hash(Teacher.this)
