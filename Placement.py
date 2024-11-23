class Placement:
    def __init__(self, lecture, room, day, slot):
        """
        Constructor to initialize a placement object.
        
        :param lecture: The lecture being assigned.
        :param room: The room for the lecture.
        :param day: The day for the lecture.
        :param slot: The time slot for the lecture.
        """
        self.lecture = lecture
        self.room = room
        self.day = day
        self.slot = slot
        self.hash_code = hash(f"{lecture.get_course().get_id()} {self.get_room().get_id()} {self.get_day()} {self.get_slot()}")

    def get_room(self):
        """Return the room assigned to this placement."""
        return self.room

    def get_day(self):
        """Return the day assigned to this placement."""
        return self.day

    def get_slot(self):
        """Return the time slot assigned to this placement."""
        return self.slot

    def __str__(self):
        """String representation of the placement."""
        compact_penalty = sum(curricula.get_compact_penalty(self) for curricula in self.lecture.get_course().get_curriculas())
        return f"{self.lecture.get_name()} = {self.get_room().get_id()} {self.get_day()} {self.get_slot()} [{self.get_room_cap_penalty()}+{self.get_min_days_penalty()}+{compact_penalty}+{self.get_room_penalty()}]"

    def get_room_cap_penalty(self):
        """
        Compute room capacity penalty for this placement.
        The number of students must be less than or equal to the room's capacity.
        Each student above the capacity counts as 1 point of penalty.
        """
        return max(0, self.lecture.get_course().get_nr_students() - self.get_room().get_size())

    def get_room_penalty(self):
        """
        Compute room stability penalty for this placement.
        All lectures of a course should be given in the same room.
        Each distinct room used counts as 1 point of penalty after the first room.
        """
        same, different = 0, 0
        for i in range(self.lecture.get_course().get_nr_lectures()):
            if i == self.lecture.get_idx():
                continue
            placement = self.lecture.get_course().get_lecture(i).get_assignment()
            if not placement:
                continue
            if placement.get_room() == self.get_room():
                same += 1
            else:
                different += 1
        return 0 if (different == 0 or same != 0) else 1

    def get_min_days_penalty(self):
        """
        Compute the minimum working days penalty for this placement.
        Lectures must be spread across a minimum number of days.
        Each day below the minimum counts as 5 points of penalty.
        """
        days = 0
        nr_same_days = 0
        same_day = False
        for i in range(self.lecture.get_course().get_nr_lectures()):
            p = self if i == self.lecture.get_idx() else self.lecture.get_course().get_lecture(i).get_assignment()
            if not p:
                continue
            if i != self.lecture.get_idx() and p.get_day() == self.get_day():
                same_day = True
            day = 1 << p.get_day()
            if days & day:
                nr_same_days += 1
            days |= day
        return 5 if same_day and self.lecture.get_course().get_nr_lectures() - nr_same_days < self.lecture.get_course().get_min_days() else 0

    def get_compact_penalty(self):
        """
        Compute the curriculum compactness penalty for this placement.
        Lectures belonging to the same curriculum should be adjacent to each other.
        """
        return sum(curricula.get_compact_penalty(self) for curricula in self.lecture.get_course().get_curriculas())

    def to_int(self):
        """Return the overall penalty as an integer."""
        return self.get_room_cap_penalty() + self.get_room_penalty() + self.get_min_days_penalty() + self.get_compact_penalty()

    def to_double(self):
        """Return the overall penalty as a double."""
        return float(self.to_int())

    def __eq__(self, other):
        """Compare two placements for equality."""
        if not isinstance(other, Placement):
            return False
        return (self.get_day() == other.get_day() and
                self.get_slot() == other.get_slot() and
                self.get_room() == other.get_room() and
                self.lecture.get_course() == other.lecture.get_course())

    def get_name(self):
        """Return the name of the placement (room id, day, and time)."""
        return f"{self.get_room().get_id()} {self.get_day()} {self.get_slot()}"

    def __hash__(self):
        """Return the hash code of the placement."""
        return self.hash_code

    def tabu_element(self):
        """Return the placement as an element for the tabu list (course id, day, time, and room id)."""
        return f"{self.lecture.get_course().get_id()}:{self.get_day()}:{self.get_slot()}:{self.get_room().get_id()}"
