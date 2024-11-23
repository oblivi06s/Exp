import random

def parse_dataset(content):
    data = {
        "general": {},
        "courses": [],
        "rooms": [],
        "curricula": [],
    }
    section = None

    for line in content:
        line = line.strip()
        if not line:
            continue

        # Detecting sections
        if line.endswith(":"):
            section = line[:-1].lower()
            continue

        # Parse general information
        if section == "general":
            key, value = line.split(":")
            data["general"][key.strip().lower()] = int(value.strip())

        # Parse courses
        elif section == "courses":
            parts = line.split()
            course_id = parts[0]
            teacher_id = parts[1]
            lectures = int(parts[2])
            min_days = int(parts[3])
            students = int(parts[4])
            data["courses"].append({
                "course_id": course_id,
                "teacher_id": teacher_id,
                "lectures": lectures,
                "min_days": min_days,
                "unavailability": [],  # Placeholder for unavailability constraints
            })

        # Parse rooms
        elif section == "rooms":
            parts = line.split()
            room_id = parts[0]
            data["rooms"].append({"room_id": room_id})

        # Parse curricula
        elif section == "curricula":
            parts = line.split()
            curriculum_id = parts[0]
            num_courses = int(parts[1])
            courses = parts[2:]
            data["curricula"].append({
                "curriculum_id": curriculum_id,
                "num_courses": num_courses,
                "courses": courses
            })

    return data


def game_theory_with_heuristic(parsed_data):
    # Extract data
    courses = parsed_data["courses"]
    rooms = parsed_data["rooms"]
    curricula = parsed_data["curricula"]

    # Define periods
    days = 5
    periods_per_day = 6
    periods = [(d, p) for d in range(days) for p in range(periods_per_day)]

    # Build Conflict Graph
    conflict_graph = set()
    for curriculum in curricula:
        curriculum_courses = curriculum["courses"]
        for i, course1 in enumerate(curriculum_courses):
            for course2 in curriculum_courses[i + 1:]:
                conflict_graph.add((course1, course2))

    # Map unavailability constraints
    unavailability_constraints = {}
    for course in courses:
        course_id = course["course_id"]
        course_unavailability = course.get("unavailability", [])
        unavailability_constraints[course_id] = set(course_unavailability)

    # Initialize lectures as players
    lectures = []
    lecture_to_course = {}
    for course in courses:
        course_id = course["course_id"]
        for lecture_index in range(course["lectures"]):
            lecture_id = f"{course_id}_L{lecture_index + 1}"
            lectures.append(lecture_id)
            lecture_to_course[lecture_id] = course_id

    # Strategies for each lecture
    strategies = {lecture: None for lecture in lectures}

    # Room tracker
    room_tracker = {period: set() for period in periods}

    # Helper: Calculate payoff for a lecture
    def calculate_payoff(lecture_id, period, room):
        course_id = lecture_to_course[lecture_id]

        # Base payoff
        payoff = 10

        # Penalize unavailable periods
        if period in unavailability_constraints.get(course_id, set()):
            payoff -= 100

        # Penalize repeated periods for the same course
        assigned_periods = {assignment[0] for other_lecture, assignment in strategies.items()
                            if assignment is not None and lecture_to_course[other_lecture] == course_id}
        if period in assigned_periods:
            payoff -= 50

        # Penalize room conflicts
        if room["room_id"] in room_tracker[period]:
            payoff -= 1000  # Large penalty for conflicting room assignment

        # Penalize curriculum conflicts
        for other_lecture, assignment in strategies.items():
            if other_lecture == lecture_id or assignment is None:
                continue
            other_course_id = lecture_to_course[other_lecture]
            other_period, _ = assignment
            if other_period == period:
                if (course_id, other_course_id) in conflict_graph or (other_course_id, course_id) in conflict_graph:
                    payoff -= 100

        return payoff

    # Assign a lecture dynamically
    def assign_lecture(lecture_id):
        best_payoff = -float("inf")
        best_assignment = None

        for period in periods:
            for room in rooms:
                payoff = calculate_payoff(lecture_id, period, room)
                if payoff > best_payoff:
                    best_payoff = payoff
                    best_assignment = (period, room)

        # Apply the best assignment
        if best_assignment:
            period, room = best_assignment
            strategies[lecture_id] = best_assignment
            room_tracker[period].add(room["room_id"])
        else:
            strategies[lecture_id] = None

    # Iterative improvement with reassessment
    for iteration in range(50):
        print(f"Iteration {iteration + 1}: Refining timetable...")

        unassigned_lectures = []

        # Reevaluate all lectures dynamically
        for lecture_id in lectures:
            current_assignment = strategies[lecture_id]
            if current_assignment is not None:
                # Temporarily unassign the lecture
                period, room = current_assignment
                room_tracker[period].remove(room["room_id"])
                strategies[lecture_id] = None

            # Reassign the lecture dynamically
            assign_lecture(lecture_id)

            # Track unassigned lectures
            if strategies[lecture_id] is None:
                unassigned_lectures.append(lecture_id)

        # Progress Logging
        if not unassigned_lectures:
            print("No unassigned lectures. Timetable finalized.")
            break
        else:
            print(f"Unassigned lectures detected: {unassigned_lectures}")
    else:
        # Raise an error only after all iterations are exhausted
        raise ValueError(f"Could not assign the following lectures after 50 iterations: {unassigned_lectures}")

    # Build the solution
    solution = []
    for lecture_id, assignment in strategies.items():
        if assignment is None:
            raise ValueError(f"Lecture {lecture_id} is still unscheduled.")  # Double-check; should not occur
        period, room = assignment
        day, slot = period
        course_id = lecture_to_course[lecture_id]
        solution.append((course_id, room["room_id"], day, slot))

    return solution


def main():
    # Load dataset
    file_path = "./Input Files/comp01.ctt"  # Replace with your file path
    with open(file_path, "r") as file:
        dataset_content = file.readlines()

    parsed_data = parse_dataset(dataset_content)

    # Solve timetabling problem
    print("Starting timetabling...")
    try:
        solution = game_theory_with_heuristic(parsed_data)
    except ValueError as e:
        print(f"Error: {e}")
        return

    # Write solution to file
    output_file = "./Validator/solution.out"
    with open(output_file, "w") as file:
        for entry in solution:
            file.write(f"{entry[0]} {entry[1]} {entry[2]} {entry[3]}\n")
    print(f"Solution written to {output_file}")


if __name__ == "__main__":
    main()
