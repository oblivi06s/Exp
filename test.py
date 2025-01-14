import os
from data_processing import DataProcessor
from ProblemModel import ProblemModel
from GameTheory import game_theory_timetabling
from integer_program import TimetableIP


def detect_violations(solution, model):
    """
    Detect violations in the timetable solution for four hard constraints.
    """
    courses = model.get_courses()
    rooms = model.get_rooms()
    periods = [(d, s) for d in range(model.get_nr_days()) for s in range(model.get_nr_slots_per_day())]
    conflict_graph = model.get_conflict_graph()

    violations = {
        "lectures": [],          # Missing lectures for a course
        "conflicts": [],         # Conflicts between courses
        "availability": [],      # Assignments violating availability
        "room_occupation": []    # Multiple courses in the same room and period
    }

    # Map course_id to the number of assigned lectures
    lecture_assignments = {course.get_id(): 0 for course in courses}

    # Check for room and period conflicts
    room_period_assignments = {}
    for course_id, room_id, day, slot in solution:
        # Update lecture assignment count
        lecture_assignments[course_id] += 1

        # Check room occupation
        room_period_key = (room_id, day, slot)
        if room_period_key not in room_period_assignments:
            room_period_assignments[room_period_key] = []
        room_period_assignments[room_period_key].append(course_id)

    # Check lectures constraint: Ensure all lectures for each course are assigned
    for course in courses:
        assigned_lectures = lecture_assignments[course.get_id()]
        if assigned_lectures != course.get_nr_lectures():
            violations["lectures"].append({
                "course_id": course.get_id(),
                "expected": course.get_nr_lectures(),
                "assigned": assigned_lectures
            })

    # Check conflicts constraint: Courses in conflict cannot share the same period
    for (course1, course2) in conflict_graph:
        for period in periods:
            course1_assigned = any(
                (course1.get_id(), room.get_id(), period[0], period[1]) in solution
                for room in rooms
            )
            course2_assigned = any(
                (course2.get_id(), room.get_id(), period[0], period[1]) in solution
                for room in rooms
            )
            if course1_assigned and course2_assigned:
                violations["conflicts"].append({
                    "course1": course1.get_id(),
                    "course2": course2.get_id(),
                    "period": period
                })

    # Check availability constraint: Ensure courses are assigned to available slots
    for course_id, room_id, day, slot in solution:
        course = next(c for c in courses if c.get_id() == course_id)
        if not course.is_available(day, slot):
            violations["availability"].append({
                "course_id": course_id,
                "day": day,
                "slot": slot
            })

    # Check room occupation constraint: Ensure at most one course per room and period
    for (room_id, day, slot), assigned_courses in room_period_assignments.items():
        if len(assigned_courses) > 1:
            violations["room_occupation"].append({
                "room_id": room_id,
                "day": day,
                "slot": slot,
                "assigned_courses": assigned_courses
            })

    return violations


def generate_output_file(solution, filename):
    """
    Generate an output file for a timetable solution.

    :param solution: The solution as a list of tuples (course_id, room_id, day, slot).
    :param filename: Path to the output file.
    """
    with open(filename, "w") as f:
        for course_id, room_id, day, slot in solution:  # Unpack all four elements
            f.write(f"{course_id} {room_id} {day} {slot}\n")  # Include room_id in the output
    print(f"Output saved to {filename}")


def main():
    file_path = "./ConvertedFiles/comp21_converted.xlsx"  # Replace with the actual path to your Excel file

    # Initialize the ProblemModel
    model = ProblemModel()

    # Load data into the model using the DataProcessor
    processor = DataProcessor(file_path)
    processor.initialize_model(model=model)

    # Test Integer Programming directly
    print("\nSolving the timetable problem using Integer Programming...")
    try:
        # Solve timetabling problem
        timetable_solver = TimetableIP(model)
        solution = timetable_solver.solve()
    except ValueError as e:
        print(f"\nError during scheduling: {e}")
        return

    # Check if a feasible solution was found
    if solution:
        print("\nFeasible solution generated by Integer Programming!")
        output_file = "./Validator/Solution21.out"
        generate_output_file(solution, output_file)

        # Detect and print violations
        violations = detect_violations(solution, model)
        if violations:
            print("\nDetected Violations:")
            for violation_type, details in violations.items():
                print(f"{violation_type.capitalize()}: {len(details)} violations")
                for detail in details:
                    print(detail)
    else:
        print("\nFailed to generate a feasible solution using Integer Programming.")


if __name__ == "__main__":
    # Ensure the output directory exists
    if not os.path.exists("./Validator"):
        os.makedirs("./Validator")

    main()
