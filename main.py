import os
from data_processing import DataProcessor
from ProblemModel import ProblemModel
from integer_program import TimetableIP


def is_feasible(solution, model):
    """
    Check if a solution satisfies all hard constraints.
    """
    courses = model.get_courses()
    rooms = model.get_rooms()
    periods = [(d, s) for d in range(model.get_nr_days()) for s in range(model.get_nr_slots_per_day())]
    conflict_graph = model.get_conflict_graph()

    lecture_assignments = {course.get_id(): 0 for course in courses}
    for course_id, room_id, day, slot in solution:
        lecture_assignments[course_id] += 1

    for course in courses:
        if lecture_assignments[course.get_id()] != course.get_nr_lectures():
            return False

    for (course1, course2) in conflict_graph:
        for period in periods:
            course1_assigned = any((course1.get_id(), room.get_id(), period[0], period[1]) in solution for room in rooms)
            course2_assigned = any((course2.get_id(), room.get_id(), period[0], period[1]) in solution for room in rooms)
            if course1_assigned and course2_assigned:
                return False

    for course_id, room_id, day, slot in solution:
        course = next(c for c in courses if c.get_id() == course_id)
        if not course.is_available(day, slot):
            return False

    room_period_assignments = {}
    for course_id, room_id, day, slot in solution:
        room_period_key = (room_id, day, slot)
        if room_period_key not in room_period_assignments:
            room_period_assignments[room_period_key] = []
        room_period_assignments[room_period_key].append(course_id)

    for assigned_courses in room_period_assignments.values():
        if len(assigned_courses) > 1:
            return False

    return True


def main():
    file_path = "./ConvertedFiles/comp02_converted.xlsx"
    model = ProblemModel()
    processor = DataProcessor(file_path)
    processor.initialize_model(model=model)

    print("\nGenerating solutions using Integer Programming...")
    solutions = []

    for _ in range(10):  # Generate multiple solutions
        timetable_solver = TimetableIP(model)
        solution = timetable_solver.solve()
        if solution and is_feasible(solution, model):
            solutions.append(solution)

    if not solutions:
        print("No feasible solutions generated.")
        return
    else:
        print(f"Generated {len(solutions)} feasible solutions.")

    # Save the solutions to files
    for i, solution in enumerate(solutions):
        output_file = f"./Validator/Solution_IP_{i + 1}.out"
        generate_output_file(solution, output_file)


def generate_output_file(solution, filename):
    """
    Generate an output file for a timetable solution.

    :param solution: The solution as a list of tuples (course_id, room_id, day, slot).
    :param filename: Path to the output file.
    """
    with open(filename, "w") as f:
        for course_id, room_id, day, slot in solution:
            f.write(f"{course_id} {room_id} {day} {slot}\n")
    print(f"Output saved to {filename}")


if __name__ == "__main__":
    if not os.path.exists("./Validator"):
        os.makedirs("./Validator")
    main()
