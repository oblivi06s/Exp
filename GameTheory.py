def game_theory_timetabling(problem_model):
    import random
    from collections import defaultdict

    # Extract data from ProblemModel
    courses = problem_model.get_courses()
    rooms = problem_model.get_rooms()
    days = problem_model.get_nr_days()
    slots_per_day = problem_model.get_nr_slots_per_day()
    periods = [(d, p) for d in range(days) for p in range(slots_per_day)]
    conflict_graph = problem_model.get_conflict_graph()

    # Transform conflict_graph (list of tuples) into a dictionary
    conflict_dict = defaultdict(list)
    for course1, course2 in conflict_graph:
        conflict_dict[course1].append(course2)
        conflict_dict[course2].append(course1)

    # Unavailability constraints
    unavailability_constraints = {
        course.get_id(): course.teacher.get_unavailability() if course.teacher else []
        for course in courses
    }

    # Initialize strategies
    strategies = {course.get_id(): [None] * len(course.lectures) for course in courses}
    conflict_penalty = defaultdict(int)  # Track penalty for courses to prioritize reassignment

    def calculate_payoff(course_id, period, room, lecture_index):
        payoff = 0

        # Ensure unique periods for the same course
        for idx, lecture in enumerate(strategies[course_id]):
            if idx == lecture_index or lecture is None:
                continue
            if lecture[0] == period:
                return -float('inf')  # Hard constraint violation

        # Check room occupation
        for other_course, lectures in strategies.items():
            if other_course == course_id:
                continue
            for lecture in lectures:
                if lecture is None:
                    continue
                other_period, other_room = lecture
                if other_period == period and other_room == room:
                    return -float('inf')  # Hard constraint violation

        # Check conflicts
        for other_course, lectures in strategies.items():
            if other_course == course_id:
                continue
            for lecture in lectures:
                if lecture is None:
                    continue
                other_period, _ = lecture
                if other_period == period:
                    if other_course in conflict_dict[course_id]:
                        return -float('inf')  # Hard constraint violation

        # Check unavailability constraints
        if course_id in unavailability_constraints and period in unavailability_constraints[course_id]:
            return -float('inf')  # Hard constraint violation

        # Reward valid assignments
        return 10 - conflict_penalty[course_id]  # Penalize courses with higher conflicts

    def assign_lecture(course_id, lecture_index):
        """Assign a lecture to the best period-room pair."""
        best_payoff = -float('inf')
        best_assignment = None

        for period in periods:
            for room in rooms:
                payoff = calculate_payoff(course_id, period, room, lecture_index)
                if payoff > best_payoff:
                    best_payoff = payoff
                    best_assignment = (period, room)

        if best_assignment:
            strategies[course_id][lecture_index] = best_assignment
        else:
            print(f"Warning: Could not assign lecture {lecture_index + 1} of course {course_id}")
            conflict_penalty[course_id] += 1  # Increase conflict penalty for reassignment prioritization

    def resolve_conflicts():
        """
        Resolve conflicts by unassigning and reassigning lectures.
        """
        assigned_periods = {}
        unassigned_lectures = []

        for course_id, lectures in strategies.items():
            for lecture_index, lecture in enumerate(lectures):
                if lecture is None:
                    unassigned_lectures.append((course_id, lecture_index))
                    continue
                period, room = lecture
                if period in assigned_periods:
                    # Conflict detected
                    conflicting_course = assigned_periods[period]
                    print(f"Conflict detected between {course_id} and {conflicting_course} at period {period}")
                    unassigned_lectures.append((course_id, lecture_index))
                    unassigned_lectures.append((conflicting_course, next(
                        (idx for idx, l in enumerate(strategies[conflicting_course]) if l and l[0] == period),
                        None
                    )))
                else:
                    assigned_periods[period] = course_id

        # Reassign unassigned lectures
        for course_id, lecture_index in set(unassigned_lectures):
            assign_lecture(course_id, lecture_index)

    # Main iteration loop
    max_iterations = 50
    for iteration in range(max_iterations):
        print(f"Iteration {iteration + 1}/{max_iterations}: Refining timetable...")
        for course in courses:
            for lecture_index in range(len(course.lectures)):
                assign_lecture(course.get_id(), lecture_index)

        resolve_conflicts()

        # Check for conflicts
        remaining_conflicts = sum(1 for c_id, lectures in strategies.items() for lec in lectures if lec is None)
        if remaining_conflicts == 0:
            print("All lectures successfully scheduled!")
            break
    else:
        print("Maximum iterations reached. Some conflicts may remain.")

    # Build the solution
    solution = []
    for course_id, lectures in strategies.items():
        for lecture in lectures:
            if lecture is None:
                raise ValueError(f"Lecture of course {course_id} is unscheduled.")
            period, room = lecture
            day, slot = period
            solution.append((course_id, room.get_id(), day, slot))

    return solution
