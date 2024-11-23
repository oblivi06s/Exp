import random
from ortools.sat.python import cp_model

class TimetableIP:
    def __init__(self, model):
        self.model = model

    def solve(self):
        cp_model_instance = cp_model.CpModel()

        # Extract data from ProblemModel
        courses = self.model.get_courses()
        rooms = self.model.get_rooms()
        periods = [(d, s) for d in range(self.model.get_nr_days()) for s in range(self.model.get_nr_slots_per_day())]
        conflict_graph = self.model.get_conflict_graph()

        print("Starting to define variables...")
        # Step 1: Define variables x[c, p, r] (course, period, room)
        x = {}
        for course in courses:
            for period in periods:
                for room in rooms:
                    x[(course.get_id(), period, room.get_id())] = cp_model_instance.NewBoolVar(
                        f"x_{course.get_id()}_{period}_{room.get_id()}"
                    )

        print("Defining constraints...")
        # Step 2: Add constraints

        print("Adding lectures constraint...")
        # (a) Lectures Constraint: All lectures of a course must be scheduled
        for course in courses:
            cp_model_instance.Add(
                sum(
                    x[(course.get_id(), period, room.get_id())]
                    for period in periods
                    for room in rooms
                )
                == course.get_nr_lectures()
            )
        
        for course in courses:
            for period in periods:
                cp_model_instance.Add(
                    sum(
                        x[(course.get_id(), period, room.get_id())]
                        for room in rooms
                    )
                    <= 1  # At most one lecture of the course in this period
                )

        # (b) Conflict Constraint: Courses in conflict cannot share the same period
        print("Adding conflict constraints...")
        for (course1, course2) in conflict_graph:
            for period in periods:
                cp_model_instance.Add(
                    sum(
                        x[(course1.get_id(), period, room.get_id())]
                        for room in rooms
                    )
                    + sum(
                        x[(course2.get_id(), period, room.get_id())]
                        for room in rooms
                    )
                    <= 1
                )

        # (c) Unavailability Constraint: Courses must respect availability
        print("Adding unavailability constraints...")
        for course in courses:
            unavailable_periods = course.unavailable_periods  # Retrieve unavailable periods for the course
            for day, slot in unavailable_periods:
                for room in rooms:
                    cp_model_instance.Add(
                        x[(course.get_id(), (day, slot), room.get_id())] == 0
                    )

        # (d) Room Occupation Constraint: At most one course per room in a period
        print("Adding room occupation constraints...")
        for period in periods:
            for room in rooms:
                cp_model_instance.Add(
                    sum(
                        x[(course.get_id(), period, room.get_id())]
                        for course in courses
                    )
                    <= 1
                )

        # Step 3: Randomized Objective function 
        # Add slight random perturbation to the priority weights
        cp_model_instance.Minimize(
            sum(
                (course.get_priority(day, slot) + random.uniform(-0.1, 0.1)) *
                x[(course.get_id(), (day, slot), room.get_id())]
                for course in courses
                for day, slot in periods
                for room in rooms
            )
        )

        # Solve the model
        solver = cp_model.CpSolver()
        solver.parameters.log_search_progress = True
        solver.parameters.max_time_in_seconds = 60
        status = solver.Solve(cp_model_instance)

        # Extract solution
        if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
            solution = []
            for course in courses:
                for day, slot in periods:
                    for room in rooms:
                        if solver.Value(x[(course.get_id(), (day, slot), room.get_id())]) == 1:
                            solution.append((course.get_id(), room.get_id(), day, slot))

            return solution
        else:
            print("No feasible solution found.")
            return None, None
