class Room:
    def __init__(self, model, room_id, size):
        """
        Constructor to initialize a room object.

        :param model: The problem model.
        :param room_id: The unique identifier for the room.
        :param size: The size (capacity) of the room.
        """
        self.model = model
        self.room_id = room_id
        self.size = size
        self.constraint = self.RoomConstraint(model)
        model.add_constraint(self.constraint)

    def get_model(self):
        """Return the problem model."""
        return self.model

    def get_id(self):
        """Return the unique identifier of the room."""
        return self.room_id

    def get_size(self):
        """Return the size (capacity) of the room."""
        return self.size
    
    def is_eligible(self, course):
        """
        Check if the room is eligible for the given course.
        :param course: Course object to check eligibility for.
        :return: True if eligible, False otherwise.
        """
        # Example condition: room capacity must be greater than or equal to course size
        return course.get_nr_students() <= self.size

    def __eq__(self, other):
        """Compare two rooms for equality."""
        if not isinstance(other, Room):
            return False
        return self.get_id() == other.get_id()

    def __hash__(self):
        """Return the hash code for the room."""
        return hash(self.get_id())

    def __str__(self):
        """String representation of the room."""
        return f"{self.get_id()} {self.get_size()}"

    def get_constraint(self):
        """Return the room's constraint."""
        return self.constraint

    class RoomConstraint:
        def __init__(self, model):
            """Constructor for the RoomConstraint."""
            self.model = model  # Set the model in RoomConstraint
            # Now the model is properly initialized, and we can use it to access nr_days and nr_slots_per_day
            self.placement = [[None for _ in range(self.model.nr_slots_per_day)] for _ in range(self.model.nr_days)]
            self.assigned_variables = None

        def compute_conflicts(self, placement, conflicts):
            """Compute conflicts, i.e., another placement that uses this room at the same time."""
            if placement.get_room() != Room.this:
                return
            if self.placement[placement.get_day()][placement.get_slot()] is not None and \
                    self.placement[placement.get_day()][placement.get_slot()].variable() != placement.variable():
                conflicts.add(self.placement[placement.get_day()][placement.get_slot()])

        def in_conflict(self, placement):
            """Check if there is a conflict, i.e., if another lecture is placed in the same room at the same time."""
            if placement.get_room() != Room.this:
                return False
            return self.placement[placement.get_day()][placement.get_slot()] is not None and \
                   self.placement[placement.get_day()][placement.get_slot()].variable() != placement.variable()

        def is_consistent(self, placement1, placement2):
            """Check if two placements are consistent (i.e., they are not placed at the same day and time)."""
            if placement1.get_room() != Room.this:
                return True
            if placement2.get_room() != Room.this:
                return True
            return placement1.get_day() != placement2.get_day() or placement1.get_slot() != placement2.get_slot()

        def assigned(self, iteration, placement):
            """Assign a placement to this room."""
            if placement.get_room() == Room.this:
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
            """Unassign a placement from this room."""
            if placement.get_room() == Room.this:
                self.placement[placement.get_day()][placement.get_slot()] = None

        def __str__(self):
            """String representation of the room constraint."""
            return str(Room.this)

        def __hash__(self):
            """Return the hash code of the room constraint."""
            return hash(Room.this)

        def get_placement(self, day, slot):
            """Return the placement of a lecture in this room at the given day and time."""
            return self.placement[day][slot]
